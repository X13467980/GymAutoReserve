from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
import time
from dotenv import load_dotenv
import os

# .env 読み込み
load_dotenv()

# ユーザー情報を環境変数から取得
USER_INFO = {
    "name": os.getenv("USER_NAME"),
    "email": os.getenv("USER_EMAIL"),
    "permit": os.getenv("USER_PERMIT"),
    "faculty": os.getenv("USER_FACULTY")
}

# Chrome 実行バイナリとChromeDriverパス（Dockerfileの ENV を使う）
CHROME_BIN = os.getenv("CHROME_BIN", "/usr/bin/chromium")
CHROMEDRIVER_PATH = os.getenv("CHROMEDRIVER_PATH", "/usr/lib/chromium/chromedriver")

def make_reservation(date_str: str, time_slot_text: str):
    options = Options()
    options.binary_location = CHROME_BIN
    options.add_argument("--headless=new")  # ←ここ重要。新しいヘッドレスモードを使う
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-setuid-sandbox")
    options.add_argument("--remote-debugging-port=9222")  # ← これがないと DevToolsActivePort が作られない

    service = Service(CHROMEDRIVER_PATH)
    driver = webdriver.Chrome(service=service, options=options)

    try:
        driver.get("https://select-type.com/rsv/?id=KatPteH9vEg")
        print("✅ ページを開きました")

        # 会場選択
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "select")))
        Select(driver.find_element(By.TAG_NAME, "select")).select_by_visible_text("OICトレーニングルーム/OIC Gymnasium")
        print("✅ 会場を選択しました")
        time.sleep(2)

        # 日付選択
        year, month, day = map(int, date_str.split('-'))
        date_xpath = f'//a[@id="{year}-{month}-{day}_td_cls"]'
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, date_xpath))).click()
        print(f"✅ 日付 {date_str} を選択しました")
        time.sleep(1)

        # 時間帯選択
        time_xpath = f'//a[contains(@class, "res-label") and contains(text(), "{time_slot_text}")]'
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, time_xpath))).click()
        print(f"✅ 時間帯「{time_slot_text}」を選択しました")

        # 次へボタン
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//input[@type="button" and @value="次へ"]'))
        ).click()
        print("✅ 『次へ』をクリックしました")

        # 入力フォーム
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "name")))
        driver.find_element(By.NAME, "name").send_keys(USER_INFO["name"])
        driver.find_element(By.NAME, "email").send_keys(USER_INFO["email"])
        driver.find_element(By.NAME, "email_conf").send_keys(USER_INFO["email"])
        driver.find_element(By.NAME, "other").send_keys(USER_INFO["permit"])
        driver.find_element(By.NAME, "other2").send_keys(USER_INFO["faculty"])
        print("✅ フォームに入力しました")

        # 最終確認へ
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//input[@type="submit" and @value="次へ"]'))
        ).click()
        print("✅ 最終確認へ進みました")

        # reCAPTCHA 対応
        print("⚠️ reCAPTCHA 対応してください（30秒待機）")
        driver.save_screenshot("before_recaptcha.png")
        time.sleep(30)

        # 確定
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "ebtn_id"))
        ).click()
        print("✅ 予約確定ボタンをクリックしました")
        driver.save_screenshot("reservation_done.png")
        time.sleep(3)

    except Exception as e:
        driver.save_screenshot("error_screenshot.png")
        print(f"❌ エラー: {e}")

    finally:
        driver.quit()

# 実行例
if __name__ == "__main__":
    make_reservation("2025-04-17", "14:30～15:45")