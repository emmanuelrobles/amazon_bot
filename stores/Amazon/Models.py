from typing import Callable

from models.product_options import ProductOptions


class AmazonSiteData:
    def __init__(self, price_found: float, add_to_cart_callback: Callable[[], str]):
        self.price_found = price_found
        self.add_to_cart_callback = add_to_cart_callback


class AmazonProductFoundAction:
    def __init__(self, site_data: AmazonSiteData, options: ProductOptions):
        self.site_data = site_data
        self.options = options


class AmazonProductNotFoundAction:
    def __init__(self, error_msg: str, options: ProductOptions):
        self.error_msg = error_msg
        self.options = options