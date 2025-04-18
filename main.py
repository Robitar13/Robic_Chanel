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

# --- Списки ---
RSS_FEEDS = [
    # IT и 3D
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

USED_LINKS_FILE = "posted_links.txt"
USED_IMAGES_FILE = "used_images.txt"

EMOJIS = ["🚀", "💡", "🔥", "🧠", "📢", "🔧", "⚙️", "🌐", "📱", "🎮"]
HASHTAGS = ["#Программирование", "#3D", "#AI", "#Новости", "#Графика", "#Технологии"]

# --- Утилиты ---
def is_posted(link):
    if not os.path.exists(USED_LINKS_FILE):
        return False
    with open(USED_LINKS_FILE, "r", encoding="utf-8") as f:
        return link in f.read()

def mark_as_posted(link):
    with open(USED_LINKS_FILE, "a", encoding="utf-8") as f:
        f.write(link + "\n")

def is_image_used(url):
    if not os.path.exists(USED_IMAGES_FILE):
        return False
    with open(USED_IMAGES_FILE, "r", encoding="utf-8") as f:
        return url in f.read()

def mark_image_as_used(url):
    with open(USED_IMAGES_FILE, "a", encoding="utf-8") as f:
        f.write(url + "\n")

def get_random_news():
    for _ in range(10):
        feed = feedparser.parse(random.choice(RSS_FEEDS))
        for entry in feed.entries:
            link = entry.link
            if is_posted(link):
                continue
            return {
                "title": entry.title,
                "summary": entry.summary,
                "link": link,
                "source": feed.feed.title if hasattr(feed, "feed") else "Источник"
            }
    return None

def stylize_post(news):
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    date = datetime.now().strftime("%d.%m.%Y")
    emoji = random.choice(EMOJIS)
    hashtags = " ".join(random.sample(HASHTAGS, 2))

    prompt = f"""
Сделай короткий, оформленный Telegram-пост на русском языке по этой новости.

Структура:
{emoji} <b>{news['title']}</b>  
📅 {date} · {news['source']}

🔹 Основная суть в 2-4 строках (без воды)
🔹 Укажи почему это важно или что поменяется

📌 Заключение или вопрос для обсуждения  
<a href="{news['link']}">Читать полностью</a>

{hashtags} 👇
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
            return "⚠️ Не удалось сгенерировать пост. Попробуйте позже."
    except Exception as e:
        print("⚠️ Ошибка при обработке ответа:", e)
        return "⚠️ Ошибка генерации."

def get_image_url(query):
    url = f"https://api.unsplash.com/search/photos?query={query}&client_id={UNSPLASH_ACCESS_KEY}"
    res = requests.get(url).json()
    for item in res.get("results", []):
        img = item["urls"]["regular"]
        if not is_image_used(img):
            mark_image_as_used(img)
            return img
    return None

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

# --- Основная логика ---
def main():
    news = get_random_news()
    if not news:
        print("😐 Нет новых новостей")
        return
    print("📰 Найдена новость:", news["title"])

    text = stylize_post(news)
    img = get_image_url("3D modeling" if "3d" in news["summary"].lower() else "programming")

    if img:
        post_to_telegram(text, img)
        mark_as_posted(news["link"])
        print("✅ Пост опубликован")
    else:
        print("⚠️ Не удалось подобрать изображение")

# --- Запуск ---
if __name__ == "__main__":
    main()
