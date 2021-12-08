from seleniumwire import webdriver

from models.enums import BrowsersEnum


def get_a_driver(browser: BrowsersEnum, is_headless=True, seleniumwire_options=None):
    if browser is BrowsersEnum.FIREFOX:
        options = webdriver.FirefoxOptions()
        options.headless = is_headless
        from selenium.webdriver.firefox.service import Service
        from webdriver_manager.firefox import GeckoDriverManager
        service = Service(GeckoDriverManager().install())
        return webdriver.Firefox(service=service, options=options, seleniumwire_options=seleniumwire_options)
    if browser is BrowsersEnum.CHROME:
        options = webdriver.ChromeOptions()
        options.headless = is_headless
        from selenium.webdriver.chrome.service import Service
        from webdriver_manager.chrome import DriverManager
        service = Service(DriverManager().install())
        return webdriver.Chrome(service=service, options=options)
    if browser is BrowsersEnum.CHROMIUM:
        from selenium.webdriver.chromium.options import ChromiumOptions
        from selenium.webdriver.chromium.webdriver import ChromiumDriver
        from selenium.webdriver.chromium.webdriver import ChromiumDriver
        options = ChromiumOptions()
        options.headless = is_headless
        from selenium.webdriver.chromium.service import ChromiumService
        from webdriver_manager.chrome import ChromeDriverManager
        from webdriver_manager.utils import ChromeType
        service = ChromiumService(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install(),
                                  start_error_message='Couldnt start')
        return ChromiumDriver(service=service, options=options, browser_name="chromium", vendor_prefix="webkit",
                              seleniumwire_options=seleniumwire_options)
