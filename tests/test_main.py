# tests/test_main.py
import os
import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By


@pytest.fixture
def driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")

    driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(10)
    yield driver
    driver.quit()


def test_text(driver):
    base_url = os.getenv("BASE_URL", "http://localhost:5173")
    driver.get(base_url)
    parent_div = driver.find_element(By.CSS_SELECTOR, "#child-div")
    print(parent_div.text)
    assert parent_div.text != ""
