# test_carousel.py
import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By


@pytest.fixture
def driver():
    driver = webdriver.Chrome()
    driver.get("http://localhost:5173/")
    driver.implicitly_wait(10)
    yield driver
    driver.quit()


def test_text(driver):  # ← takes driver as parameter
    parent_div = driver.find_element(By.CSS_SELECTOR, "#child-div")
    print(parent_div.text)
    assert parent_div.text != ""  # ← actual check
