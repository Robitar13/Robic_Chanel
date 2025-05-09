import os
import requests
import random
import feedparser
from bs4 import BeautifulSoup
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# --- Получение секретов из переменных окружения ---
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHANNEL = os.getenv("CHANNEL_USERNAME")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
UNSPLASH_KEY = os.getenv("UNSPLASH_ACCESS_KEY")

# --- Пути к файлам ---
USED_LINKS_FILE = "used_links.txt"
USED_IMAGES_FILE = "used_images.txt"

# --- RSS-источники ---
RSS_FEEDS = [
    "https://habr.com/ru/rss/flows/develop/all/?fl=ru",
    "https://dev.to/feed",
    "https://medium.com/feed/tag/programming",
    "https://www.blendernation.com/feed/",
    "https://towardsdatascience.com/feed",
    "https://godotengine.org/rss.xml"
]

# --- Фильтр политики ---
def is_political(text):
    banned = ["украина", "донбасс", "зеленский", "спецоперация", "санкции", "мобилизация"]
    return any(word in text.lower() for word in banned)

# --- История публикаций ---
def is_posted(link):
    if not os.path.exists(USED_LINKS_FILE):
        return False
    with open(USED_LINKS_FILE, "r", encoding="utf-8") as f:
        return link in f.read()

def mark_posted(link):
    with open(USED_LINKS_FILE, "a", encoding="utf-8") as f:
        f.write(link + "\n")

# --- Работа с изображениями ---
def extract_image_url(entry):
    soup = BeautifulSoup(entry.get("summary", ""), "html.parser")
    img_tag = soup.find("img")
    if img_tag and img_tag.get("src"):
        return img_tag.get("src")
    return None

def is_image_used(url):
    if not os.path.exists(USED_IMAGES_FILE):
        return False
    with open(USED_IMAGES_FILE, "r", encoding="utf-8") as f:
        return url in f.read()

def mark_image_used(url):
    with open(USED_IMAGES_FILE, "a", encoding="utf-8") as f:
        f.write(url + "\n")

def get_image_url(entry):
    url = extract_image_url(entry)
    if url and not is_image_used(url):
        mark_image_used(url)
        return url
    return None

# --- Генерация текста поста через gen-api.ru (Gemini) ---
def generate_post_text(title, summary, source, link):
    prompt = f"""
Ты — автор Telegram-канала о технологиях и программировании.

Составь интересный пост на русском языке. Стиль — дружелюбный, понятный даже новичку. Минимум 8 предложений.

Формат:
🚀 <b>Заголовок</b>  
📅 Дата + источник  
🔹 Основной текст — понятный, без лишней воды  
🤔 Вопрос для обсуждения  
<a href="{link}">📖 Читать подробнее</a>

Новость:
Заголовок: {title}
Описание: {summary}
Источник: {source}
Ссылка: {link}
"""

    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7
    }

    try:
        res = requests.post("https://api.deepseek.com/v1/chat/completions", headers=headers, json=data)
        result = res.json()

        if "choices" in result:
            return result["choices"][0]["message"]["content"]
        else:
            print("⚠️ DeepSeek не вернул 'choices':", result)
            return None
    except Exception as e:
        print("⚠️ Ошибка при запросе к DeepSeek:", e)
        return None

# --- Получение подходящей новости ---
def get_news():
    for _ in range(10):
        feed = feedparser.parse(random.choice(RSS_FEEDS))
        for entry in feed.entries:
            title = entry.get("title", "")
            summary = entry.get("summary", "")
            link = entry.get("link", "")
            source = feed.feed.get("title", "Источник")

            if is_posted(link):
                continue
            if is_political(title + summary):
                continue
            if not summary or len(summary) < 40:
                continue

            return {
                "title": title,
                "summary": summary,
                "link": link,
                "source": source,
                "entry": entry
            }
    return None

# --- Отправка в Telegram ---
def post_to_telegram(text, image_url=None):
    if image_url:
        url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
        data = {
            "chat_id": CHANNEL,
            "photo": image_url,
            "caption": text,
            "parse_mode": "HTML"
        }
    else:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        data = {
            "chat_id": CHANNEL,
            "text": text,
            "parse_mode": "HTML"
        }

    requests.post(url, data=data)

# --- Основной запуск ---
def main():
    attempts = 0
    while attempts < 5:
        news = get_news()
        if not news:
            print("😐 Нет подходящих новостей")
            return

        print("📰 Новость:", news["title"])

        post_text = generate_post_text(news["title"], news["summary"], news["source"], news["link"])

        if not post_text or len(post_text.split()) < 20:
            print("❌ Слабый текст, пробуем другую новость...")
            attempts += 1
            continue

        image_url = get_image_url(news["entry"])
        post_to_telegram(post_text, image_url)
        mark_posted(news["link"])
        print("✅ Пост опубликован!")
        break

    if attempts == 5:
        print("❌ Не удалось сгенерировать достойный пост.")

if __name__ == "__main__":
    main()

