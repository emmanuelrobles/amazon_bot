from typing import Optional, Callable

import rx
from selenium.webdriver.remote.webdriver import WebDriver

from models.communication import Action
import rx.operators as ops


def init_scheduler(get_driver: Callable[[], WebDriver], get_metadata: Callable[[WebDriver], Optional[Action]], interval=1) -> rx.Observable:
    driver = get_driver()

    return rx.interval(interval).pipe(
        ops.map(lambda i: get_metadata(driver)),
        ops.filter(lambda v: v is not None)
    )
