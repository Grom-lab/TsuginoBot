from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext

import os

# Получаем токен из переменной окружения
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Функция для обработки команды /start
def start(update: Update, context: CallbackContext):
    # Создаем кнопки
    keyboard = [
        [InlineKeyboardButton("Кнопка 1", callback_data='button1')],
        [InlineKeyboardButton("Кнопка 2", callback_data='button2')],
        [InlineKeyboardButton("Кнопка 3", callback_data='button3')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    # Отправляем сообщение с кнопками
    update.message.reply_text("Привет! Выберите одну из кнопок:", reply_markup=reply_markup)

# Функция для обработки нажатий на кнопки
def button_click(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    # Проверяем, на какую кнопку нажали, и отправляем ответ
    if query.data == 'button1':
        query.edit_message_text(text="Вы нажали Кнопка 1!")
    elif query.data == 'button2':
        query.edit_message_text(text="Вы нажали Кнопка 2!")
    elif query.data == 'button3':
        query.edit_message_text(text="Вы нажали Кнопка 3!")

# Главная функция для запуска бота
def main():
    # Создаем объект Updater
    updater = Updater(TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    # Обработчики команд
    dispatcher.add_handler(CommandHandler("start", start))

    # Обработчик нажатий на кнопки
    dispatcher.add_handler(CallbackQueryHandler(button_click))

    # Запускаем бота
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
