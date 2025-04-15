from flask import Flask, request, abort
from linebot.v3 import WebhookHandler
from linebot.v3.messaging import (
    MessagingApi, ReplyMessageRequest, TextMessage,
    Configuration, ApiClient,
    QuickReply, QuickReplyItem, MessageAction,
    PushMessageRequest
)
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.webhooks import MessageEvent, TextMessageContent

from datetime import datetime, timedelta
from threading import Thread
import os
from dotenv import load_dotenv
from main import make_reservation
from supabase_client import get_user_info_from_supabase, register_user_in_supabase

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
    date_items = [
        QuickReplyItem(action=MessageAction(
            label=f"{(today + timedelta(days=i)).month}月{(today + timedelta(days=i)).day}日",
            text=(today + timedelta(days=i)).strftime("%Y-%m-%d")
        )) for i in range(6)
    ]
    date_items.append(
        QuickReplyItem(action=MessageAction(label="キャンセル", text="キャンセル"))
    )
    return QuickReply(items=date_items)


def generate_time_quick_reply():
    times = [
        "09:00～10:00",
        "10:00～11:00",
        "13:15～14:30",
        "14:30～15:45",
        "15:45～17:00",
        "17:00～18:15",
        "18:15～19:30",
        "19:30～20:45"
    ]
    time_items = [
        QuickReplyItem(action=MessageAction(label=t, text=t)) for t in times
    ]
    time_items.append(
        QuickReplyItem(action=MessageAction(label="キャンセル", text="キャンセル"))
    )
    return QuickReply(items=time_items)


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

    state = user_state.get(user_id, {})

    if state.get("step") == "register_name":
        state["name"] = text
        state["step"] = "register_email"
        messaging_api.reply_message(ReplyMessageRequest(
            reply_token=reply_token,
            messages=[TextMessage(text="📧 メールアドレスを入力してください。")]
        ))
        return

    if state.get("step") == "register_email":
        state["email"] = text
        state["step"] = "register_permit"
        messaging_api.reply_message(ReplyMessageRequest(
            reply_token=reply_token,
            messages=[TextMessage(text="🪪 学籍番号を入力してください。")]
        ))
        return

    if state.get("step") == "register_permit":
        state["permit"] = text
        state["step"] = "register_faculty"
        messaging_api.reply_message(ReplyMessageRequest(
            reply_token=reply_token,
            messages=[TextMessage(text="🏫 学部名を入力してください。")]
        ))
        return

    if state.get("step") == "register_faculty":
        state["faculty"] = text

        try:
            register_user_in_supabase(
                line_user_id=user_id,
                name=state["name"],
                email=state["email"],
                permit=state["permit"],
                faculty=state["faculty"]
            )
            reply_text = "✅ 登録が完了しました！"
        except Exception as e:
            reply_text = f"❌ 登録に失敗しました: {e}"

        messaging_api.reply_message(ReplyMessageRequest(
            reply_token=reply_token,
            messages=[TextMessage(text=reply_text)]
        ))
        user_state.pop(user_id, None)
        return

    if text == "登録":
        user_state[user_id] = {"step": "register_name"}
        messaging_api.reply_message(ReplyMessageRequest(
            reply_token=reply_token,
            messages=[TextMessage(text="📝 名前を入力してください。")]
        ))
        return

    if text == "キャンセル":
        user_state.pop(user_id, None)
        messaging_api.reply_message(
            ReplyMessageRequest(
                reply_token=reply_token,
                messages=[TextMessage(text="❌ 操作をキャンセルしました。")]
            )
        )
        return

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

    if state.get("step") == "waiting_for_date":
        state["date"] = text
        state["step"] = "waiting_for_time"
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

    if state.get("step") == "waiting_for_time":
        selected_date = state["date"]
        selected_time = text

        messaging_api.reply_message(
            ReplyMessageRequest(
                reply_token=reply_token,
                messages=[TextMessage(text="⏳ 予約処理を開始しました。完了後に通知します。")]
            )
        )

        def background_task():
            try:
                user_info = get_user_info_from_supabase(user_id)
                logs, _ = make_reservation(selected_date, selected_time, user_info)
                messaging_api.push_message(
                    PushMessageRequest(
                        to=user_id,
                        messages=[
                            TextMessage(text=f"✅ 予約完了しました！\n{selected_date} {selected_time}"),
                            TextMessage(text=logs)
                        ]
                    )
                )
            except Exception as e:
                messaging_api.push_message(
                    PushMessageRequest(
                        to=user_id,
                        messages=[TextMessage(text=f"❌ 予約に失敗しました。\nエラー: {str(e)}")]
                    )
                )

        Thread(target=background_task).start()
        user_state.pop(user_id, None)
        return

    messaging_api.reply_message(
        ReplyMessageRequest(
            reply_token=reply_token,
            messages=[TextMessage(text="「登録」または「予約」と送って始めてください！")]
        )
    )


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
