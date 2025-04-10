from flask import Flask, request, abort
from linebot.v3 import WebhookHandler
from linebot.v3.messaging import (
    MessagingApi, ReplyMessageRequest, TextMessage,
    Configuration, ApiClient,
    QuickReply, QuickReplyItem, MessageAction
)
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.webhooks import MessageEvent, TextMessageContent

from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

channel_secret = os.getenv("LINE_CHANNEL_SECRET")
access_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")

print("✅ CHANNEL SECRET:", channel_secret)
print("✅ ACCESS TOKEN:", access_token)

if not channel_secret or not access_token:
    print("❌ .env の読み込み失敗！")
    exit(1)

configuration = Configuration(access_token=access_token)
api_client = ApiClient(configuration)
messaging_api = MessagingApi(api_client)
handler = WebhookHandler(channel_secret)


def generate_date_quick_reply():
    today = datetime.now()
    quick_items = []

    for i in range(13):  # 今日から12日後まで
        date = today + timedelta(days=i)
        label = f"{date.month}月{date.day}日"
        text = date.strftime("%Y-%m-%d")
        quick_items.append(
            QuickReplyItem(action=MessageAction(label=label, text=text))
        )

    return QuickReply(items=quick_items)


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

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("❌ 署名検証エラー！")
        abort(403)

    return "OK"


@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    print("💬 LINEからメッセージ受信")
    user_id = event.source.user_id
    reply_token = event.reply_token
    text = event.message.text.strip()

    print(f"[{user_id}] {text}")

    if text == "予約":
        messaging_api.reply_message(
            ReplyMessageRequest(
                reply_token=reply_token,
                messages=[
                    TextMessage(
                        text="予約したい日付を選んでください",
                        quick_reply=generate_date_quick_reply()
                    )
                ]
            )
        )
    else:
        messaging_api.reply_message(
            ReplyMessageRequest(
                reply_token=reply_token,
                messages=[TextMessage(text="「予約」と送って始めてください！")]
            )
        )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)