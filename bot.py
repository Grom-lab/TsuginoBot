import os
import requests
from bs4 import BeautifulSoup
from aiogram import Bot, Dispatcher, types
from aiogram.types import InputFile
from aiogram.utils import executor

# Инициализация бота
API_TOKEN = os.getenv("BOT_TOKEN", "7122707567:AAFFWCTyE6XhhFqv1hAe-DsVvBq5dlkfcQ8")
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# URL сайта
BASE_URL = "https://com-x.life"

# Поиск манги/комиксов
def search_comics(query):
    search_url = f"{BASE_URL}/search?q={query}"
    response = requests.get(search_url)
    if response.status_code != 200:
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    results = soup.find_all("div", class_="content-title")
    comics = []

    for result in results:
        title = result.find("a").text.strip()
        link = BASE_URL + result.find("a")["href"]
        comics.append({"title": title, "link": link})

    return comics

# Получение ссылок для скачивания
def get_download_links(comic_url):
    response = requests.get(comic_url)
    if response.status_code != 200:
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    download_links = soup.find_all("a", class_="download-btn")
    links = []

    for link in download_links:
        file_url = BASE_URL + link["href"]
        file_name = link.text.strip()
        links.append({"file_name": file_name, "file_url": file_url})

    return links

# Обработка команды /start
@dp.message_handler(commands=["start"])
async def send_welcome(message: types.Message):
    await message.reply("Привет! Я помогу найти и скачать мангу или комиксы. Введите название для поиска.")

# Обработка текста (поиск)
@dp.message_handler()
async def handle_search(message: types.Message):
    query = message.text
    comics = search_comics(query)

    if not comics:
        await message.reply("Ничего не найдено. Попробуйте другое название.")
        return

    reply_text = "Найдено:\n\n"
    for idx, comic in enumerate(comics, start=1):
        reply_text += f"{idx}. [{comic['title']}]({comic['link']})\n"

    reply_text += "\nВыберите номер для получения ссылок на скачивание."
    await message.reply(reply_text, parse_mode="Markdown")

# Обработка номера выбранного комикса
@dp.message_handler(lambda message: message.text.isdigit())
async def handle_selection(message: types.Message):
    idx = int(message.text) - 1
    comics = search_comics(message.reply_to_message.text)

    if idx < 0 or idx >= len(comics):
        await message.reply("Некорректный выбор. Попробуйте ещё раз.")
        return

    comic = comics[idx]
    download_links = get_download_links(comic["link"])

    if not download_links:
        await message.reply("Ссылки на скачивание не найдены.")
        return

    reply_text = f"Ссылки на скачивание для {comic['title']}:\n\n"
    for link in download_links:
        reply_text += f"- [{link['file_name']}]({link['file_url']})\n"

    await message.reply(reply_text, parse_mode="Markdown")

# Запуск бота
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
