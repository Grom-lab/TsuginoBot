import logging
import os
import requests
import zipfile
from io import BytesIO
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext
from telegram.ext import MessageHandler
from telegram.ext.filters import Text  # Исправлено на правильный импорт

# Настройка логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# Ваш токен бота
TOKEN = '7122707567:AAFFWCTyE6XhhFqv1hAe-DsVvBq5dlkfcQ8'

# Функция для скачивания и упаковки комикса в zip
def download_comic(url):
    # Получаем страницу с комиксом
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    # Ищем ссылки на главы комикса (предположим, что ссылки на Яндекс.Диск находятся в <a> тегах)
    chapters = soup.find_all('a', href=True)
    file_urls = []
    
    for chapter in chapters:
        if 'disk.yandex.ru' in chapter['href']:  # Смотрим, что ссылка ведет на Яндекс.Диск
            file_urls.append(chapter['href'])
    
    # Скачиваем все главы и упаковываем их в zip
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
        for index, file_url in enumerate(file_urls):
            # Скачиваем изображение/главу
            file_data = requests.get(file_url).content
            zip_file.writestr(f"chapter_{index + 1}.jpg", file_data)
    
    zip_buffer.seek(0)
    return zip_buffer

# Функция обработки команды /start
def start(update: Update, context: CallbackContext):
    update.message.reply_text('Привет! Отправь ссылку на комикс, и я отправлю тебе его в формате zip.')

# Функция обработки ссылки на комикс
def handle_comic_link(update: Update, context: CallbackContext):
    url = update.message.text
    try:
        zip_buffer = download_comic(url)
        # Отправляем zip файл пользователю
        update.message.reply_document(document=zip_buffer, filename="comic.zip")
    except Exception as e:
        update.message.reply_text(f"Произошла ошибка: {str(e)}")

# Основная функция
def main():
    updater = Updater(TOKEN)
    dispatcher = updater.dispatcher

    # Обработчик команды /start
    dispatcher.add_handler(CommandHandler('start', start))
    # Обработчик ссылки на комикс
    dispatcher.add_handler(MessageHandler(Text & ~Text.command, handle_comic_link))

    # Запуск бота
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
