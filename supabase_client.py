from supabase import create_client, Client
import os
from dotenv import load_dotenv
import traceback

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_user_info_from_supabase(line_user_id: str):
    response = supabase.table("users").select("*").eq("line_user_id", line_user_id).execute()

    if not response.data or len(response.data) == 0:
        raise Exception("ユーザー情報が見つかりませんでした")

    user = response.data[0]
    return {
        "name": user["name"],
        "email": user["email"],
        "permit": user["permit"],
        "faculty": user["faculty"]
    }


def register_user_in_supabase(line_user_id, name, email, permit, faculty):
    try:
        user_data = {
            "line_user_id": line_user_id,
            "name": name,
            "email": email,
            "permit": permit,
            "faculty": faculty
        }

        print("📦 登録または更新するデータ:", user_data)

        # 🟡 line_user_id をキーに upsert（登録 or 更新）
        response = supabase.table("users").upsert(
            [user_data], on_conflict="line_user_id"
        ).execute()

        print("✅ Supabase response:", response)
        return response

    except Exception as e:
        print("❌ 登録時にエラー:", str(e))
        print("🧵 トレース:", traceback.format_exc())
        if hasattr(e, 'args') and e.args:
            raise Exception(f"登録中に例外が発生しました: {e.args[0]}")
        raise