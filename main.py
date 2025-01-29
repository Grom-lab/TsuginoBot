import os
import telebot
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv('TELEGRAM_TOKEN')
bot = telebot.TeleBot(TOKEN)

def search_fandom(query):
    url = "https://www.fandom.com/search"
    params = {'query': query, 'resultsLang': 'en'}
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
    response = requests.get(url, params=params, headers=headers)
    results = []
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        items = soup.find_all('div', class_='search-result')
        for item in items:
            title_elem = item.find('h3', class_='title')
            link_elem = item.find('a', class_='link')
            snippet_elem = item.find('div', class_='snippet')
            if title_elem and link_elem:
                title = title_elem.text.strip()
                link = link_elem['href']
                desc = snippet_elem.text.strip() if snippet_elem else ''
                results.append({'title': title, 'url': link, 'description': desc})
    return results

@bot.inline_handler(func=lambda query: True)
def inline_query(inline_query):
    query = inline_query.query
    if not query:
        return
    search_results = search_fandom(query)[:10]
    results = []
    for idx, res in enumerate(search_results):
        results.append(
            telebot.types.InlineQueryResultArticle(
                id=str(idx),
                title=res['title'],
                description=res['description'],
                input_message_content=telebot.types.InputTextMessageContent(
                    message_text=f"<b>{res['title']}</b>\n{res['url']}",
                    parse_mode='HTML'
                )
            )
        )
    try:
        bot.answer_inline_query(inline_query.id, results)
    except Exception as e:
        print(e)

if __name__ == '__main__':
    bot.infinity_polling()
