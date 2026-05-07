# tests/conftest.py
import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

@pytest.fixture
def driver():
    options = Options()
    options.add_argument("--headless")           # ← required on Jenkins (no display)
    options.add_argument("--no-sandbox")         # ← required when running as root
    options.add_argument("--disable-dev-shm-usage")  # ← prevents crashes in CI
    driver = webdriver.Chrome(options=options)
    yield driver
    driver.quit()