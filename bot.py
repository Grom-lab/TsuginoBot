import os
import requests
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext
from zipfile import ZipFile

# Токен бота (замените на ваш токен)
TOKEN = "7122707567:AAFFWCTyE6XhhFqv1hAe-DsVvBq5dlkfcQ8"

# Функция для скачивания файлов с Яндекс.Диска
def download_from_yandex(disk_url, download_folder):
    # Загружаем страницу и получаем ссылку на файл
    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(disk_url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Извлекаем ссылку для скачивания
    download_link = soup.find('a', {'class': 'b-link'})['href']
    
    # Скачиваем файл по найденной ссылке
    response = requests.get(download_link, stream=True)
    filename = os.path.join(download_folder, disk_url.split('/')[-1] + '.zip')
    
    with open(filename, 'wb') as file:
        for chunk in response.iter_content(1024):
            file.write(chunk)
    
    return filename

# Функция для создания архива
def create_zip(comic_urls, zip_filename):
    with ZipFile(zip_filename, 'w') as zipf:
        for url in comic_urls:
            file_path = download_from_yandex(url, 'downloads')
            zipf.write(file_path, os.path.basename(file_path))

# Обработчик команды /start
def start(update: Update, context: CallbackContext):
    update.message.reply_text('Привет! Отправь ссылку на комикс с comicsdb.ru.')

# Обработчик команды /download
def download_comic(update: Update, context: CallbackContext):
    try:
        comic_url = context.args[0]  # Получаем ссылку на комикс из сообщения
        comic_urls = get_comic_links(comic_url)  # Функция для извлечения ссылок глав с комиксом
        
        # Создание архива с главами
        zip_filename = '/tmp/comic.zip'  # Временно сохраняем zip на сервере
        create_zip(comic_urls, zip_filename)
        
        # Отправляем архив пользователю
        with open(zip_filename, 'rb') as f:
            update.message.reply_document(f)

    except Exception as e:
        update.message.reply_text(f"Ошибка: {str(e)}")

# Функция для извлечения ссылок глав
def get_comic_links(comic_url):
    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(comic_url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Найдем все ссылки на главы
    chapter_links = [a['href'] for a in soup.find_all('a', {'class': 'chapter-link'})]
    return chapter_links

def main():
    # Настройка и запуск бота
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("download", download_comic))
    
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
