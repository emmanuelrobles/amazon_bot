import asyncio
from typing import Callable

from rx import Observable
from rx.scheduler import ThreadPoolScheduler

import stores.amazon
from browser.driver import get_a_driver
from models import enums
from models.communication import Action
import rx.operators as ops
import services.scheduler as SchedulerObs
from stores.amazon import AmazonMetadata

USER = 'email'
PASS = 'password'


def get_amazon() -> Observable:
    scheduler = ThreadPoolScheduler()

    p1 = SchedulerObs.init_scheduler(lambda:
                                     stores.Amazon.get_default_driver(enums.BrowsersEnum.FIREFOX)
                                     ('https://www.amazon.com/uxcell-Thermistors-Resistors-Temperature-Sensors/dp'
                                      '/B07P5Q67RH/ref=sr_1_3?keywords=thermistor&qid=1636465069&sr=8-3&aod=1'),
                                     stores.Amazon.get_product_metadata(10))

    p2 = SchedulerObs.init_scheduler(lambda:
                                     stores.Amazon.get_default_driver(enums.BrowsersEnum.FIREFOX)
                                     ('https://www.amazon.com/Thermometer-Adults-Digital-Oral-Fever/dp/B08B7V2RG3/ref'
                                      '=sr_1_6?crid=IY1ROXH1ARLN&keywords=thermometer&qid=1636468332&sprefix=therm%2Caps'
                                      '%2C257&sr=8-6&aod=1'),
                                     stores.Amazon.get_product_metadata(10))

    return p1.pipe(
        ops.merge(p2),
        ops.observe_on(scheduler)
    )


async def main():
    c = init_logged_browser()
    get_amazon() \
        .pipe(
        ops.map(c)
    ).subscribe()


def init_logged_browser() -> Callable[[Action[AmazonMetadata]], None]:
    driver = get_a_driver(enums.BrowsersEnum.FIREFOX, False)
    driver = stores.Amazon.get_logged_in_driver(driver)(USER, PASS)

    def get_url(url: str):
        driver.get(url)

    return lambda action: get_url(action.data.add_to_cart_callback())


loop = asyncio.get_event_loop()
loop.create_task(main())
loop.run_forever()
