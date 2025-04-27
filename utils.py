import os
import random
import feedparser
import requests
from datetime import datetime

# --- RSS-источники ---
RSS_FEEDS = [
    "https://www.blendernation.com/feed/",
    "https://www.ixbt.com/export/news.rss",
    "https://kod.ru/feed",
    "https://www.cnews.ru/inc/rss/news.xml",
    "https://stackoverflow.blog/feed/",
    "https://dev.to/feed",
    "https://medium.com/feed/tag/programming",
    "https://www.gamedeveloper.com/rss.xml",
    "https://thenextweb.com/feed",
    "https://www.rbc.ru/rss/",
    "https://gcup.ru/news/rss/"
]

USED_LINKS_FILE = "used_links.txt"
USED_IMAGES_FILE = "used_images.txt"

EMOJIS = ["🚀", "💡", "🔥", "🧠", "📢", "🎮", "🔍", "🖥️", "🎨", "⚙️"]
HASHTAGS = ["#IT", "#Технологии", "#Новости", "#Разработка", "#3D", "#AI", "#Игры"]

# --- Парсинг новостей ---
def is_posted(link):
    if not os.path.exists(USED_LINKS_FILE):
        return False
    with open(USED_LINKS_FILE, "r", encoding="utf-8") as f:
        return link in f.read()
def is_political(text: str) -> bool:
    political_keywords = [
        "украина", "україна", "ukraine", "zelensky", "зеленский", "киев", "київ",
        "донбасс", "донецк", "луганск", "россия", "russia", "политика", "война",
        "военные", "конфликт", "санкции", "путин", "мобилизация", "спецоперация"
    ]
    text_lower = text.lower()
    return any(word in text_lower for word in political_keywords)



def mark_as_posted(link):
    with open(USED_LINKS_FILE, "a", encoding="utf-8") as f:
        f.write(link + "\n")

def get_new_news():
    for _ in range(10):
        feed_url = random.choice(RSS_FEEDS)
        feed = feedparser.parse(feed_url)
        if feed.entries:
            random.shuffle(feed.entries)
            for entry in feed.entries:
                link = entry.link
                if not is_posted(link):
                    title = entry.title
                    summary = entry.summary if 'summary' in entry else ''
                    published = entry.published if 'published' in entry else ''
                    source = feed.feed.title if 'title' in feed.feed else 'Источник'
                    mark_as_posted(link)
                    return title, summary, link, published, source
    return None

# --- Форматирование поста ---
def format_post(title, summary, link, published, source):
    emoji = random.choice(EMOJIS)
    date = datetime.now().strftime("%d.%m.%Y")
    hashtags = " ".join(random.sample(HASHTAGS, 2))

    short_summary = summary.split(".")[0] + "." if "." in summary else summary

    post = f"""{emoji} <b>{title}</b>
📅 {date} · {source}

🔹 {short_summary}
🔹 Почему это важно? Узнайте в статье!

<a href="{link}">📖 Читать статью</a>

{hashtags}
"""
    return post

# --- Генерация изображения ---
def is_image_used(url):
    if not os.path.exists(USED_IMAGES_FILE):
        return False
    with open(USED_IMAGES_FILE, "r", encoding="utf-8") as f:
        return url in f.read()

def mark_image_as_used(url):
    with open(USED_IMAGES_FILE, "a", encoding="utf-8") as f:
        f.write(url + "\n")

def generate_image(prompt):
    api_key = os.getenv("GENAPI_API_KEY")

    url = "https://gen-api.ru/model/dalle-3/api"
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    payload = {
        "prompt": prompt,
        "quality": "standard",
        "n": 1,
        "size": "1024x1024"
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        result = response.json()
        if "data" in result and result["data"]:
            img_url = result["data"][0]["url"]
            if not is_image_used(img_url):
                mark_image_as_used(img_url)
                return img_url
        else:
            print("⚠️ Картинка не сгенерирована:", result)
            return None
    except Exception as e:
        print("❌ Ошибка генерации изображения:", e)
        return None
