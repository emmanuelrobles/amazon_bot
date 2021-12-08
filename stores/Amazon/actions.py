from enum import Enum

from models.communication import Action
from stores.Amazon.models import AmazonProductFoundAction, AmazonProductNotFoundAction, \
    AmazonProductBoughtSuccessAction, AmazonProductBoughtErrorAction, AmazonProduct, AmazonSiteData, \
    AmazonProductAllBoughtAction, AmazonBotDetectedAction, AmazonCookiesProxiesRefreshedAction


def on_product_found(site_data: AmazonSiteData, product: AmazonProduct) -> Action[AmazonProductFoundAction]:
    return Action(AmazonActionTypes.product_found, AmazonProductFoundAction(site_data, product))


def on_product_not_found(error_msg: str, product: AmazonProduct) -> Action[AmazonProductNotFoundAction]:
    return Action(AmazonActionTypes.product_not_found, AmazonProductNotFoundAction(error_msg, product))


def on_product_bought_success(product: AmazonProduct) -> Action[AmazonProductBoughtSuccessAction]:
    return Action(AmazonActionTypes.product_bought_success, AmazonProductBoughtSuccessAction(product))


def on_product_bought_error(error_msg: str, product: AmazonProduct) -> Action[AmazonProductBoughtErrorAction]:
    return Action(AmazonActionTypes.product_bought_error, AmazonProductBoughtErrorAction(error_msg, product))


def on_all_products_bought(product: AmazonProduct) -> Action[AmazonProductAllBoughtAction]:
    return Action(AmazonActionTypes.all_products_bought, AmazonProductAllBoughtAction(product))


def on_bot_detected(proxies: dict, product: AmazonProduct) -> Action[AmazonBotDetectedAction]:
    return Action(AmazonActionTypes.bot_detected, AmazonBotDetectedAction(proxies, product))


def on_cookies_proxies_refreshed(cookies: dict, proxies: dict) -> Action[AmazonCookiesProxiesRefreshedAction]:
    return Action(AmazonActionTypes.cookies_proxies_refreshed, AmazonCookiesProxiesRefreshedAction(cookies, proxies))


class AmazonActionTypes(str, Enum):
    product_found = 'amazon_product_found'
    product_not_found = 'amazon_product_not_found'
    product_bought_success = 'amazon_product_bought_success'
    product_bought_error = 'amazon_product_bought_error'
    all_products_bought = 'all_products_bought'
    bot_detected = 'bot_detected'
    cookies_proxies_refreshed = 'cookies_proxies_refreshed'
