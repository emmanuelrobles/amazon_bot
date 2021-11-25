import json
import time
from typing import Optional, Callable
from bs4 import BeautifulSoup
import requests

from browser.driver import get_a_driver
from models.communication import Action
from models.enums import BrowsersEnum
from services.helpers import get_cookies_from_driver
from stores.Amazon.actions import on_product_not_found, on_product_found
from stores.Amazon.models import AmazonSiteData, AmazonProductNotFoundAction, AmazonProductFoundAction, AmazonProduct


def __get_base_headers() -> dict:
    return {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:66.0) Gecko/20100101 Firefox/66.0",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept": "*/*",
            "DNT": "1",
            "Connection": "close",
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'no-cors',
            'Sec-Fetch-Site': 'same-origin',
            'Pragma': 'no-cache',
            'Cache-Control': 'no-cache',
            'TE': 'trailers'
            }


def init_scrap(get_html_callback: Callable[[], Callable[[str], str]]) -> Callable[[AmazonProduct], Action]:
    # use to refresh in case of captcha
    get_html = get_html_callback()

    def scrap_product(product: AmazonProduct) -> Action:

        def get_data() -> Action:
            data = get_html(product.url)
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


def get_data_using_request(browser: BrowsersEnum) -> Callable[[str], str]:
    driver = get_a_driver(browser, False)

    # clear cookies
    driver.delete_all_cookies()

    driver.get('https://www.amazon.com')
    # wait to load everything and fix captcha
    time.sleep(5)

    # get cookies
    cookies = get_cookies_from_driver(driver)

    # close driver
    driver.close()

    def get_page_source(url: str) -> str:
        headers = __get_base_headers()
        # make request
        response = requests.get(url, headers=headers, cookies=cookies)

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


def express_checkout(product_id: str) -> Callable[[str, str, dict], bool]:
    url = f'https://www.amazon.com/checkout/turbo-initiate?ref_=dp_start-bbf_1_glance_buyNow_2-1&referrer=detail' \
          f'&pipelineType=turbo&clientId=retailwebsite&weblab=RCX_CHECKOUT_TURBO_DESKTOP_PRIME_87783' \
          f'&temporaryAddToCart=1&asin.1={product_id}'

    def try_checkout(address_id: str, offer_id: str, cookies: dict) -> bool:
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

    return try_checkout
