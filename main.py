from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
import time

# ーーー🔧 自動入力するユーザー情報 ーーー
USER_INFO = {
    "name": "矢野陽大",
    "email": "is0747fr@ed.ritsumei.ac.jp",
    "permit": "28235",
    "faculty": "情報理工学部"
}

def make_reservation(date_str: str, time_slot_text: str):
    """
    指定した日付と時間帯で予約を自動実行する関数
    - date_str: "2025-04-15"
    - time_slot_text: "14:30～15:45"
    """

    driver = webdriver.Chrome()

    try:
        driver.get("https://select-type.com/rsv/?id=KatPteH9vEg")

        # ① 種別選択
        select_elem = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "select"))
        )
        Select(select_elem).select_by_visible_text("OICトレーニングルーム/OIC Gymnasium")
        time.sleep(2)

        # ② 日付をクリック
        year, month, day = map(int, date_str.split('-'))
        xpath = f'//td[@data-day="{year}-{month:02d}-{day:02d}"]//div[contains(@class, "blue")]'
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, xpath))).click()
        time.sleep(1)

        # ③ 時間帯を選択
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, f'//div[contains(text(), "{time_slot_text}")]'))
        ).click()

        # ④ 「次へ」
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//button[contains(text(), "次へ")]'))
        ).click()

        # ⑤ フォーム入力
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "お名前")))
        driver.find_element(By.NAME, "お名前").send_keys(USER_INFO["name"])
        driver.find_element(By.NAME, "メールアドレス").send_keys(USER_INFO["email"])
        driver.find_element(By.NAME, "メールアドレス（確認）").send_keys(USER_INFO["email"])
        driver.find_element(By.NAME, "利用許可証番号").send_keys(USER_INFO["permit"])
        driver.find_element(By.NAME, "学部").send_keys(USER_INFO["faculty"])

        # ⑥ 「次へ」ボタン（最終確認画面へ）
        driver.find_element(By.XPATH, '//button[contains(text(), "次へ")]').click()

        # 完了までしばらく待機
        time.sleep(5)

    finally:
        driver.quit()