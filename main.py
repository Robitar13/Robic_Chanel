import os
import requests
import random
import feedparser
from bs4 import BeautifulSoup
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# --- Секреты и токены ---
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHANNEL = os.getenv("CHANNEL_USERNAME")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
GEN_API_KEY = os.getenv("GEN_API_KEY")

USED_LINKS_FILE = "used_links.txt"
USED_IMAGES_FILE = "used_images.txt"

# --- RSS источники ---
RSS_FEEDS = [
    "https://habr.com/ru/rss/flows/develop/all/?fl=ru",
    "https://dev.to/feed",
    "https://medium.com/feed/tag/programming",
    "https://www.blendernation.com/feed/",
    "https://towardsdatascience.com/feed",
    "https://godotengine.org/rss.xml"
]

# --- Политический фильтр ---
def is_political(text):
    banned = ["украина", "зеленский", "донбасс", "мобилизация", "санкции", "спецоперация"]
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

# --- Изображения ---
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

# --- Получение новости ---
def get_news():
    for _ in range(10):
        feed = feedparser.parse(random.choice(RSS_FEEDS))
        for entry in feed.entries:
            title = entry.get("title", "")
            summary = entry.get("summary", "")
            link = entry.get("link", "")
            source = feed.feed.get("title", "Источник")

            if is_posted(link) or is_political(title + summary):
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

# --- Генерация текста через DeepSeek ---
def try_deepseek(title, summary, source, link):
    prompt = f"""
Ты — автор Telegram-канала. Составь пост о новости для подписчиков. Пост должен быть интересным, с эмодзи, не менее 8 предложений. Язык — русский. Добавь вопрос в конце.

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
        if not res.content:
            print("⚠️ DeepSeek вернул пустой ответ.")
            return None
        result = res.json()
        return result["choices"][0]["message"]["content"]
    except Exception as e:
        print("⚠️ Ошибка DeepSeek:", e)
        return None

# --- Генерация через Gemini (gen-api.ru) ---
def try_gemini(title, summary, source, link):
    prompt = f"""
Сделай живой, интересный пост на русском языке в Telegram-стиле.

Формат:
🚀 <b>Заголовок</b>  
📅 Дата + источник  
🔹 Кратко и по делу — не менее 8 предложений  
🤔 Вопрос в конце  
<a href="{link}">📖 Читать подробнее</a>

Новость:
Заголовок: {title}
Описание: {summary}
Источник: {source}
"""

    headers = {
        "Authorization": f"Bearer {GEN_API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "gemini-pro",
        "messages": [{"role": "user", "content": prompt}]
    }

    try:
        res = requests.post("https://api.gen-api.ru/api/v1/chat/completions", headers=headers, json=data)
        if not res.content:
            print("⚠️ Gemini вернул пустой ответ.")
            return None
        result = res.json()
        return result["choices"][0]["message"]["content"]
    except Exception as e:
        print("⚠️ Ошибка Gemini:", e)
        return None

# --- Telegram отправка ---
def post_to_telegram(text, image_url=None):
    if image_url:
        requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendPhoto",
            data={
                "chat_id": CHANNEL,
                "photo": image_url,
                "caption": text,
                "parse_mode": "HTML"
            }
        )
    else:
        requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            data={
                "chat_id": CHANNEL,
                "text": text,
                "parse_mode": "HTML"
            }
        )

# --- Основной запуск ---
def main():
    attempts = 0
    while attempts < 5:
        news = get_news()
        if not news:
            print("😐 Нет подходящих новостей.")
            return

        print("📰 Новость:", news["title"])

        post_text = try_deepseek(news["title"], news["summary"], news["source"], news["link"])
        if not post_text:
            print("🔁 Переход к Gemini...")
            post_text = try_gemini(news["title"], news["summary"], news["source"], news["link"])

        if not post_text or len(post_text.split()) < 20:
            print("❌ Текст слишком короткий или не получен. Пробуем другую новость.")
            attempts += 1
            continue

        image_url = get_image_url(news["entry"])
        post_to_telegram(post_text, image_url)
        mark_posted(news["link"])
        print("✅ Пост опубликован.")
        break

    if attempts == 5:
        print("❌ Не удалось сгенерировать достойный пост после 5 попыток.")

if __name__ == "__main__":
    main()
