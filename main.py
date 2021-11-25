import asyncio

import stores.amazon
from models import enums
from stores.Amazon.models import AmazonProduct

USER = ''
PASS = ''


async def main():
    products = [
        # ProductOptions('https://www.amazon.com/dp/B097CMQVF4?smid=ATVPDKIKX0DER&aod=1', 2, 500),
        # ProductOptions('https://www.amazon.com/dp/B09C43DLXG/#aod?smid=ATVPDKIKX0DER&aod=1', 2, 520),
        # ProductOptions('https://www.amazon.com/dp/B098682XKX/#aod?smid=ATVPDKIKX0DER&aod=1', 2, 500),
        # ProductOptions('https://www.amazon.com/dp/B096WM6JFS?smid=ATVPDKIKX0DER&aod=1', 1, 800),
        # ProductOptions('https://www.amazon.com/gp/aod/ajax/ref=auto_load_aod?asin=B09B2W2ZQ3&pc=dp', 1, 800),

        # ProductOptions('https://www.amazon.com/gp/aod/ajax/ref=auto_load_aod?asin=B097CMQVF4&pc=dp', 2, 500),
        # ProductOptions('https://www.amazon.com/gp/aod/ajax/ref=auto_load_aod?asin=B09C43DLXG&pc=dp', 2, 500),
        # ProductOptions('https://www.amazon.com/gp/aod/ajax/ref=auto_load_aod?asin=B098682XKX&pc=dp', 2, 530),
        # ProductOptions('https://www.amazon.com/gp/aod/ajax/ref=auto_load_aod?asin=B096WM6JFS&pc=dp', 1, 800),
        # ProductOptions('https://www.amazon.com/gp/aod/ajax/ref=auto_load_aod?asin=B083Z5P6TX&pc=dp', 2, 510),
        # ProductOptions('https://www.amazon.com/gp/aod/ajax/ref=auto_load_aod?asin=B09CBQYXLN&pc=dp', 1, 600),
        # ProductOptions('https://www.amazon.com/gp/aod/ajax/ref=auto_load_aod?asin=B098PJNWKD&pc=dp', 1, 570),
        # ProductOptions('https://www.amazon.com/gp/aod/ajax/ref=auto_load_aod?asin=B0985YLRB3&pc=dp', 1, 610),
        # ProductOptions('https://www.amazon.com/gp/aod/ajax/ref=auto_load_aod?asin=B08HHDP9DW&pc=dp', 1, 1000),
        # ProductOptions('https://www.amazon.com/gp/aod/ajax/ref=auto_load_aod?asin=B083HZG3HK&pc=dp', 1, 1640),
        # ProductOptions('https://www.amazon.com/gp/aod/ajax/ref=auto_load_aod?asin=B083HZGMWZ&pc=dp', 1, 1500),
        # ProductOptions('https://www.amazon.com/gp/aod/ajax/ref=auto_load_aod?asin=B08P3ZN62G&pc=dp', 1, 1000),
        # ProductOptions('https://www.amazon.com/gp/aod/ajax/ref=auto_load_aod?asin=B096L3GLYS&pc=dp', 1, 1500),

        # Doest work when its only one offer? maybe TODO investigate issue
        # AmazonProduct('B07NS655QM', 1, 20),
        AmazonProduct('B097CMQVF4', 1, 500),
        AmazonProduct('B09C43DLXG', 1, 500),
        AmazonProduct('B098682XKX', 1, 530),
        AmazonProduct('B096WM6JFS', 1, 800),
        AmazonProduct('B083Z5P6TX', 1, 510),
        AmazonProduct('B09CBQYXLN', 1, 600),
        AmazonProduct('B098PJNWKD', 1, 570),
        AmazonProduct('B0985YLRB3', 1, 610),
        AmazonProduct('B08HHDP9DW', 1, 1000),
        AmazonProduct('B083HZG3HK', 1, 1640),
        AmazonProduct('B083HZGMWZ', 1, 1500),
        AmazonProduct('B08P3ZN62G', 1, 1000),
        AmazonProduct('B096L3GLYS', 1, 1500),
    ]

    driver = stores.amazon.init_logged_in_driver(enums.BrowsersEnum.FIREFOX, USER, PASS)

    stores.amazon.init_store(driver, products).subscribe()

loop = asyncio.get_event_loop()
loop.create_task(main())
loop.run_forever()
