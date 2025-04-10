from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
import time

CHROMEDRIVER_PATH = "/usr/local/bin/chromedriver"

USER_INFO = {
    "name": "矢野陽大",
    "email": "is0747fr@ed.ritsumei.ac.jp",
    "permit": "28235",
    "faculty": "情報理工学部"
}

def make_reservation(date_str: str, time_slot_text: str):
    service = Service(CHROMEDRIVER_PATH)
    options = Options()
    # options.add_argument("--headless")

    driver = webdriver.Chrome(service=service, options=options)

    try:
        driver.get("https://select-type.com/rsv/?id=KatPteH9vEg")
        print("✅ ページを開きました")

        select_elem = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "select"))
        )
        Select(select_elem).select_by_visible_text("OICトレーニングルーム/OIC Gymnasium")
        print("✅ 予約の種類を選択しました")
        time.sleep(2)

        year, month, day = map(int, date_str.split('-'))
        xpath = f'//a[@id="{year}-{month}-{day}_td_cls"]'
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, xpath))
        ).click()
        print(f"✅ 日付 {date_str} を選択しました")
        time.sleep(1)

        try:
            print("⌛ 時間帯を検索中…")
            time_xpath = f'//a[contains(@class, "res-label") and contains(text(), "{time_slot_text}")]'
            time_slot = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, time_xpath))
            )
            time_slot.click()
            print(f"✅ 時間帯「{time_slot_text}」を選択しました")
        except Exception as e:
            driver.save_screenshot("no_time_slot.png")
            print(f"❌ 時間帯「{time_slot_text}」が見つかりませんでした: {e}")
            return

        try:
            print("⌛ 『次へ』ボタンを待機中…")
            WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//input[@type="button" and @value="次へ"]'))
            ).click()
            print("✅ 次へをクリック")
        except Exception as e:
            driver.save_screenshot("next_button_error.png")
            print(f"❌ 『次へ』ボタンのクリックに失敗しました: {e}")
            return

        try:
            print("⌛ 入力フォームの読み込みを待機中…")
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "name")))
            driver.find_element(By.NAME, "name").send_keys(USER_INFO["name"])
            driver.find_element(By.NAME, "email").send_keys(USER_INFO["email"])
            driver.find_element(By.NAME, "email_conf").send_keys(USER_INFO["email"])
            driver.find_element(By.NAME, "other").send_keys(USER_INFO["permit"])
            driver.find_element(By.NAME, "other2").send_keys(USER_INFO["faculty"])
            print("✅ 入力フォーム完了")
        except Exception as e:
            driver.save_screenshot("form_input_error.png")
            print(f"❌ 入力フォームの読み込みに失敗しました: {e}")
            return

        try:
            WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//input[@type="button" and @value="次へ"]'))
            ).click()
            print("✅ 最終確認へ進みました")
        except Exception as e:
            driver.save_screenshot("form_next_button_error.png")
            print(f"❌ 入力後の『次へ』ボタンのクリックに失敗しました: {e}")
            return

        time.sleep(5)

    except Exception as e:
        driver.save_screenshot("error_screenshot.png")
        print(f"❌ エラー発生: {e}")

    finally:
        driver.quit()

if __name__ == "__main__":
    make_reservation("2025-04-15", "14:30～15:45")