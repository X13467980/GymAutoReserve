from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
    QuickReply, QuickReplyButton, MessageAction
)
from main import make_reservation
import os
from dotenv import load_dotenv

# .env 読み込み
load_dotenv()

app = Flask(__name__)

print("SECRET:", os.getenv("LINE_CHANNEL_SECRET"))

line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))

# 状態保存（本番はRedisやDBなど推奨）
user_state = {}

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    text = event.message.text.strip()

    # STEP 1: 日付を選んでもらう
    if text.lower() in ["予約", "start"]:
        msg = TextSendMessage(
            text="予約したい日付を選んでください",
            quick_reply=QuickReply(items=[
                QuickReplyButton(action=MessageAction(label="4月15日", text="2025-04-15")),
                QuickReplyButton(action=MessageAction(label="4月16日", text="2025-04-16")),
                QuickReplyButton(action=MessageAction(label="4月17日", text="2025-04-17")),
            ])
        )
        user_state[user_id] = {"step": "waiting_time"}
        line_bot_api.reply_message(event.reply_token, msg)
        return

    # STEP 2: 時間を選んでもらう
    if user_id in user_state and user_state[user_id].get("step") == "waiting_time" and text.startswith("2025-"):
        user_state[user_id]["date"] = text
        user_state[user_id]["step"] = "reserve"

        msg = TextSendMessage(
            text=f"{text} の予約時間帯を選んでください",
            quick_reply=QuickReply(items=[
                QuickReplyButton(action=MessageAction(label="14:30～15:45", text="14:30～15:45")),
                QuickReplyButton(action=MessageAction(label="16:00～17:15", text="16:00～17:15")),
            ])
        )
        line_bot_api.reply_message(event.reply_token, msg)
        return

    # STEP 3: 時間を受け取って予約実行
    if user_id in user_state and user_state[user_id].get("step") == "reserve":
        date = user_state[user_id].get("date")
        time_slot = text

        try:
            make_reservation(date, time_slot)
            reply = TextSendMessage(text=f"✅ 予約完了しました：{date} {time_slot}")
        except Exception as e:
            reply = TextSendMessage(text=f"❌ 予約に失敗しました：{str(e)}")

        user_state.pop(user_id)
        line_bot_api.reply_message(event.reply_token, reply)
        return

    # それ以外のメッセージ
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text="「予約」と送って始めてください！"))


if __name__ == "__main__":
    app.run(debug=True)