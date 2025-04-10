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

# ✅ 状態管理（簡易）
user_state = {}

# ✅ 日付選択 QuickReply
def generate_date_quick_reply():
    today = datetime.now()
    quick_items = []

    for i in range(6):  # 今日から12日後まで（最大13個）
        date = today + timedelta(days=i)
        label = f"{date.month}月{date.day}日"
        text = date.strftime("%Y-%m-%d")
        quick_items.append(
            QuickReplyItem(action=MessageAction(label=label, text=text))
        )

    return QuickReply(items=quick_items)

# ✅ 時間帯選択 QuickReply
def generate_time_quick_reply():
    times = ["14:30～15:45", "16:00～17:15"]
    quick_items = [
        QuickReplyItem(action=MessageAction(label=t, text=t)) for t in times
    ]
    return QuickReply(items=quick_items)


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

    # ステップ1: 「予約」
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

    # ステップ2: 日付が選ばれたら時間帯へ
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

    # ステップ3: 時間を受け取って予約完了へ（実処理は後で実装）
    if user_state.get(user_id, {}).get("step") == "waiting_for_time":
        selected_date = user_state[user_id]["date"]
        selected_time = text

        # 予約処理（ここに make_reservation() を呼び出してもOK！）
        print(f"🎯 予約実行: {selected_date} {selected_time}")

        messaging_api.reply_message(
            ReplyMessageRequest(
                reply_token=reply_token,
                messages=[
                    TextMessage(text=f"✅ 予約完了しました！\n{selected_date} {selected_time}")
                ]
            )
        )

        user_state.pop(user_id, None)
        return

    # その他
    messaging_api.reply_message(
        ReplyMessageRequest(
            reply_token=reply_token,
            messages=[TextMessage(text="「予約」と送って始めてください！")]
        )
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)