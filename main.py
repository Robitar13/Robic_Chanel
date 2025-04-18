import os
import time
import random
import requests
import feedparser
from dotenv import load_dotenv

load_dotenv()

# --- Константы из .env ---
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHANNEL_USERNAME = os.getenv("CHANNEL_USERNAME")
UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY")

# --- Список RSS-источников ---
RSS_FEEDS = [
    # Программирование и IT
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

    # 3D-моделирование
    "https://www.blendernation.com/feed/",
    "https://80.lv/feed/",
    "https://www.cgchannel.com/feed/",
    "https://www.cgtrader.com/blog.rss",
    "https://3ddd.ru/news/rss",

    # Новости и технологии
    "https://www.rbc.ru/rss/"
]


# --- Проверка, публиковалась ли новость ---
def is_posted(link):
    if not os.path.exists("posted_links.txt"):
        return False
    with open("posted_links.txt", "r", encoding="utf-8") as file:
        posted = file.read().splitlines()
    return link in posted


# --- Сохранение новой опубликованной ссылки ---
def mark_as_posted(link):
    with open("posted_links.txt", "a", encoding="utf-8") as file:
        file.write(link + "\n")


# --- Проверка, была ли картинка использована ---
def is_image_used(image_url):
    if not os.path.exists("used_images.txt"):
        return False
    with open("used_images.txt", "r", encoding="utf-8") as file:
        used_images = file.read().splitlines()
    return image_url in used_images


# --- Сохранение использованной картинки ---
def mark_image_as_used(image_url):
    with open("used_images.txt", "a", encoding="utf-8") as file:
        file.write(image_url + "\n")


# --- Фильтр для интересных новостей ---
def is_interesting(news):
    keywords = [
        "ai", "нейросеть", "gpu", "рендер", "unity", "blender", "python",
        "c++", "3d", "game", "code", "open source", "интерфейс", "design"
    ]
    content = (news["title"] + news["summary"]).lower()
    return any(keyword in content for keyword in keywords)


# --- Получение случайной новой новости ---
def get_random_news():
    for _ in range(10):  # Попытки найти неповторную новость
        feed_url = random.choice(RSS_FEEDS)
        feed = feedparser.parse(feed_url)
        entries = [
            entry for entry in feed.entries if entry.title and entry.summary
        ]
        random.shuffle(entries)

        for entry in entries:
            news = {
                "title": entry.title,
                "summary": entry.summary,
                "link": entry.link
            }
            if not is_posted(news["link"]) and is_interesting(news):
                return news
    return None


# --- Генерация текста поста на русском (без "факт 1", "факт 2") ---
def stylize_post(news):
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    prompt = f"""
Сформируй пост для Telegram-канала по этой новости. Пост должен быть на русском языке, структурированным и красиво оформленным с эмодзи и разметкой (HTML-стиль).

Формат:
🚀 <b>[Заголовок]</b>  
📅 [Дата] · [Источник]  

🔹 <i>[Основной факт]</i>  
🔹 <i>[Дополнительная информация]</i>  
🔹 <i>[Последствия/мнение эксперта]</i>  

📌 [1 предложение]  

#Тэг 👇 Обсуждаем в комментариях!  
"""

    data = {
        "model": "openai/gpt-3.5-turbo",
        "messages": [{
            "role": "user",
            "content": prompt
        }]
    }

    response = requests.post("https://openrouter.ai/api/v1/chat/completions",
                             json=data,
                             headers=headers)
    return response.json()['choices'][0]['message']['content']


# --- Получение изображения с Unsplash (исключая использованные) ---
def get_image_url(query):
    url = f"https://api.unsplash.com/search/photos?query={query}&client_id={UNSPLASH_ACCESS_KEY}"
    response = requests.get(url)
    data = response.json()

    if data.get('results'):
        for image in data['results']:
            image_url = image['urls']['regular']
            if not is_image_used(
                    image_url
            ):  # Проверяем, не была ли картинка уже использована
                mark_image_as_used(image_url)
                return image_url
    return None


# --- Публикация в Telegram ---
def post_with_image(text, image_url):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
    payload = {
        "chat_id": CHANNEL_USERNAME,
        "photo": image_url,
        "caption": text,
        "parse_mode": "HTML"
    }
    requests.post(url, data=payload)


# --- Главная функция ---
def main():
    news = get_random_news()
    if news:
        print("📰 Найдена новость:", news["title"])
        post_text = stylize_post(news)
        print("✍️ Сгенерирован пост.")
        query = "3D modeling" if "3d" in news["summary"].lower(
        ) else "programming"
        image_url = get_image_url(query)
        print("📸 Картинка подобрана.")
        if image_url:
            post_with_image(post_text, image_url)
            mark_as_posted(news["link"])
            print("✅ Пост опубликован.")
        else:
            print("⚠️ Картинка не найдена.")


# --- Цикл запуска (каждые 1 час) ---
if __name__ == "__main__":
    main()
