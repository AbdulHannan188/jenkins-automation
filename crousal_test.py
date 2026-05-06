from selenium import webdriver
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import time
import re

driver = webdriver.Chrome()
driver.get("https://staging.aliflaila.app/")
time.sleep(2)

soup = BeautifulSoup(driver.page_source, "html.parser")

def get_x_position(element):
    style = element.get_attribute("style")
    match = re.search(r'translate3d\(([-\d.]+)px', style)
    if match:
        return float(match.group(1))
    return 0.0

buttons = soup.find_all("div")  # prevIcon is a div, not button
for button in buttons:
    classes = button.attrs.get("class", [])  # returns list
    # check if any class in the list ends with 'prevIcon'
    if any("prevIcon" in c for c in classes):
        print(button.get_text(), button.attrs, sep="\n")


crousal_prev_div = driver.find_element(By.CSS_SELECTOR, "[class*='prevIcon']")

crousal_next_div = driver.find_element(By.CSS_SELECTOR, "[class*='nextIcon']")

# Finding how much pixels crousal moves

crousal_parent_div = driver.find_element(By.CSS_SELECTOR, "[class*='emblaContainer']")
# print("Before Clicking div_style:", crousal_parent_div.get_attribute("style"))
x_before = get_x_position(crousal_parent_div)
print(f"Position before: {x_before}px")

crousal_next_div.click()
time.sleep(2)

print("Crousal Prev_btn div attr:", crousal_prev_div.get_attribute("class"))

crousal_prev_div.click()
time.sleep(2)


print("Crousal Prev_btn div attr:", crousal_prev_div.get_attribute("class"))


time.sleep(10)
print("After Clicking div_style:", crousal_parent_div.get_attribute("style"))
x_after = get_x_position(crousal_parent_div)
print(f"Position after: {x_after}px")


distance = abs(x_before-x_after)
print("Distance is:", distance)

driver.quit()
