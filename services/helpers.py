from typing import Callable

import rx.operators
from rx import Observable
from selenium.webdriver.remote.webdriver import WebDriver


def of_type(action_type: str) -> Callable[[Observable], Observable]:
    return rx.operators.filter(lambda action: action.action_type == action_type)


def get_cookies_from_driver(driver: WebDriver) -> dict:
    # get cookies
    cookies = {}
    selenium_cookies = driver.get_cookies()
    for cookie in selenium_cookies:
        cookies[cookie['name']] = cookie['value']
    return cookies
