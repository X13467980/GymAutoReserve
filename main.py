from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
import time

# Chrome 実行バイナリとChromeDriverパス（Dockerfileの ENV を使う）
import os
CHROME_BIN = os.getenv("CHROME_BIN", "/usr/bin/chromium")
CHROMEDRIVER_PATH = os.getenv("CHROMEDRIVER_PATH", "/usr/lib/chromium/chromedriver")

def make_reservation(date_str: str, time_slot_text: str, user_info: dict):
    logs = []

    def log(msg):
        print(msg)
        logs.append(msg)

    options = Options()
    options.binary_location = CHROME_BIN
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-software-rasterizer")
    options.add_argument("--remote-debugging-port=9222")

    service = Service(CHROMEDRIVER_PATH)
    driver = webdriver.Chrome(service=service, options=options)

    try:
        driver.get("https://select-type.com/rsv/?id=KatPteH9vEg")
        log("✅ ページを開きました")

        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "select")))
        Select(driver.find_element(By.TAG_NAME, "select")).select_by_visible_text("OICトレーニングルーム/OIC Gymnasium")
        log("✅ 会場を選択しました")
        time.sleep(2)

        year, month, day = map(int, date_str.split('-'))
        date_xpath = f'//a[@id="{year}-{month}-{day}_td_cls"]'
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, date_xpath))).click()
        log(f"✅ 日付 {date_str} を選択しました")
        time.sleep(1)

        time_xpath = f'//a[contains(@class, "res-label") and contains(text(), "{time_slot_text}")]'
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, time_xpath))).click()
        log(f"✅ 時間帯「{time_slot_text}」を選択しました")

        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//input[@type="button" and @value="次へ"]'))).click()
        log("✅ 『次へ』をクリックしました")

        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "name")))
        driver.find_element(By.NAME, "name").send_keys(user_info["name"])
        driver.find_element(By.NAME, "email").send_keys(user_info["email"])
        driver.find_element(By.NAME, "email_conf").send_keys(user_info["email"])
        driver.find_element(By.NAME, "other").send_keys(user_info["permit"])
        driver.find_element(By.NAME, "other2").send_keys(user_info["faculty"])
        log("✅ フォームに入力しました")

        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//input[@type="submit" and @value="次へ"]'))).click()
        log("✅ 最終確認へ進みました")

        driver.save_screenshot("before_recaptcha.png")
        time.sleep(30)

        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "ebtn_id"))).click()
        log("✅ 予約確定ボタンをクリックしました")
        driver.save_screenshot("reservation_done.png")
        time.sleep(3)

    except Exception as e:
        driver.save_screenshot("error_screenshot.png")
        log(f"❌ エラー: {e}")
    finally:
        driver.quit()

    return "\n".join(logs), "reservation_done.png"

# テスト用実行
if __name__ == "__main__":
    user = {
        "name": "矢野陽大",
        "email": "is0747fr@ed.ritsumei.ac.jp",
        "permit": "28235",
        "faculty": "情報理工学部"
    }
    print(make_reservation("2025-04-17", "14:30～15:45", user))
