# Dockerfile
FROM python:3.10-slim

# 必要なパッケージのインストール
RUN apt-get update && apt-get install -y \
    chromium chromium-driver \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# 環境変数を設定（Pythonからも参照できるように）
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver

WORKDIR /app
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt
COPY . .

CMD ["python", "app.py"]