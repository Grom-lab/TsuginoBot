import requests
from bs4 import BeautifulSoup
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils import executor

# Токен бота
API_TOKEN = "7122707567:AAFFWCTyE6XhhFqv1hAe-DsVvBq5dlkfcQ8"
BASE_URL = "https://com-x.life"

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Клавиатура для главного меню
menu_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
menu_keyboard.add(KeyboardButton("🔍 Поиск по названию"))
menu_keyboard.add(KeyboardButton("🌐 Поиск по ссылке"))


# Поиск комиксов по названию
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


# Получение ссылок для скачивания с конкретной страницы
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


# Переменная для отслеживания режима работы
user_mode = {}


# Обработка команды /start
@dp.message_handler(commands=["start"])
async def send_welcome(message: types.Message):
    user_mode[message.from_user.id] = None
    await message.reply(
        "Добро пожаловать! Выберите, что вы хотите сделать:",
        reply_markup=menu_keyboard
    )


# Обработка выбора из меню
@dp.message_handler(lambda message: message.text in ["🔍 Поиск по названию", "🌐 Поиск по ссылке"])
async def handle_menu_selection(message: types.Message):
    if message.text == "🔍 Поиск по названию":
        user_mode[message.from_user.id] = "search_by_name"
        await message.reply("Введите название для поиска:")
    elif message.text == "🌐 Поиск по ссылке":
        user_mode[message.from_user.id] = "search_by_link"
        await message.reply("Введите ссылку на комикс/мангу:")


# Обработка текста в зависимости от режима
@dp.message_handler()
async def handle_input(message: types.Message):
    mode = user_mode.get(message.from_user.id)

    # Если выбран поиск по названию
    if mode == "search_by_name":
        query = message.text
        comics = search_comics(query)
        if not comics:
            await message.reply("Ничего не найдено. Попробуйте другое название.")
            return

        reply_text = "Найдено:\n\n"
        for idx, comic in enumerate(comics, start=1):
            reply_text += f"{idx}. [{comic['title']}]({comic['link']})\n"

        reply_text += "\nВведите номер для получения ссылок на скачивание."
        await message.reply(reply_text, parse_mode="Markdown")

    # Если выбран поиск по ссылке
    elif mode == "search_by_link":
        url = message.text
        if not url.startswith(BASE_URL):
            await message.reply("Некорректная ссылка. Убедитесь, что вы ввели ссылку с сайта com-x.life.")
            return

        download_links = get_download_links(url)
        if not download_links:
            await message.reply("Ссылки на скачивание не найдены.")
            return

        reply_text = "Ссылки на скачивание:\n\n"
        for link in download_links:
            reply_text += f"- [{link['file_name']}]({link['file_url']})\n"

        await message.reply(reply_text, parse_mode="Markdown")

    else:
        await message.reply("Выберите действие в главном меню.")


# Запуск бота
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
