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

# 🔽 予約処理関数をインポート
from main import make_reservation

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

# ✅ 状態管理
user_state = {}

def generate_date_quick_reply():
    today = datetime.now()
    quick_items = []

    for i in range(6):
        date = today + timedelta(days=i)
        label = f"{date.month}月{date.day}日"
        text = date.strftime("%Y-%m-%d")
        quick_items.append(QuickReplyItem(action=MessageAction(label=label, text=text)))

    return QuickReply(items=quick_items)

def generate_time_quick_reply():
    times = ["14:30～15:45", "16:00～17:15"]
    return QuickReply(items=[
        QuickReplyItem(action=MessageAction(label=t, text=t)) for t in times
    ])

@app.route("/", methods=["GET"])
def root():
    return "✅ Flask is running!"

@app.route("/callback", methods=["POST"])
def callback():
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
        user_state[user_id] = {"step": "waiting_for_date"}
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
        return

    if user_state.get(user_id, {}).get("step") == "waiting_for_date":
        user_state[user_id]["date"] = text
        user_state[user_id]["step"] = "waiting_for_time"
        messaging_api.reply_message(
            ReplyMessageRequest(
                reply_token=reply_token,
                messages=[
                    TextMessage(
                        text=f"{text} の時間帯を選んでください",
                        quick_reply=generate_time_quick_reply()
                    )
                ]
            )
        )
        return

    if user_state.get(user_id, {}).get("step") == "waiting_for_time":
        selected_date = user_state[user_id]["date"]
        selected_time = text

        try:
            make_reservation(selected_date, selected_time)
            reply_text = f"✅ 予約完了しました！\n{selected_date} {selected_time}"
        except Exception as e:
            reply_text = f"❌ 予約に失敗しました。\nエラー: {str(e)}"

        messaging_api.reply_message(
            ReplyMessageRequest(
                reply_token=reply_token,
                messages=[TextMessage(text=reply_text)]
            )
        )
        user_state.pop(user_id, None)
        return

    messaging_api.reply_message(
        ReplyMessageRequest(
            reply_token=reply_token,
            messages=[TextMessage(text="「予約」と送って始めてください！")]
        )
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)