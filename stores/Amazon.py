import json
from typing import Optional, Callable

from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait

import models.enums
from browser.Driver import get_a_driver
from models.communication import Action


class AmazonMetadata:
    def __init__(self, price: float, add_to_cart_callback: Callable[[], str]):
        self.price = price
        self.add_to_cart_callback = add_to_cart_callback


def get_default_driver(browser: models.enums.BrowsersEnum) -> Callable[[str], WebDriver]:
    driver = get_a_driver(browser)

    def set_url(url: str) -> WebDriver:
        driver.get(url)
        return driver

    return set_url


def get_product_metadata(minimumPrice: float) -> Callable[[WebDriver], Optional[Action[AmazonMetadata]]]:
    def set_driver(driver: WebDriver) -> Optional[Action[AmazonMetadata]]:
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

            # getting the best price
            if best_offer is None and default_price is None:
                return None
            if best_offer is None or default_price <= best_offer:
                return AmazonMetadata(default_price, lambda: get_url('a-autoid-2-offer-0'))
            elif default_price is None or default_price > best_offer:
                return AmazonMetadata(best_offer, lambda: get_url('a-autoid-2-offer-1'))
        driver.refresh()
        metadata = get_metadata()
        if metadata.price <= minimumPrice:
            return Action("product_found", metadata)
        return None

    return set_driver


def get_logged_in_driver(driver: WebDriver) -> Callable[[str, str], WebDriver]:
    def sign_in(username: str, password: str):
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "ap_email"))).send_keys(username)

        driver.find_element(By.ID, 'continue').click()

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "ap_password"))).send_keys(password)

        driver.find_element(By.ID, 'signInSubmit').click()
        return driver

    driver.get(
        'https://www.amazon.com/ap/signin?openid.pape.max_auth_age=0&openid.return_to=https%3A%2F%2Fwww.amazon.com%2F%3Fref_%3Dnav_signin&openid.identity=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0%2Fidentifier_select&openid.assoc_handle=usflex&openid.mode=checkid_setup&openid.claimed_id=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0%2Fidentifier_select&openid.ns=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0&')
    return sign_in
