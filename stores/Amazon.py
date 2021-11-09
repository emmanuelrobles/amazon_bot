from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait


def check_price(driver) -> float:
    return float((driver.find_element(By.ID, "corePrice_feature_div").text[1:]).replace(',', ''))


def buy_item(driver, username, password):
    driver.find_element(By.ID, 'submit.buy-now').click()

    if driver.current_url.startswith("https://www.amazon.com/ap/signin"):
        sign_in(driver, username, password)

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "submitOrderButtonId"))).click()


def sign_in(driver, username, password):
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "ap_email"))).send_keys(username)

    driver.find_element(By.ID, 'continue').click()

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "ap_password"))).send_keys(password)

    driver.find_element(By.ID, 'signInSubmit').click()
