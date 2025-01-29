import telebot
import requests
from bs4 import BeautifulSoup

TOKEN = '7122707567:AAEYKetCJYpRC7ZCBx7rD2dOs8rNVI2ZiBc'
bot = telebot.TeleBot(TOKEN)

def search_fandom(query):
    url = "https://www.fandom.com/search"
    params = {'query': query, 'resultsLang': 'en'}
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        results = []
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            items = soup.find_all('div', class_='search-result')
            
            for item in items:
                title = item.find('h3', class_='title').text.strip() if item.find('h3', class_='title') else ''
                link = item.find('a', class_='link')['href'] if item.find('a', class_='link') else ''
                desc = item.find('div', class_='snippet').text.strip() if item.find('div', class_='snippet') else ''
                
                if title and link:
                    results.append({
                        'title': title,
                        'url': link,
                        'description': desc
                    })
        return results[:10]  # Ограничиваем 10 результатами
    
    except Exception as e:
        print(f"Error in search: {e}")
        return []

@bot.inline_handler(func=lambda query: True)
def handle_inline(inline_query):
    try:
        query = inline_query.query.strip()
        if not query:
            return
            
        results = []
        search_data = search_fandom(query)
        
        for idx, item in enumerate(search_data):
            results.append(
                telebot.types.InlineQueryResultArticle(
                    id=str(idx),
                    title=item['title'],
                    description=item['description'][:200],  # Ограничение длины описания
                    input_message_content=telebot.types.InputTextMessageContent(
                        message_text=f"<b>{item['title']}</b>\n{item['url']}",
                        parse_mode='HTML'
                    ),
                    thumb_url='https://www.fandom.com/favicon.ico'  # Добавляем иконку
                )
            )
        
        bot.answer_inline_query(inline_query.id, results, cache_time=300)
        
    except Exception as e:
        print(f"Inline error: {e}")

if __name__ == '__main__':
    print("Bot started!")
    bot.infinity_polling()
