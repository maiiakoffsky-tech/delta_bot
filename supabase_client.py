import os
from supabase import create_client, Client
from datetime import datetime
import logging
logger = logging.getLogger(__name__)
SUPABASE_URL = "https://xobebksnoefgdnkjikhf.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InhvYmVia3Nub2VmZ2Rua2ppa2hmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODAzMjYwODksImV4cCI6MjA5NTkwMjA4OX0.dZaFe4ynqzoTIcme6M8HGAQMwr4DUHuvsHv5gZFWAUA"

class DeltaMemory:
    def __init__(self):
        self.supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

    async def register_user(self, telegram_id: int, username: str = None, full_name: str = None):
        try:
            existing = self.supabase.table("users").select("*").eq("user_id", telegram_id).execute()
            if not existing.data:
                self.supabase.table("users").insert({
                    "user_id": telegram_id,
                    "user_name": username,
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
        try:
            logger.info(f"💾 Сохраняю: user_id={telegram_id}, role={role}, content={content[:30]}...")
            result = self.supabase.table("messages").insert({
                "user_id": telegram_id,
                "role": role,
                "content": content
            }).execute()
            logger.info(f"✅ Сохранено! ID: {result.data[0]['id'] if result.data else 'неизвестно'}")
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения: {e}")

    async def get_context(self, telegram_id: int, limit: int = 30):
        try:
        # Логируем, что ищем
            logger.info(f"📚 Запрос контекста для user_id={telegram_id}")
        
            msgs = self.supabase.table("messages") \
                .select("role, content") \
                .eq("user_id", telegram_id) \
                .order("created_at", desc=True) \
                .limit(limit) \
                .execute()
        
        # Логируем, сколько нашлось
            logger.info(f"📚 Найдено сообщений: {len(msgs.data)}")
        
            context = [{"role": m["role"], "content": m["content"]} for m in reversed(msgs.data)]
            return context
        except Exception as e:
            logger.error(f"❌ Ошибка получения контекста: {e}")
            return []
        

    async def create_order(self, telegram_id: int, order_details: str):
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