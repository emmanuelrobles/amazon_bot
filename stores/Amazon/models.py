from typing import Callable


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
