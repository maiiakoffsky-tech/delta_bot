import os
from supabase import create_client, Client
from datetime import datetime

# ТВОИ ДАННЫЕ (исправлено)
SUPABASE_URL = "https://xobebksnoefgdnkjikhf.supabase.co"
SUPABASE_KEY = "sb_publishable_rooLf_gMcsteR_MYm-A5aA_OO90qR2T"  # <-- НОВЫЙ КЛЮЧ

class DeltaMemory:
    def __init__(self):
        self.supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

    async def register_user(self, telegram_id: int, username: str = None, full_name: str = None):
        """Записывает пользователя в базу, если его там еще нет"""
        try:
            existing = self.supabase.table("users").select("*").eq("user_id", telegram_id).execute()
            if not existing.data:
                self.supabase.table("users").insert({
                    "user_id": telegram_id,
                    "username": username,
                    "full_name": full_name,
                    "last_active": datetime.now().isoformat()
                }).execute()
                print(f"✅ Новый пользователь: {telegram_id}")
            else:
                self.supabase.table("users").update({
                    "last_active": datetime.now().isoformat()
                }).eq("user_id", telegram_id).execute()
        except Exception as e:
            print(f"❌ Ошибка регистрации: {e}")

    async def save_message(self, telegram_id: int, role: str, content: str):
        """Сохраняет сообщение (user или assistant)"""
        try:
            self.supabase.table("messages").insert({
                "user_id": telegram_id,
                "role": role,
                "content": content
            }).execute()
        except Exception as e:
            print(f"❌ Ошибка сохранения сообщения: {e}")

    async def get_context(self, telegram_id: int, limit: int = 30):
        """Получает последние N сообщений для контекста"""
        try:
            msgs = self.supabase.table("messages") \
                .select("role, content") \
                .eq("user_id", telegram_id) \
                .order("created_at", desc=True) \
                .limit(limit) \
                .execute()

            context = [{"role": m["role"], "content": m["content"]} for m in reversed(msgs.data)]
            return context
        except Exception as e:
            print(f"❌ Ошибка получения контекста: {e}")
            return []

    async def create_order(self, telegram_id: int, order_details: str):
        """Создает новый заказ/бронь"""
        try:
            self.supabase.table("orders").insert({
                "user_id": telegram_id,
                "order_details": order_details,
                "status": "pending"
            }).execute()
            return True
        except Exception as e:
            print(f"❌ Ошибка создания заказа: {e}")
            return False