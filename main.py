import asyncio

import stores.amazon
from models import enums
from models.product_options import ProductOptions

USER = 'email'
PASS = 'pass'


async def main():
    products = [ProductOptions('https://www.amazon.com/uxcell-Thermistors-Resistors-Temperature-Sensors/dp'
                               '/B07P5Q67RH/ref=sr_1_3?keywords=thermistor&qid=1636465069&sr=8-3&aod=1', 1, 10),
                ProductOptions('https://www.amazon.com/uxcell-Thermistors-Resistors-Temperature-Sensors/dp'
                               '/B07P5Q67RH/ref=sr_1_3?keywords=thermistor&qid=1636465069&sr=8-3&aod=1', 1, 10),
                ProductOptions('https://www.amazon.com/uxcell-Thermistors-Resistors-Temperature-Sensors/dp'
                               '/B07P5Q67RH/ref=sr_1_3?keywords=thermistor&qid=1636465069&sr=8-3&aod=1', 1, 10)
                ]

    driver = stores.amazon.init_logged_in_driver(enums.BrowsersEnum.FIREFOX, USER, PASS)

    stores.amazon.init_store(driver, products, enums.BrowsersEnum.FIREFOX).subscribe()


loop = asyncio.get_event_loop()
loop.create_task(main())
loop.run_forever()
