FROM python:3.10-slim

# 必要な依存関係をインストール
RUN apt-get update && apt-get install -y \
    chromium-driver \
    chromium \
    wget \
    unzip \
    curl \
    gnupg \
    libglib2.0-0 \
    libnss3 \
    libgconf-2-4 \
    libfontconfig1 \
    libxss1 \
    libappindicator3-1 \
    libasound2 \
    libx11-xcb1 \
    fonts-liberation \
    libatk-bridge2.0-0 \
    libgtk-3-0 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libxtst6 \
    xdg-utils \
    libu2f-udev \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# 環境変数で明示的にパスを通す（ここ重要）
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver

# 作業ディレクトリ
WORKDIR /app

# Python依存のインストール
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# アプリケーションのコピー
COPY . .

# ポートと起動
EXPOSE 5000
CMD ["python", "app.py"]