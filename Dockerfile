FROM python:3.10-slim

# ChromeとChromeDriverをインストール（arm64対応）
RUN apt-get update && apt-get install -y \
    curl unzip gnupg wget ca-certificates \
    fonts-liberation libglib2.0-0 libnss3 libgconf-2-4 \
    libxss1 libappindicator3-1 libasound2 libatk-bridge2.0-0 libgtk-3-0 \
    chromium chromium-driver \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 作業ディレクトリ
WORKDIR /app

# requirements
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# アプリ本体
COPY . .

# 環境変数（Selenium用）
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMEDRIVER_PATH=/usr/lib/chromium/chromedriver

# 起動コマンド（任意でFastAPIとかFlaskなら uvicorn 起動でも可）
CMD ["python", "app.py"]