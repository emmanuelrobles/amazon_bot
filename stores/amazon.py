import json
from collections import Counter
from typing import Optional, Callable, List

import requests
import rx
import scheduler
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

from services.helpers import of_type, get_cookies_from_driver
from stores.Amazon.models import AmazonProductFoundAction, AmazonProduct
from stores.Amazon.scraper import get_data_using_request, init_scrap, get_data_using_selenium, try_add_to_cart_request, \
    express_checkout, get_add_to_cart_url


def init_scrapers(products: List[AmazonProduct]) -> Observable:
    from rx.scheduler import ThreadPoolScheduler
    scrap = init_scrap(lambda: get_data_using_request(models.enums.BrowsersEnum.CHROMIUM))

    def map_product(option: AmazonProduct):
        return SchedulerObs.init_scheduler(lambda: scrap(option), 3)

    return rx.from_iterable(products, ThreadPoolScheduler()) \
        .pipe(
        ops.map(map_product),
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
def init_store(logged_in_driver: WebDriver, products: List[AmazonProduct]) -> Observable:
    # guards the buy action, check if the products meets the criteria before
    def init_guard() -> Callable[[WebDriver, AmazonProductFoundAction], bool]:
        desire_qty: dict = {}
        bought_qty: Counter = Counter()
        for p in products:
            desire_qty.update({p.url: p.qty})

        #  tries to buy a product
        def try_buy(driver: WebDriver, action: AmazonProductFoundAction) -> bool:
            # already bought specified qty
            if bought_qty[action.product.url] >= action.product.qty:
                print("Product was bought already")
                return False

            # get the cookies from the login driver
            cookies = get_cookies_from_driver(driver)

            # Try to buy the item with express checkout
            bought = express_checkout(action.product.product_id)(
                'njlgprjsskkq',
                action.site_data.offer_id_callback(),
                cookies)

            if bought:
                bought_qty.update([action.product.url])

            return bought

        # request add to cart with the cookies from the login driver
            # if not try_add_to_cart_request(action.site_data.offer_id_callback(), cookies):
            #     return False

            # go to the product add to cart url
            # url = get_add_to_cart_url(action.site_data.offer_id_callback())
            # driver.get(url)
            #
            # try:
            #     # add to cart
            #     WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, 'a-autoid-0'))).click()
            #     # confirm
            #     WebDriverWait(driver, 10).until(
            #         EC.presence_of_element_located((By.ID, 'sc-buy-box-ptc-button'))).click()
            #     # place order
            #     WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, 'submitOrderButtonId'))).click()
            # except Exception as e:
            #     # Couldn't buy return false
            #     print(e)
            #     return False
            #
            # return True

        return try_buy

    # init the guard
    buy = init_guard()

    # init scrapers
    products_notification_obs = init_scrapers(products)

    product_not_found_obs = products_notification_obs.pipe(
        of_type("amazon_product_not_found"))

    product_found_obs = products_notification_obs.pipe(
        ops.do_action(lambda action: print(
            f'{action.payload.error_msg} for product: {action.payload.product.url}'
            if action.action_type == 'amazon_product_not_found'
            else 'product_found')),

        of_type("amazon_product_found"))

    return rx.merge(
        product_found_obs.pipe(
            ops.do_action(lambda action:
                          print(f'{action.action_type}: '
                                f'price {action.payload.site_data.price_found} '
                                f'url {action.payload.product.url}'))
        )).pipe(ops.map(lambda action: buy(logged_in_driver, action.payload)))
