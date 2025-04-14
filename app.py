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
from threading import Thread
import os
from dotenv import load_dotenv
from main import make_reservation
from linebot.v3.messaging import PushMessageRequest

load_dotenv()
app = Flask(__name__)

channel_secret = os.getenv("LINE_CHANNEL_SECRET")
access_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")

configuration = Configuration(access_token=access_token)
api_client = ApiClient(configuration)
messaging_api = MessagingApi(api_client)
handler = WebhookHandler(channel_secret)

user_state = {}

def generate_date_quick_reply():
    today = datetime.now()
    return QuickReply(items=[
        QuickReplyItem(action=MessageAction(label=f"{(today + timedelta(days=i)).month}月{(today + timedelta(days=i)).day}日", text=(today + timedelta(days=i)).strftime("%Y-%m-%d")))
        for i in range(6)
    ])

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

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(403)

    return "OK"

@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    user_id = event.source.user_id
    reply_token = event.reply_token
    text = event.message.text.strip()

    if text == "予約":
        user_state[user_id] = {"step": "waiting_for_date"}
        messaging_api.reply_message(
            ReplyMessageRequest(
                reply_token=reply_token,
                messages=[TextMessage(
                    text="予約したい日付を選んでください",
                    quick_reply=generate_date_quick_reply()
                )]
            )
        )
        return

    if user_state.get(user_id, {}).get("step") == "waiting_for_date":
        user_state[user_id]["date"] = text
        user_state[user_id]["step"] = "waiting_for_time"
        messaging_api.reply_message(
            ReplyMessageRequest(
                reply_token=reply_token,
                messages=[TextMessage(
                    text=f"{text} の時間帯を選んでください",
                    quick_reply=generate_time_quick_reply()
                )]
            )
        )
        return

    if user_state.get(user_id, {}).get("step") == "waiting_for_time":
        selected_date = user_state[user_id]["date"]
        selected_time = text

        messaging_api.reply_message(
            ReplyMessageRequest(
                reply_token=reply_token,
                messages=[TextMessage(text="⏳ 予約処理を開始しました。完了後に通知します。")]
            )
        )

        def background_task():
            try:
                logs, image_path = make_reservation(selected_date, selected_time)

                # 予約完了のメッセージ
                messaging_api.push_message(
                    to=user_id,
                    messages=[TextMessage(text=f"✅ 予約完了しました！\n{selected_date} {selected_time}\n\n{logs}")]
                )

                # スクリーンショットの送信
                with open(image_path, "rb") as f:
                    messaging_api.push_message(
                        to=user_id,
                        messages=[TextMessage(text="📸 スクリーンショットを送信します（仮）※実装では画像送信に変更）")]
                        # 実際には ImageMessage を使用（LINEのMessaging APIでは画像URLを使うかContent APIで送信）
                    )

            except Exception as e:
                messaging_api.push_message(
                    to=user_id,
                    messages=[TextMessage(text=f"❌ 予約に失敗しました。\nエラー: {str(e)}")]
                )

        Thread(target=background_task).start()
        user_state.pop(user_id, None)
        return

    messaging_api.reply_message(
        ReplyMessageRequest(
            reply_token=reply_token,
            messages=[TextMessage(text="「予約」と送って始めてください！")]
        )
    )

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)