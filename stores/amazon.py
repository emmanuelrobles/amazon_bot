import asyncio
import time
from collections import Counter
from typing import Callable, List

import rx
import rx.operators as ops
from rx import Observable
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

import models.enums
import services.scheduler as SchedulerObs
from browser.driver import get_a_driver
from models.communication import Action
from services.helpers import of_type, get_cookies_from_driver
from stores.Amazon.actions import on_all_products_bought, on_product_bought_success, AmazonActionTypes, \
    on_product_bought_error
from stores.Amazon.models import AmazonProductFoundAction, AmazonProduct, AmazonConfig
from stores.Amazon.scraper import init_scrap, get_data_using_selenium, get_data_using_request, \
    try_checkout


def init_scrapers(scraper: Callable[[AmazonProduct], Action], products: List[AmazonProduct]) -> Observable:
    from rx.scheduler import ThreadPoolScheduler

    def map_product(option: AmazonProduct):
        return SchedulerObs.init_scheduler(lambda: scraper(option), 2.3)

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
        'https://www.amazon.com/ap/signin?openid.pape.max_auth_age=0&openid.return_to=https%3A%2F%2Fwww.amazon.com%2F'
        '%3Fref_%3Dnav_signin&openid.identity=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0%2Fidentifier_select&openid'
        '.assoc_handle=usflex&openid.mode=checkid_setup&openid.claimed_id=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0'
        '%2Fidentifier_select&openid.ns=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0&')
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "ap_email"))).send_keys(username)

    driver.find_element(By.ID, 'continue').click()

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "ap_password"))).send_keys(password)

    driver.find_element(By.ID, 'signInSubmit').click()
    print("driver successfully created")
    return driver


def init_store(amazonConfig: AmazonConfig) -> Observable:
    # guards the buy action, check if the products meets the criteria before
    def init_guard() -> Callable[[dict, AmazonProductFoundAction], Action]:
        desire_qty: dict = {}
        bought_qty: Counter = Counter()
        for p in amazonConfig.products:
            desire_qty.update({p.url: p.qty})

        #  tries to buy a product
        def try_buy(cookies: dict, action: AmazonProductFoundAction) -> Action:
            # already bought specified qty
            if bought_qty[action.product.url] >= action.product.qty:
                return on_all_products_bought(action.product)

            # Try to buy the item with express checkout
            bought = asyncio.run(try_checkout(action.product.product_id,
                                              amazonConfig.address_id,
                                              action.site_data.offer_id_callback(),
                                              cookies))

            if bought:
                bought_qty.update([action.product.url])
                return on_product_bought_success(action.product)

            return on_product_bought_error('couldnt buy product', action.product)

        return try_buy

    # get cookies use to buy products
    def get_autobuy_cookies():
        # get a driver with the user logged in
        driver = init_logged_in_driver(amazonConfig.autobuy_browser, amazonConfig.user_name, amazonConfig.password)
        # wait for the user
        time.sleep(amazonConfig.browser_wait)
        # get the cookies
        cookies = get_cookies_from_driver(driver)
        # close the driver instance
        driver.close()
        return cookies

    # saving cookies
    cookies = get_autobuy_cookies()

    # init the guard
    buy = init_guard()

    # init scrapers
    scraper = init_scrap(get_data_using_request(amazonConfig.scrapper_browser))
    products_notification_obs = init_scrapers(scraper, amazonConfig.products)

    def log_action(action: Action):
        if action.action_type == AmazonActionTypes.product_found:
            print(f'{action.action_type}: '
                  f'price {action.payload.site_data.price_found} '
                  f'url {action.payload.product.url}')
        else:
            print(f'{action.payload.error_msg} for product: {action.payload.product.url}')

    return products_notification_obs.pipe(
        ops.do_action(log_action)).pipe(
        of_type(AmazonActionTypes.product_found),
        ops.map(lambda action: buy(cookies, action.payload)),
        ops.do_action(lambda action: print(f'{action.action_type}: product {action.payload.product.url}'))
    )
