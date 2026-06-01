import os
from supabase import create_client, Client
from datetime import datetime

# Твои данные из Supabase (я их сюда поставил)
SUPABASE_URL = "https://xobebksnoefgdnkjikhf.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InhvYmVia3Nub2VmZ2Rua2ppa2hmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODAzMjYwODksImV4cCI6MjA5NTkwMjA4OX0.dZaFe4ynqzoTIcme6M8HGAQMwr4DUHuvsHv5gZFWAUA"

class DeltaMemory:
    def __init__(self):
        self.supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

    async def register_user(self, telegram_id: int, username: str = None, full_name: str = None):
        """Записывает пользователя в базу, если его там еще нет"""
        try:
            # Проверяем, есть ли уже
            existing = self.supabase.table("users").select("*").eq("telegram_id", telegram_id).execute()
            if not existing.data:
                # Создаем нового
                self.supabase.table("users").insert({
                    "telegram_id": telegram_id,
                    "username": username,
                    "full_name": full_name,
                    "last_active": datetime.now().isoformat()
                }).execute()
            else:
                # Обновляем время активности
                self.supabase.table("users").update({
                    "last_active": datetime.now().isoformat()
                }).eq("telegram_id", telegram_id).execute()
        except Exception as e:
            print(f"Ошибка регистрации: {e}")

    async def save_message(self, telegram_id: int, role: str, content: str):
        """Сохраняет сообщение (user или assistant)"""
        try:
            # Сначала получим внутренний UUID пользователя
            user_res = self.supabase.table("users").select("id").eq("telegram_id", telegram_id).execute()
            if not user_res.data:
                await self.register_user(telegram_id)
                user_res = self.supabase.table("users").select("id").eq("telegram_id", telegram_id).execute()

            user_uuid = user_res.data[0]["id"]
            self.supabase.table("messages").insert({
                "user_id": user_uuid,
                "role": role,
                "content": content
            }).execute()
        except Exception as e:
            print(f"Ошибка сохранения сообщения: {e}")

    async def get_context(self, telegram_id: int, limit: int = 30):
        """Получает последние N сообщений для контекста (от старых к новым)"""
        try:
            # Получаем user_uuid
            user_res = self.supabase.table("users").select("id").eq("telegram_id", telegram_id).execute()
            if not user_res.data:
                return []

            user_uuid = user_res.data[0]["id"]
            # Берем последние `limit` сообщений
            msgs = self.supabase.table("messages") \
                .select("role, content") \
                .eq("user_id", user_uuid) \
                .order("created_at", desc=True) \
                .limit(limit) \
                .execute()

            # Переворачиваем в хронологическом порядке
            context = [{"role": m["role"], "content": m["content"]} for m in reversed(msgs.data)]
            return context
        except Exception as e:
            print(f"Ошибка получения контекста: {e}")
            return []

    async def create_order(self, telegram_id: int, order_details: str):
        """Создает новый заказ/бронь"""
        try:
            user_res = self.supabase.table("users").select("id").eq("telegram_id", telegram_id).execute()
            if user_res.data:
                user_uuid = user_res.data[0]["id"]
                self.supabase.table("orders").insert({
                    "user_id": user_uuid,
                    "order_details": order_details,
                    "status": "pending"
                }).execute()
                return True
            return False
        except Exception as e:
            print(f"Ошибка создания заказа: {e}")
            return False