import os
import random
import requests
import feedparser
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# --- Переменные окружения ---
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHANNEL_USERNAME = os.getenv("CHANNEL_USERNAME")
UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY")

# --- RSS источники ---
RSS_FEEDS = [
    "https://habr.com/ru/rss/flows/develop/all/?fl=ru",
    "https://www.ixbt.com/export/news.rss",
    "https://kod.ru/feed",
    "https://www.cnews.ru/inc/rss/news.xml",
    "https://stackoverflow.blog/feed/",
    "https://dev.to/feed",
    "https://medium.com/feed/tag/programming",
    "https://techcrunch.com/feed/",
    "https://www.digitaltrends.com/feed/",
    "https://thenextweb.com/feed",
    "https://www.pcworld.com/index.rss",
    "https://hnrss.org/frontpage",
    "https://www.theverge.com/rss/index.xml",
    "https://feeds.arstechnica.com/arstechnica/index",
    "https://www.blendernation.com/feed/",
    "https://80.lv/feed/",
    "https://www.cgchannel.com/feed/",
    "https://www.cgtrader.com/blog.rss",
    "https://3ddd.ru/news/rss",
    "https://www.rbc.ru/rss/"
]

# --- Эмодзи и хештеги ---
EMOJIS = ["🚀", "💡", "🔥", "🧠", "📢", "🔧", "⚙️", "🌐", "📱", "🎮"]
HASHTAGS = ["#Программирование", "#3D", "#AI", "#Новости", "#Графика", "#Технологии"]

# --- Получение свежей новости ---
def get_random_news():
    for _ in range(10):
        feed = feedparser.parse(random.choice(RSS_FEEDS))
        for entry in feed.entries:
            return {
                "title": entry.title,
                "summary": entry.summary,
                "link": entry.link,
                "source": feed.feed.title if hasattr(feed, "feed") else "Источник"
            }
    return None

# --- Генерация текста поста на русском ---
def stylize_post(news):
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    emoji = random.choice(EMOJIS)
    hashtags = " ".join(random.sample(HASHTAGS, 2))

    prompt = f"""
Ты — Telegram-бот, публикующий новости на русском языке.
Сделай короткий, оформленный пост в стиле канала для гиков.

<b>Важно:</b>
– Пиши строго на русском языке.  
– Не используй английские слова и термины, кроме брендовых.  
– Форматируй текст: эмодзи, переносы строк, заголовок, дата, вывод.  
– Не используй слово "факт", пиши как живой человек.  
– Обязательно добавь хештеги и ссылку.

Исходные данные:
Заголовок: {news['title']}
Описание: {news['summary']}
Ссылка: {news['link']}
Источник: {news['source']}
Дата: {datetime.now().strftime("%d.%m.%Y")}

Ответ должен быть отформатирован в HTML для Telegram.
"""

    data = {
        "model": "openai/gpt-3.5-turbo",
        "messages": [{"role": "user", "content": prompt}]
    }

    res = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)
    try:
        result = res.json()
        if "choices" in result:
            return result['choices'][0]['message']['content']
        else:
            print("⚠️ Ответ без choices:", result)
            return "⚠️ Не удалось сгенерировать пост."
    except Exception as e:
        print("⚠️ Ошибка при генерации:", e)
        return "⚠️ Ошибка при обработке запроса."

# --- Получение случайной картинки ---
def get_image_url(query):
    search_terms = [
        query, f"{query} concept", f"{query} art", f"{query} idea",
        f"{query} tech", f"{query} future", f"{query} workspace"
    ]
    random.shuffle(search_terms)

    for term in search_terms:
        url = f"https://api.unsplash.com/search/photos?query={term}&client_id={UNSPLASH_ACCESS_KEY}"
        res = requests.get(url).json()
        results = res.get("results", [])
        if results:
            img = random.choice(results)["urls"]["regular"]
            return img
    return None

# --- Публикация в Telegram ---
def post_to_telegram(text, img_url):
    requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto",
        data={
            "chat_id": CHANNEL_USERNAME,
            "photo": img_url,
            "caption": text,
            "parse_mode": "HTML"
        }
    )

# --- Главная функция ---
def main():
    news = get_random_news()
    if not news:
        print("😐 Новостей не найдено.")
        return

    print("📰 Новость:", news["title"])
    text = stylize_post(news)
    query = "3D modeling" if "3d" in news["summary"].lower() else "programming"
    img = get_image_url(query)

    if img:
        post_to_telegram(text, img)
        print("✅ Пост опубликован.")
    else:
        print("⚠️ Картинка не найдена.")

# --- Запуск ---
if __name__ == "__main__":
    main()
