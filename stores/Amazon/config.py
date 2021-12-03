from typing import List

from models.enums import BrowsersEnum
from stores.Amazon.models import AmazonConfig, AmazonProduct


def amazon_config_from_json(data: dict) -> AmazonConfig:
    def products_from_json() -> List[AmazonProduct]:
        products = []
        for product in data['products']:
            products.append(AmazonProduct(product['id'], product['qty'], product['price']))
        return products

    credentials = data['credentials']

    return AmazonConfig(credentials['user'],
                        credentials['password'],
                        data['addressId'],
                        products_from_json(),
                        BrowsersEnum(data['scraperBrowser']),
                        BrowsersEnum(data['autoBuyBrowser']),
                        data['browserWait'])
