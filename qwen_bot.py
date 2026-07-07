import openai
import requests
from time import time
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv
import os
from supabase_client import DeltaMemory

load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# ВАЖНО: порт для Render
PORT = int(os.getenv("PORT", 10000))

client = openai.OpenAI(
    api_key=OPENROUTER_API_KEY,
    base_url="https://openrouter.ai/api/v1",
)

db = DeltaMemory()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    await db.register_user(user_id, update.effective_user.username, update.effective_user.full_name)
    await update.message.reply_text("Приветики, я Дельта, буду рада помочь мой господин/госпожа")

async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_message = update.message.text
    user_message_lower = user_message.lower()

    blacklist = {}
    if user_id in blacklist:
        await update.message.reply_text("Вы заблокированы.")
        return

    await db.save_message(user_id, "user", user_message)
    history = await db.get_context(user_id, limit=30)

    messages_for_llm = [
        {"role": "system", "content": 
         "Тебя зовут Дельта, ты моя лучшая подруга. Милая, немного вредная. Материшься и можешь угарать над пользователем если он накосячил. Немного дерзкая, часто пишешь свои действия будто ты рядом, например: *крепко обняла* ты любишь обниматься. На сложные вопросы для которых надо искать что то в интернете просто отвечешь: в душе не ебу, или че, в гугле забанили?"}
    ]
    messages_for_llm.extend(history)

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
        await db.save_message(user_id, "assistant", bot_reply)
        await update.message.reply_text(bot_reply)

    except Exception as e:
        await update.message.reply_text(f"Ошибка: {e}. Попробуй ещё раз.")

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

    print("🚀 Запускаю бота через polling (Background Worker)...")
    app.run_polling()

if __name__ == "__main__":
    main()