import json
from collections import Counter
from typing import Optional, Callable, List

import rx
from rx import Observable
import rx.operators as ops
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
import services.scheduler as SchedulerObs

import models.enums
from browser.driver import get_a_driver
from models.communication import Action
from models.product_options import ProductOptions


class AmazonSiteData:
    def __init__(self, price_found: float, add_to_cart_callback: Callable[[], str]):
        self.price_found = price_found
        self.add_to_cart_callback = add_to_cart_callback


class AmazonProductFoundAction:
    def __init__(self, site_data: AmazonSiteData, options: ProductOptions):
        self.site_data = site_data
        self.options = options


# Send a notification when finds a product with the right price
def init_scrapers(products: List[ProductOptions], browser: models.enums.BrowsersEnum) -> Observable:
    #    get a driver with no auth
    def init_default_driver(url) -> WebDriver:
        print("creating driver for url: " + url)
        driver = get_a_driver(browser)
        driver.get(url)
        print("driver created for url: " + url)
        return driver

    # get the product data from the site
    def get_product(options: ProductOptions) -> Callable[[WebDriver], Optional[Action[AmazonProductFoundAction]]]:
        def set_driver(driver: WebDriver) -> Optional[Action[AmazonProductFoundAction]]:
            def get_metadata():
                def get_price_by_id(id: str) -> Optional[float]:
                    try:
                        price: float = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, id))) \
                            .find_element(By.XPATH, './/span[@class = "a-price"]/span[@class = "a-offscreen"]') \
                            .get_attribute('innerHTML')
                        return float(price[1:].replace(',', ''))
                    except:
                        return None

                def get_url(id: str) -> str:
                    child: WebElement = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, id)))
                    ele = child.find_element(By.XPATH, './../..')
                    data = json.loads(ele.get_attribute('data-aod-atc-action'))

                    def build_add_to_cart_url(oid: str):
                        base_url = 'https://www.amazon.com/gp/aws/cart/add-res.html?Quantity.1=1&OfferListingId.1='
                        return base_url + oid

                    return build_add_to_cart_url(data['oid'])

                default_price = get_price_by_id('aod-price-0')
                best_offer = get_price_by_id('aod-price-1')

                # getting the best price, extremely ugly solution but it works :), TODO rework this later
                if best_offer is None and default_price is None:
                    return None
                elif best_offer is not None and default_price is not None:
                    if default_price <= best_offer:
                        return AmazonSiteData(default_price, lambda: get_url('a-autoid-2-offer-0'))
                    return AmazonSiteData(best_offer, lambda: get_url('a-autoid-2-offer-1'))
                elif best_offer is None:
                    return AmazonSiteData(default_price, lambda: get_url('a-autoid-2-offer-0'))
                elif default_price is None:
                    return AmazonSiteData(best_offer, lambda: get_url('a-autoid-2-offer-1'))

            driver.refresh()
            metadata = get_metadata()
            if metadata.price_found <= options.price:
                return Action("product_found", AmazonProductFoundAction(metadata, options))
            return None

        return set_driver

    # schedule the scraper to run with the given options
    def create_observable(product: ProductOptions) -> Observable:
        driver = init_default_driver(product.url)
        return SchedulerObs.init_scheduler(driver, get_product(product))

    from rx.scheduler import ThreadPoolScheduler
    return rx.from_iterable(products, ThreadPoolScheduler())\
        .pipe(
            ops.map(create_observable),
            ops.merge_all()
        )


# gets a driver with the credentials
def init_logged_in_driver(browser: models.enums.BrowsersEnum, username: str, password: str) -> WebDriver:
    print("creating driver with credentials")
    driver = get_a_driver(browser, False)
    driver.get(
        'https://www.amazon.com/ap/signin?openid.pape.max_auth_age=0&openid.return_to=https%3A%2F%2Fwww.amazon.com%2F%3Fref_%3Dnav_signin&openid.identity=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0%2Fidentifier_select&openid.assoc_handle=usflex&openid.mode=checkid_setup&openid.claimed_id=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0%2Fidentifier_select&openid.ns=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0&')
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "ap_email"))).send_keys(username)

    driver.find_element(By.ID, 'continue').click()

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "ap_password"))).send_keys(password)

    driver.find_element(By.ID, 'signInSubmit').click()
    print("driver successfully created")
    return driver


# returns an observable[bool], TODO add a better response type, Action[AmazonProductBought]
def init_store(logged_in_driver: WebDriver, products: List[ProductOptions],
               browser: models.enums.BrowsersEnum) -> Observable:

    # guards the buy action, check if the products meets the criteria before
    def init_guard() -> Callable[[WebDriver, AmazonProductFoundAction], bool]:
        desire_qty: dict = {}
        bought_qty: Counter = Counter()
        for p in products:
            desire_qty.update({p.url: p.qty})

        #  tries to buy a product
        def try_buy(driver: WebDriver, action: AmazonProductFoundAction) -> bool:
            # already bought specified qty
            if bought_qty[action.options.url] >= action.options.qty:
                print("Product was bought already")
                return False
            # go to the product add to cart url
            url = action.site_data.add_to_cart_callback()
            driver.get(url)

            try:
                # add to cart
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, 'a-autoid-0'))).click()
                # confirm
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, 'sc-buy-box-ptc-button'))).click()
                # place order
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, 'submitOrderButtonId'))).click()
            except Exception as e:
                # Couldn't buy return false
                print(e)
                return False

            bought_qty.update([action.options.url])
            return True

        return try_buy

    # init the guard
    buy = init_guard()

    # init scrapers
    products_notification = init_scrapers(products, browser)

    return products_notification.pipe(
        ops.do_action(lambda action: print(action.action_type)),
        ops.map(lambda action: buy(logged_in_driver, action.data))
    )
