import asyncio
import json
import time
from typing import Optional, Callable, NamedTuple, Tuple
from bs4 import BeautifulSoup
import requests
from selenium.webdriver.remote.webdriver import WebDriver

from browser.driver import get_a_driver
from models.communication import Action
from models.enums import BrowsersEnum
from services.helpers import get_cookies_from_driver
from stores.Amazon.actions import on_product_not_found, on_product_found, on_bot_detected
from stores.Amazon.exceptions import AmazonBotFoundException
from stores.Amazon.models import AmazonSiteData, AmazonProductNotFoundAction, AmazonProductFoundAction, AmazonProduct, \
    RequestData


def __get_base_headers() -> dict:
    return {
        'authority': 'www.amazon.com',
        'rtt': '50',
        'downlink': '10',
        'ect': '4g',
        'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="96"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Linux"',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'sec-fetch-site': 'none',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-user': '?1',
        'sec-fetch-dest': 'document',
        'accept-language': 'en-US,en;q=0.9',
    }


def init_scrap(get_html_callback: Callable[[str], str]) -> Callable[[AmazonProduct], Action]:
    def scrap_product(product: AmazonProduct) -> Action:

        def get_data() -> Action:
            # try to get the html
            try:
                data = get_html_callback(product.url)
            except AmazonBotFoundException as e:
                return on_bot_detected(e.proxies, product)

            # Passing the source code to BeautifulSoup to create a BeautifulSoup object for it.
            soup = BeautifulSoup(data, features="lxml")

            def get_price_by_id(price_id: str) -> Optional[float]:
                parent = soup.find(id=price_id)
                if parent is None:
                    return None
                ele = parent.find('span', {'class': 'a-offscreen'})
                return float(ele.string[1:].replace(',', ''))

            # Get offer listing id for product
            def get_offer_id(element_id: str) -> str:
                ele = soup.find(id=element_id).parent.parent
                return json.loads(ele.attrs['data-aod-atc-action'])['oid']

            # returns the product metadata found, None if no price was found
            def get_product_metadata() -> Optional[AmazonSiteData]:
                default_price = get_price_by_id('aod-price-0')
                best_offer = get_price_by_id('aod-price-1')

                # getting the best price, extremely ugly solution but it works :), TODO rework this later
                if best_offer is None and default_price is None:
                    return None
                elif best_offer is not None and default_price is not None:
                    if default_price <= best_offer:
                        return AmazonSiteData(default_price,
                                              lambda: get_offer_id('a-autoid-2-offer-0'))
                    return AmazonSiteData(best_offer,
                                          lambda: get_offer_id('a-autoid-2-offer-1'))
                elif best_offer is None:
                    return AmazonSiteData(default_price,
                                          lambda: get_offer_id('a-autoid-2-offer-0'))
                elif default_price is None:
                    return AmazonSiteData(best_offer,
                                          lambda: get_offer_id('a-autoid-2-offer-1'))

            metadata = get_product_metadata()

            if metadata is not None:
                if metadata.price_found <= product.price:
                    return on_product_found(metadata, product)
                else:
                    return on_product_not_found(
                        'Price %s is too high, expected price: %s' % (metadata.price_found, product.price),
                        product)
            return on_product_not_found("Price not found", product)

        try:
            return get_data()
        except Exception as e:
            return on_product_not_found("Request failed", product)

    return scrap_product


def get_data_using_selenium(browser: BrowsersEnum) -> Callable[[str], str]:
    driver = get_a_driver(browser, False)
    driver.get('https://www.amazon.com')
    time.sleep(5)

    def get_page_source(url: str) -> str:
        driver.get(url)
        return driver.page_source

    return get_page_source


# get cookies from a driver
def get_cookies(driver: WebDriver) -> dict:
    # clear cookies
    driver.delete_all_cookies()

    driver.get('https://www.amazon.com')
    # wait to load everything and fix captcha
    time.sleep(5)

    # get cookies
    cookies = get_cookies_from_driver(driver)

    # close driver
    driver.close()
    return cookies


def get_data_using_request(data: RequestData) -> Callable[[str], str]:

    def get_page_source(url: str) -> str:
        headers = __get_base_headers()
        # make request
        response = requests.get(url, headers=headers, cookies=data.cookies, proxies=data.proxies)

        if response.status_code == 503:
            raise AmazonBotFoundException(data.proxies, url)

        # Extracting the source code of the page.
        return response.text

    return get_page_source


# Get the url to add to cart given an offerId
def get_add_to_cart_url(offer_id: str) -> str:
    base_url = 'https://www.amazon.com/gp/aws/cart/add-res.html?Quantity.1=1&OfferListingId.1='
    return base_url + offer_id


# makes the request to add to the cart given an offer id and a sessionId
def try_add_to_cart_request(offer_id: str, cookies: dict) -> bool:
    session_id = cookies['session-id']
    headers = __get_base_headers()
    response = requests.post('https://www.amazon.com/gp/product/handle-buy-box/ref=dp_start-bbf_1_glance',
                             data={'offerListingID': offer_id, 'session-id': session_id}, cookies=cookies,
                             headers=headers)
    return response.status_code == 200


# try to check out items using all possible ways
async def try_checkout(product_id: str, address_id: str, offer_id: str, cookies: dict) -> bool:
    # normal checkout, adds to cart and place order
    async def normal_checkout() -> bool:
        def add_to_cart() -> str:
            url = 'https://www.amazon.com/gp/product/handle-buy-box/ref=dp_start-bbf_1_glance'
            headers = __get_base_headers()
            session_id = cookies['session-id']
            data = {'offerListingID': offer_id, 'session-id': session_id, 'ASIN': product_id, 'rsid': session_id,
                    'quantity': 1,
                    'submit.buy-now': 'Submit+Query', 'dropdown-selection': address_id,
                    'dropdown-selection-ubb': address_id}
            response = requests.post(url, data=data, cookies=cookies, headers=headers)
            return response.text

        headers = __get_base_headers()
        cart_html = add_to_cart()

        soup = BeautifulSoup(cart_html, features="lxml")

        def get_value_or_default(name: str) -> str:
            ele = soup.find('input', {'name': name})
            if ele is None:
                return ""
            try:
                return ele['value']
            except KeyError:
                return ""

        item_id = get_value_or_default('lineitemids0')
        quantity_field_name = f'quantity.{item_id}'
        data = {
            'submitFromSPC': get_value_or_default('submitFromSPC'),
            'fasttrackExpiration': get_value_or_default('fasttrackExpiration'),
            'countdownThreshold': get_value_or_default('countdownThreshold'),
            'showSimplifiedCountdown': get_value_or_default('showSimplifiedCountdown'),
            'countdownId': get_value_or_default('countdownId'),
            quantity_field_name: get_value_or_default(quantity_field_name),
            'dupOrderCheckArgs': get_value_or_default('dupOrderCheckArgs'),
            'order0': get_value_or_default('order0'),
            'shippingofferingid0.0': get_value_or_default('shippingofferingid0.0'),
            'guaranteetype0.0': get_value_or_default('guaranteetype0.0'),
            'issss0.0': get_value_or_default('issss0.0'),
            'previousshippingofferingid0': get_value_or_default('previousshippingofferingid0'),
            'previousguaranteetype0': get_value_or_default('previousguaranteetype0'),
            'previousissss0': get_value_or_default('previousissss0'),
            'previousshippriority0': get_value_or_default('previousshippriority0'),
            'lineitemids0': item_id,
            'currentshippingspeed': get_value_or_default('currentshippingspeed'),
            'previousShippingSpeed0': get_value_or_default('previousShippingSpeed0'),
            'currentshipsplitpreference': get_value_or_default('currentshipsplitpreference'),
            'shippriority.0.shipWhenever': get_value_or_default('shippriority.0.shipWhenever'),
            'groupcount': get_value_or_default('groupcount'),
            'shiptrialprefix': get_value_or_default('shiptrialprefix'),
            'csrfToken': get_value_or_default('csrfToken'),
            'fromAnywhere': get_value_or_default('fromAnywhere'),
            'redirectOnSuccess': get_value_or_default('redirectOnSuccess'),
            'purchaseTotal': get_value_or_default('purchaseTotal'),
            'purchaseTotalCurrency': get_value_or_default('purchaseTotalCurrency'),
            'purchaseID': get_value_or_default('purchaseID'),
            'purchaseCustomerId': get_value_or_default('purchaseCustomerId'),
            'useCtb': get_value_or_default('useCtb'),
            'scopeId': get_value_or_default('scopeId'),
            'isQuantityInvariant': get_value_or_default('isQuantityInvariant'),
            'promiseTime-0': get_value_or_default('promiseTime-0'),
            'promiseAsin-0': get_value_or_default('promiseAsin-0'),
            'selectedPaymentPaystationId': get_value_or_default('selectedPaymentPaystationId'),
            'hasWorkingJavascript': get_value_or_default('hasWorkingJavascript'),
            'placeYourOrder1': get_value_or_default('placeYourOrder1'),
            'isfirsttimecustomer': get_value_or_default('isfirsttimecustomer'),
            'isTFXEligible': get_value_or_default('isTFXEligible'),
            'isFxEnabled': get_value_or_default('isFxEnabled'),
            'isFXTncShown': get_value_or_default('isFXTncShown'),
        }

        response = requests.post(
            'https://www.amazon.com/gp/buy/spc/handlers/static-submit-decoupled.html/ref=ox_spc_place_order?ie=UTF8&hasWorkingJavascript=',
            data=data, cookies=cookies, headers=headers)

        return response.status_code == 200

    # amazon has an express checkout that add the item to a temp cart
    async def express_checkout() -> bool:
        url = f'https://www.amazon.com/checkout/turbo-initiate?ref_=dp_start-bbf_1_glance_buyNow_2-1&referrer=detail' \
              f'&pipelineType=turbo&clientId=retailwebsite&weblab=RCX_CHECKOUT_TURBO_DESKTOP_PRIME_87783' \
              f'&temporaryAddToCart=1&asin.1={product_id}'

        headers = __get_base_headers()
        session_id = cookies['session-id']
        headers['x-amz-checkout-csrf-token'] = session_id
        data = {'isAsync': "1", 'addressID': address_id, 'offerListing.1': offer_id, 'quantity.1': "1"}
        response = requests.post(url, data=data, cookies=cookies, headers=headers)

        def try_buy(html: str) -> bool:
            soup = BeautifulSoup(html, features="lxml")
            # get element with req id and pid
            ele_json_data = soup.select_one('#checkout-page-container > script:nth-child(3)')
            # get element with token
            ele_token = soup.find('input', {'name': 'anti-csrftoken-a2z'})

            if ele_token is None:
                return False

            csrf_token = ele_token['value']
            json_data = json.loads(ele_json_data.text)
            request_id = json_data['currentRequestId']
            pid = json_data['currentPurchaseId']

            place_order_url = 'https://www.amazon.com/checkout/spc/place-order?ref_=chk_spc_placeOrder&_srcRID' \
                              f'={request_id}&clientId=retailwebsite&pipelineType=turbo&cachebuster=1637754583124' \
                              f'&pid={pid}'

            request_data = {'x-amz-checkout-csrf-token': session_id,
                            'ref_': 'chk_spc_placeOrder',
                            'referrer': 'spc',
                            'pid': pid,
                            'pipelineType': 'turbo',
                            'clientId': 'retailwebsite',
                            'temporaryAddToCart': '1',
                            'hostPage': 'detail',
                            'weblab': 'RCX_CHECKOUT_TURBO_DESKTOP_PRIME_87783',
                            'isClientTimeBased': '1',
                            }
            # adding token to header
            headers['anti-csrftoken-a2z'] = csrf_token

            res = requests.post(place_order_url, data=request_data, headers=headers, cookies=cookies)

            return res.status_code == 200

        return try_buy(response.text)

    # task_express_checkout = await asyncio.create_task(express_checkout())
    task_normal_checkout = await asyncio.create_task(normal_checkout())

    # run both in parallel and hopefully one finish with success, a 200 is not a guarantee that the item was bought
    # await asyncio.gather(task_normal_checkout, task_express_checkout)
    return task_normal_checkout
