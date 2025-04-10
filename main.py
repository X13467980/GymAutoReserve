from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
import time

# ✅ 自分のChromeDriverのパスを指定してください！
CHROMEDRIVER_PATH = "/usr/local/bin/chromedriver"  # ← Mac/Linuxの例（確認してね）
# CHROMEDRIVER_PATH = "C:\\Users\\YourName\\Downloads\\chromedriver.exe"  # ← Windowsの例

USER_INFO = {
    "name": "矢野陽大",
    "email": "is0747fr@ed.ritsumei.ac.jp",
    "permit": "28235",
    "faculty": "情報理工学部"
}

def make_reservation(date_str: str, time_slot_text: str):
    # ChromeDriverサービス指定
    service = Service(CHROMEDRIVER_PATH)
    
    # Chromeオプション（必要に応じてheadless除外）
    options = Options()
    # options.add_argument("--headless")  # ← 表示確認したいときはコメントアウトしてね！

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
        xpath = f'//td[@data-day="{year}-{month:02d}-{day:02d}"]//div[contains(@class, "blue")]'
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, xpath))).click()
        print(f"✅ 日付 {date_str} を選択しました")
        time.sleep(1)

        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, f'//div[contains(text(), "{time_slot_text}")]'))
        ).click()
        print(f"✅ 時間帯「{time_slot_text}」を選択しました")

        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//button[contains(text(), "次へ")]'))
        ).click()
        print("✅ 次へをクリック")

        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "お名前")))
        driver.find_element(By.NAME, "お名前").send_keys(USER_INFO["name"])
        driver.find_element(By.NAME, "メールアドレス").send_keys(USER_INFO["email"])
        driver.find_element(By.NAME, "メールアドレス（確認）").send_keys(USER_INFO["email"])
        driver.find_element(By.NAME, "利用許可証番号").send_keys(USER_INFO["permit"])
        driver.find_element(By.NAME, "学部").send_keys(USER_INFO["faculty"])
        print("✅ 入力フォーム完了")

        driver.find_element(By.XPATH, '//button[contains(text(), "次へ")]').click()
        print("✅ 最終確認へ進みました")

        time.sleep(5)

    finally:
        driver.quit()

if __name__ == "__main__":
    make_reservation("2025-04-15", "14:30～15:45")
