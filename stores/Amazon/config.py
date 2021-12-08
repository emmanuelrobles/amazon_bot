import json
import time
from typing import List, Optional

from models.enums import BrowsersEnum
from services.helpers import get_cookies_from_driver
from stores.Amazon.models import AmazonConfig, AmazonProduct
from stores.amazon import init_logged_in_driver


def amazon_config_from_json(data: dict) -> AmazonConfig:
    def products_from_json() -> List[AmazonProduct]:
        products = []
        for product in data['products']:
            products.append(AmazonProduct(product['id'], product['qty'], product['price']))
        return products

    def get_proxies_from_json() -> Optional[List[dict]]:
        if 'proxies' not in data:
            return None

        proxies_json = data['proxies']
        proxy_credentials = proxies_json['credentials']
        proxies = []
        for url in proxies_json['urls']:
            proxies.append({"https":f'socks5://{proxy_credentials["user"]}:{proxy_credentials["password"]}@{url}:{proxies_json["port"]}'})
        return proxies

    credentials = data['credentials']

    def get_cookies() -> dict:

        if 'cookies' in data:
            return data['cookies']

        # get a driver with the user logged in
        driver = init_logged_in_driver(
            BrowsersEnum(data['autoBuyBrowser']), credentials['user'], credentials['password'])
        # wait for the user
        time.sleep(data['browserWait'])
        # get the cookies
        cookies = get_cookies_from_driver(driver)
        # close the driver instance
        driver.quit()
        # print cookies
        print(json.dumps(cookies))
        return cookies

    return AmazonConfig(
        get_cookies,
        data['addressId'],
        products_from_json(),
        BrowsersEnum(data['scraperBrowser']),
        get_proxies_from_json())
