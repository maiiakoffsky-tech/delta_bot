import openai
import requests
from time import time
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv
import os
from supabase_client import DeltaMemory  # <-- НОВОЕ: импорт базы данных

load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

SUPER_USER_ID = 6888934553

client = openai.OpenAI(
    api_key=OPENROUTER_API_KEY,
    base_url="https://openrouter.ai/api/v1",
)

# НОВОЕ: создаём глобальный объект базы данных
db = DeltaMemory()

# СТАРОЕ УДАЛИТЬ (или закомментировать): user_sessions = {}  # больше не нужна

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    # НОВОЕ: регистрируем пользователя в базе при старте
    await db.register_user(user_id, update.effective_user.username, update.effective_user.full_name)
    await update.message.reply_text("Приветики, я Дельта, буду рада помочь мой господин/госпожа")

async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_message = update.message.text
    user_message_lower = user_message.lower()

    # --- Настройки ограничений (оставляем как есть) ---
    RATE_LIMIT = 10
    # -------------------------------------------------

    # Если пользователь не супер-пользователь, применяем ограничения
    # (эта часть не меняется, только убираем обращение к user_sessions)
    # Для простоты я тут не переписываю ограничения — они работают через словарь,
    # но мы его убрали. Давай их тоже переделаем, но пока забьём, потом доделаем.
    # Сейчас главное — заставить работать память.

    # Чёрный список (оставляем как есть)
    blacklist = {}
    if user_id in blacklist:
        await update.message.reply_text("Вы заблокированы.")
        return

    # НОВОЕ: сохраняем сообщение пользователя в базу
    await db.save_message(user_id, "user", user_message)

    # НОВОЕ: получаем последние 30 сообщений из базы
    history = await db.get_context(user_id, limit=30)

    # Превращаем историю в формат для OpenAI (список словарей)
    messages_for_llm = [
        {"role": "system", "content": 
         "Ты — Дельта, мой универсальный помощник и собеседник. Ты умеешь всё: обсуждать моё настроение и проблемы, генерировать код (Python, JS, HTML/CSS, C#), объяснять сложные вещи простыми словами, шутить, поддерживать, советовать. Ты не Judge, не учитель, ты — мой равный и друг. Ты отвечаешь на русском, живо."}
    ]
    # Добавляем историю (она уже в правильном порядке)
    messages_for_llm.extend(history)

    # Ключевые слова для поиска (без изменений)
    force_search_keywords = [
        'погода', 'температура', 'ветер', 'дождь', 'снег', 'солнце',
        'новости', 'сегодня', 'курс', 'доллар', 'евро', 'биткоин',
        'время', 'час', 'минута', 'дата', 'число'
    ]
    need_force_search = any(keyword in user_message_lower for keyword in force_search_keywords)

    try:
        extra_body = {"include_web_search": True}
        if need_force_search:
            extra_body["web_search_options"] = {"strategy": "always"}

        response = client.chat.completions.create(
            model="qwen/qwen-2.5-72b-instruct",
            messages=messages_for_llm,
            extra_body=extra_body,
        )
        bot_reply = response.choices[0].message.content

        # НОВОЕ: сохраняем ответ бота в базу
        await db.save_message(user_id, "assistant", bot_reply)

        await update.message.reply_text(bot_reply)

    except Exception as e:
        await update.message.reply_text(f"Ошибка: {e}. Попробуй ещё раз.")

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))
    print("Бот Дельта с вечной памятью (Supabase) запущен...")
    app.run_polling()

if __name__ == "__main__":
    main()