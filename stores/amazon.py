import asyncio
import random
import time
from collections import Counter
from typing import Callable, List, Optional, Tuple

import rx
import rx.subject as subjects
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
from stores.Amazon.models import AmazonProductFoundAction, AmazonProduct, AmazonConfig, RequestData, \
    AmazonBotDetectedAction
from stores.Amazon.scraper import init_scrap, get_data_using_selenium, get_data_using_request, \
    try_checkout, needs_captcha


def init_scrapers(scraper: Callable[[AmazonProduct], Action], products: List[AmazonProduct]) -> Observable:
    from rx.scheduler import ThreadPoolScheduler

    def map_product(option: AmazonProduct):
        return SchedulerObs.init_scheduler(lambda: scraper(option), 3.5)

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
    def init_guard() -> Callable[[AmazonProductFoundAction], Action]:
        desire_qty: dict = {}
        bought_qty: Counter = Counter()
        for p in amazonConfig.products:
            desire_qty.update({p.url: p.qty})

        # saving cookies
        cookies = amazonConfig.logged_in_cookies_callback()

        #  tries to buy a product
        def try_buy(action: AmazonProductFoundAction) -> Action:
            # already bought specified qty
            if bought_qty[action.product.url] == action.product.qty:
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

    # init the guard
    buy = init_guard()

    request_data = get_cookies_for_proxies(amazonConfig.scrapper_browser, random.choice(amazonConfig.proxies))

    # init scrapers
    scraper = init_scrap(get_data_using_request(request_data))
    products_notification_obs = init_scrapers(scraper, amazonConfig.products)

    def log_action(action: Action):
        if action.action_type == AmazonActionTypes.product_found:
            print(f'{action.action_type}: '
                  f'price {action.payload.site_data.price_found} '
                  f'url {action.payload.product.url}')
        elif action.action_type == AmazonActionTypes.product_not_found:
            print(f'{action.payload.error_msg} for product: {action.payload.product.url}')
        else:
            print(action.action_type)

    # bot detection methid
    def on_bot_detected(action: Action):
        if action.action_type == AmazonActionTypes.bot_detected:
            nonlocal request_data
            payload: AmazonBotDetectedAction = action.payload

            # if refreshed already don't do anything
            if request_data.proxies['https'] != payload.proxies['https']:
                return

            # get new data
            new_request_data = get_cookies_for_proxies(amazonConfig.scrapper_browser,
                                                       random.choice(amazonConfig.proxies))

            # set data
            request_data.proxies = new_request_data.proxies
            request_data.cookies = new_request_data.cookies

    return products_notification_obs.pipe(
        ops.do_action(log_action),
        ops.do_action(on_bot_detected),
        of_type(AmazonActionTypes.product_found),
        ops.map(lambda action: buy(action.payload)),
        ops.do_action(lambda action: print(f'{action.action_type}: product {action.payload.product.url}'))
    )


# get new cookies with a given proxy TODO move this to the right place, add timing params
def get_cookies_for_proxies(browser: models.enums.BrowsersEnum, proxy: dict) -> RequestData:
    # get a driver with the proxy
    driver = get_a_driver(browser, False, {'proxy': proxy})
    driver.get("https://www.amazon.com/")

    # if captcha req sleep for 60 sec to allow user to solve captcha TODO refactor all of this method
    if needs_captcha(driver.page_source):
        time.sleep(60)

    # making a req to an amazon product and getting the request info
    driver.get("https://www.amazon.com/gp/aod/ajax/ref=auto_load_aod?asin=B097CMQVF4&pc=dp")
    req = next(x for x in driver.requests if x.url == 'https://www.amazon.com/gp/aod/ajax/ref=auto_load_aod?asin=B097CMQVF4&pc=dp')

    # get cookies and headers
    cookies = get_cookies_from_driver(driver)
    headers = {}
    driver_headers = req.headers
    for header in driver_headers:
        headers[header] = driver_headers[header]
    driver.quit()
    return RequestData(headers, cookies, proxy)
