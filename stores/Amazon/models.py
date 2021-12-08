from typing import Callable, List, Optional

from models.enums import BrowsersEnum


class AmazonProduct:
    def __init__(self, product_id: str, qty: int, price: float):
        self.product_id = product_id
        self.url = f'https://www.amazon.com/gp/aod/ajax/ref=auto_load_aod?asin={product_id}&pc=dp'
        self.qty = qty
        self.price = price


class AmazonSiteData:
    def __init__(self, price_found: float, offer_id_callback: Callable[[], str]):
        self.price_found = price_found
        self.offer_id_callback = offer_id_callback


class AmazonProductFoundAction:
    def __init__(self, site_data: AmazonSiteData, product: AmazonProduct):
        self.site_data = site_data
        self.product = product


class AmazonProductNotFoundAction:
    def __init__(self, error_msg: str, product: AmazonProduct):
        self.error_msg = error_msg
        self.product = product


class AmazonProductBoughtSuccessAction:
    def __init__(self, product: AmazonProduct):
        self.product = product


class AmazonProductBoughtErrorAction:
    def __init__(self, error_msg: str, product: AmazonProduct):
        self.error_msg = error_msg
        self.product = product


class AmazonProductAllBoughtAction:
    def __init__(self, product: AmazonProduct):
        self.product = product


class AmazonBotDetectedAction:
    def __init__(self, proxies: dict, product: AmazonProduct):
        self.proxies = proxies
        self.product = product


class AmazonCookiesProxiesRefreshedAction:
    def __init__(self, cookies: dict, proxies: dict):
        self.cookies = cookies
        self.proxies = proxies


class AmazonConfig:
    def __init__(self,
                 logged_in_cookies_callback: Callable[[], dict],
                 address_id: str,
                 products: List[AmazonProduct],
                 scraper_browser: BrowsersEnum,
                 proxies: Optional[List[dict]]
                 ):
        self.logged_in_cookies_callback = logged_in_cookies_callback
        self.address_id = address_id
        self.products = products
        self.scrapper_browser = scraper_browser
        self.proxies = proxies


class RequestData:
    def __init__(self, headers: dict, cookies: dict, proxies: dict):
        self.cookies = cookies
        self.proxies = proxies
        self.headers = headers
