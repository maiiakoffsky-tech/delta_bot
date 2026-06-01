from threading import Thread
from flask import Flask
import qwen_bot  # твой основной файл с ботом

app = Flask(__name__)

@app.route('/')
def home():
    return "Бот Дельта работает!"

def run_bot():
    qwen_bot.main()  # запускаем твоего бота

if __name__ == "__main__":
    # Запускаем бота в отдельном потоке
    bot_thread = Thread(target=run_bot)
    bot_thread.start()
    # Запускаем веб-сервер Flask
    app.run(host='0.0.0.0', port=8080)