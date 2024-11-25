from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext

# Ваш токен
TOKEN = 'YOUR_BOT_TOKEN'

# Функция для команды /start
def start(update: Update, context: CallbackContext):
    update.message.reply_text('Привет, я твой бот!')

# Главная функция для запуска бота
def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    # Добавляем обработчики команд
    dp.add_handler(CommandHandler("start", start))

    # Запуск бота
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
