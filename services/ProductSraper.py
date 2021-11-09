import rx
from rx import Observable
from rx.subject import Subject

from browser.Driver import get_a_driver
from models.Browsers import BrowsersEnum
from models.ProductOptions import ProductOptions
import asyncio
import rx.operators as ops

from stores import Amazon


def init_scraper(options: ProductOptions, browser: BrowsersEnum) -> rx.Observable:
    driver = get_a_driver(browser)
    driver.get(options.url)
    return rx.interval(1).pipe(
        ops.map(lambda i: rx.of(get_price(options,driver))),
    )


def get_price(options: ProductOptions, driver):
    try:
        driver.refresh()
        if Amazon.check_price(driver) <= options.price:
            return driver.current_url
        else:
            return None
    except Exception as e:
        print(e)


class Product:
    def __init__(self, options: ProductOptions, browser: BrowsersEnum):
        self.options = options
        self.browserEnum = browser
        self.subject = Subject()
        driver = get_a_driver(self.browserEnum)
        driver.get(self.options.url)
        asyncio.ensure_future(self.__start_watching(driver))

    async def __start_watching(self, driver):
        while True:
            await asyncio.sleep(1)
            try:
                driver.refresh()
                if Amazon.check_price(driver) <= self.options.price:
                    self.subject.on_next(driver)
            except Exception as e:
                print(e)

    def on_product_observable(self) -> Observable:
        return self.subject
