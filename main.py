import os
import requests
import random
import feedparser
from datetime import datetime

# Загрузка ключей из переменных окружения (GitHub Secrets)
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHANNEL = os.getenv("CHANNEL_USERNAME")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
UNSPLASH_KEY = os.getenv("UNSPLASH_ACCESS_KEY")

# Логи
USED_LINKS = "used_links.txt"
USED_IMAGES = "used_images.txt"

# RSS-источники
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

    # Программирование
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
    "https://betheprogrammer.blogspot.com/feeds/posts/default",
    "https://www.hackr.io/feed",
    "https://medium.com/feed",
    "https://idiomaticprogrammers.com/rss.xml",
    "https://reactgo.com/feed.xml",
    "https://stackabuse.com/feed",

    # Геймдев и движки
    "https://80.lv/feed/",
    "https://www.gamedeveloper.com/rss.xml",
    "https://godotengine.org/rss.xml",
    "http://gcup.ru/news/rss/",
    "http://gcup.ru/load/rss/",
    "http://gcup.ru/publ/rss/",
    "http://gcup.ru/blog/rss/",
    "http://gcup.ru/dir/rss/",
    "http://gcup.ru/photo/rss/",
    "http://gcup.ru/forum/0-0-0-37",

    # 3D / CAD
    "https://www.blendernation.com/feed/",
    "https://www.cgchannel.com/feed/",
    "https://www.cgtrader.com/blog.rss",
    "https://3ddd.ru/news/rss",
    "https://blogs.solidworks.com/solidworksblog/feed",
    "https://blender.org/feed/",

    # Общее
    "https://www.rbc.ru/rss/"
]

def is_posted(link):
    if not os.path.exists(USED_LINKS):
        return False
    with open(USED_LINKS, "r", encoding="utf-8") as f:
        return link in f.read()

def mark_posted(link):
    with open(USED_LINKS, "a", encoding="utf-8") as f:
        f.write(link + "\n")

def is_image_used(url):
    if not os.path.exists(USED_IMAGES):
        return False
    with open(USED_IMAGES, "r", encoding="utf-8") as f:
        return url in f.read()

def mark_image_used(url):
    with open(USED_IMAGES, "a", encoding="utf-8") as f:
        f.write(url + "\n")

def get_unique_news():
    for _ in range(10):
        feed = feedparser.parse(random.choice(RSS_FEEDS))
        for entry in feed.entries:
            if not is_posted(entry.link):
                return {
                    "title": entry.title,
                    "summary": entry.summary,
                    "link": entry.link,
                    "source": feed.feed.title if hasattr(feed, "feed") else "Источник"
                }
    return None

def stylize_post(news):
    prompt = f"""
Оформи Telegram-пост на русском языке с лёгким юмором, чтобы даже новичок понял. Формат:

🚀 <b>Заголовок</b>
📅 Дата и источник
🔹 1-2 абзаца суть без воды
💡 Почему важно
🤔 Вопрос для обсуждения
🔗 Ссылка

Новость:
Заголовок: {news['title']}
Описание: {news['summary']}
Источник: {news['source']}
Ссылка: {news['link']}
"""

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "openai/gpt-3.5-turbo",
        "messages": [{"role": "user", "content": prompt}]
    }

    r = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)
    try:
        return r.json()['choices'][0]['message']['content']
    except Exception as e:
        print("⚠️ Ошибка генерации:", e)
        return f"<b>{news['title']}</b>\n{news['link']}"

def get_image_url(query):
    url = f"https://api.unsplash.com/search/photos?query={query}&client_id={UNSPLASH_KEY}"
    res = requests.get(url).json()
    for item in res.get("results", []):
        img = item["urls"]["regular"]
        if not is_image_used(img):
            mark_image_used(img)
            return img
    return None

def post_to_telegram(text, image_url):
    url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
    payload = {
        "chat_id": CHANNEL,
        "photo": image_url,
        "caption": text,
        "parse_mode": "HTML"
    }
    requests.post(url, data=payload)

def main():
    news = get_unique_news()
    if not news:
        print("❌ Нет новых новостей")
        return

    print("🗞️ Новость найдена:", news['title'])
    post_text = stylize_post(news)
    keyword = "ai" if "ai" in news["summary"].lower() else "technology"
    image_url = get_image_url(keyword)

    if image_url:
        post_to_telegram(post_text, image_url)
        mark_posted(news["link"])
        print("✅ Пост опубликован!")
    else:
        print("⚠️ Картинка не найдена")

if __name__ == "__main__":
    main()
