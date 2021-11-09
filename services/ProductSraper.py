import rx

from browser.Driver import get_a_driver
from models.Browsers import BrowsersEnum
from models.ProductOptions import ProductOptions
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

