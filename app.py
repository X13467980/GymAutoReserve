from flask import Flask, request, abort
from linebot.v3 import WebhookHandler
from linebot.v3.messaging import (
    MessagingApi, ReplyMessageRequest, TextMessage,
    Configuration, ApiClient
)
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.webhooks import MessageEvent, TextMessageContent
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# .env 読み込みチェック
channel_secret = os.getenv("LINE_CHANNEL_SECRET")
access_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")

print("✅ CHANNEL SECRET:", channel_secret)
print("✅ ACCESS TOKEN:", access_token)

if not channel_secret or not access_token:
    print("❌ .env の読み込み失敗！")
    exit(1)

# LINE Messaging API の設定
configuration = Configuration(access_token=access_token)
api_client = ApiClient(configuration)
messaging_api = MessagingApi(api_client)
handler = WebhookHandler(channel_secret)

@app.route("/", methods=["GET"])
def root():
    return "✅ Flask is running!"

@app.route("/callback", methods=["POST"])
def callback():
    print("📩 Flaskの /callback に POST きたよ！！")

    signature = request.headers.get("X-Line-Signature", "")
    body = request.get_data(as_text=True)

    print("==== Webhook受信 ====")
    print("Signature:", signature)
    print("Body:", body)
    print("=====================")

    return "OK"

@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    print("💬 LINEからメッセージ受信")
    user_id = event.source.user_id
    reply_token = event.reply_token
    text = event.message.text

    print(f"[{user_id}] {text}")

    messaging_api.reply_message(
        ReplyMessageRequest(
            reply_token=reply_token,
            messages=[TextMessage(text="予約ですね！日付を選んでください")]
        )
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)