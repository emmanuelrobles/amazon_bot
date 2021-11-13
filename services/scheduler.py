from typing import Optional, Callable

import rx
from selenium.webdriver.remote.webdriver import WebDriver

from models.communication import Action
import rx.operators as ops


def init_scheduler(get_driver: Callable[[], WebDriver], try_get_metadata: Callable[[WebDriver], Optional[Action]], interval=1) -> rx.Observable:
    driver = get_driver()

    def get_metadata():
        nonlocal driver
        try:
            return try_get_metadata(driver)
        except Exception as e:
            print(e)
            driver = get_driver()
            try_get_metadata(driver)

    return rx.interval(interval).pipe(
        ops.map(lambda i: get_metadata()),
        ops.filter(lambda v: v is not None),
    )
