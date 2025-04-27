import os
import requests
import random
import feedparser
from datetime import datetime
from bs4 import BeautifulSoup

# --- Получение секретов из переменных окружения ---
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHANNEL = os.getenv("CHANNEL_USERNAME")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
UNSPLASH_KEY = os.getenv("UNSPLASH_ACCESS_KEY")

# --- Пути к файлам ---
USED_LINKS_FILE = "used_links.txt"
USED_IMAGES_FILE = "used_images.txt"

# --- Политический фильтр ---
def is_political(text: str) -> bool:
    political_keywords = [
        "украина", "україна", "ukraine", "zelensky", "зеленский", "киев", "київ",
        "донбасс", "донецк", "луганск", "война",
        "военные", "конфликт", "санкции", "мобилизация", "спецоперация"
    ]
    text_lower = text.lower()
    return any(word in text_lower for word in political_keywords)

# --- RSS источники ---
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

# --- Утилиты: ссылки ---
def is_posted(link):
    if not os.path.exists(USED_LINKS_FILE):
        return False
    with open(USED_LINKS_FILE, "r", encoding="utf-8") as f:
        return link in f.read()

def mark_posted(link):
    with open(USED_LINKS_FILE, "a", encoding="utf-8") as f:
        f.write(link + "\n")

# --- Утилиты: изображения ---
def is_image_used(url):
    if not os.path.exists(USED_IMAGES_FILE):
        return False
    with open(USED_IMAGES_FILE, "r", encoding="utf-8") as f:
        return url in f.read()

def mark_image_used(url):
    with open(USED_IMAGES_FILE, "a", encoding="utf-8") as f:
        f.write(url + "\n")

def extract_image_url(entry):
    soup = BeautifulSoup(entry.get("summary", ""), "html.parser")
    img_tag = soup.find("img")
    if img_tag and img_tag.get("src"):
        return img_tag.get("src")
    return None

def get_image_url(entry):
    url = extract_image_url(entry)
    if url and not is_image_used(url):
        mark_image_used(url)
        return url
    return None

# --- Получение новости ---
def get_unique_news():
    for _ in range(10):
        feed = feedparser.parse(random.choice(RSS_FEEDS))
        for entry in feed.entries:
            title = entry.get("title", "")
            summary = entry.get("summary", "")
            link = entry.get("link", "")
            if is_posted(link):
                continue
            if is_political(title) or is_political(summary):
                print("⚠️ Пропущена политическая новость:", title)
                continue
            return {
                "title": title,
                "summary": summary,
                "link": link,
                "source": feed.feed.title if hasattr(feed, "feed") else "Источник",
                "entry": entry
            }
    return None

# --- Генерация поста ---
def stylize_post(news):
    prompt = f"""
Сделай короткий, интересный Telegram-пост на русском языке по следующему образцу:

🚀 Google добавил ручку для управления размышлениями своей модели AI
📅 17 апреля 2025г., MIT Technology Review
🔹 Google DeepMind обновил свою модель AI Gemini и добавил ручку для управления тем, насколько система "размышляет" в ответе. Эта функция призвана экономить деньги для разработчиков, но признает проблему: модели размышления склонны к переанализу, сжигая деньги и энергию.
💡 Важно для понимания, как развивается мир искусственного интеллекта.
🤔 Как вы считаете, стоит ли давать моделям возможность регулировать уровень размышлений?
🔗 Ссылка: https://www.technologyreview.com/

---
Новость для оформления:

Заголовок: {news['title']}
Описание: {news['summary']}
Источник: {news['source']}
Ссылка: {news['link']}

🔸 Минимум 4-6 строк текста.  
🔸 Форматируй с эмодзи и HTML тегами (<b>жирный</b>).
🔸 Пиши так, чтобы понял даже новичок.
🔸 Избегай сложных терминов.
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

# --- Отправка поста ---
def post_to_telegram(text, image_url):
    url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
    payload = {
        "chat_id": CHANNEL,
        "photo": image_url,
        "caption": text,
        "parse_mode": "HTML"
    }
    response = requests.post(url, data=payload)
    if response.status_code != 200:
        print("⚠️ Ошибка отправки:", response.text)

# --- Основной запуск ---
def main():
    news = get_unique_news()
    if not news:
        print("😐 Нет подходящих новостей")
        return

    print("📰 Новость:", news["title"])
    post_text = stylize_post(news)
    image_url = get_image_url(news["entry"])

    if image_url:
        post_to_telegram(post_text, image_url)
    else:
        print("⚠️ Картинка не найдена, отправка только текста")
        requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            data={"chat_id": CHANNEL, "text": post_text, "parse_mode": "HTML"}
        )

    mark_posted(news["link"])
    print("✅ Пост опубликован")

# --- Точка входа ---
if __name__ == "__main__":
    main()
