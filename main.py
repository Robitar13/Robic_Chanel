import os
import requests
import random
import feedparser
from bs4 import BeautifulSoup
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# 🔐 Переменные окружения
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHANNEL_USERNAME = os.getenv("CHANNEL_USERNAME")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY")

# 📁 Файлы
USED_LINKS_FILE = "used_links.txt"
USED_IMAGES_FILE = "used_images.txt"

# 📡 RSS-источники
RSS_FEEDS = [
    # AI и нейросети
    "https://www.technologyreview.com/topic/artificial-intelligence/feed",
    "https://deepmind.com/blog/feed/basic",
    "https://openai.com/blog/rss/",
    "http://ai.googleblog.com/feeds/posts/default?alt=rss",
    "https://towardsdatascience.com/feed",
    "https://bair.berkeley.edu/blog/feed.xml",
    "https://machinelearningmastery.com/blog/feed/",
    "https://www.aitrends.com/feed/",
    "https://www.datarobot.com/blog/feed/",
    "http://www.kdnuggets.com/feed",

    # Программирование и геймдев
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
    "https://xakep.ru/feed/",
    "https://tproger.ru/rss",

    # Геймдев / Unity / Godot
    "https://80.lv/feed/",
    "https://www.gamedeveloper.com/rss.xml",
    "https://godotengine.org/rss.xml",

    # 3D / CAD
    "https://www.blendernation.com/feed/",
    "https://www.cgchannel.com/feed/",
    "https://www.cgtrader.com/blog.rss",
    "https://3ddd.ru/news/rss",
    "https://blogs.solidworks.com/solidworksblog/feed",
    "https://www.blender.org/feed/",

    # Общее
    "https://www.rbc.ru/rss/"
]


# 🚫 Фильтр политики
def is_political(text):
    keywords = ["украина", "донбасс", "зеленский", "спецоперация", "санкции", "война"]
    return any(word in text.lower() for word in keywords)

# 📜 Проверка и отметка новостей
def is_posted(link):
    if not os.path.exists(USED_LINKS_FILE):
        return False
    with open(USED_LINKS_FILE, "r", encoding="utf-8") as f:
        return link in f.read()

def mark_posted(link):
    with open(USED_LINKS_FILE, "a", encoding="utf-8") as f:
        f.write(link + "\n")

# 🖼 Работа с изображениями
def is_image_used(url):
    if not os.path.exists(USED_IMAGES_FILE):
        return False
    with open(USED_IMAGES_FILE, "r", encoding="utf-8") as f:
        return url in f.read()

def mark_image_used(url):
    with open(USED_IMAGES_FILE, "a", encoding="utf-8") as f:
        f.write(url + "\n")

def get_unsplash_image(query):
    url = f"https://api.unsplash.com/search/photos?query={query}&client_id={UNSPLASH_ACCESS_KEY}"
    res = requests.get(url).json()
    for item in res.get("results", []):
        img = item["urls"]["regular"]
        if not is_image_used(img):
            mark_image_used(img)
            return img
    return None

# 📚 Генерация текста через DeepSeek
def generate_post_text(title, summary, source, link):
    prompt = f"""
Сделай интересный, красиво оформленный пост в Telegram-стиле на русском языке:

🚀 <b>{title}</b>
📅 {datetime.now().strftime('%d.%m.%Y')} · {source}
🔹 Расскажи суть новости — 6–10 предложений, интересно и дружелюбно
💡 Объясни, чем это может быть полезно
🤔 Заверши вопросом
🔗 <a href="{link}">Читать подробнее</a>
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
        r = requests.post("https://api.deepseek.com/v1/chat/completions", headers=headers, json=data)
        result = r.json()

        if 'choices' in result:
            return result['choices'][0]['message']['content']
        else:
            print("⚠️ DeepSeek не вернул поле 'choices':", result)
            return None
    except Exception as e:
        print("⚠️ Ошибка генерации:", e)
        return None

# 📤 Отправка в Telegram
def post_to_telegram(text, image_url=None):
    if not text or len(text.strip()) < 20:
        print("⚠️ Пустой текст. Пропуск публикации.")
        return

    if image_url:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto",
            data={
                "chat_id": CHANNEL_USERNAME,
                "photo": image_url,
                "caption": text,
                "parse_mode": "HTML"
            }
        )
    else:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            data={
                "chat_id": CHANNEL_USERNAME,
                "text": text,
                "parse_mode": "HTML"
            }
        )

# 🧠 Получение новости
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
                "source": source
            }
    return None

# 🚀 Главная функция
def main():
    news = get_news()
    if not news:
        print("😐 Нет подходящих новостей.")
        return

    print("📰 Новость:", news["title"])
    text = generate_post_text(news["title"], news["summary"], news["source"], news["link"])

    if not text or len(text.strip()) < 40:
        print("❌ Слабый текст. Пропускаем.")
        return

    image_url = get_unsplash_image("programming" if "code" in news["summary"].lower() else "technology")
    post_to_telegram(text, image_url)
    mark_posted(news["link"])
    print("✅ Пост опубликован.")

if __name__ == "__main__":
    main()
