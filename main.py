import os
import requests
import random
import feedparser
from bs4 import BeautifulSoup
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# --- Секреты и токены ---
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHANNEL_USERNAME = os.getenv("CHANNEL_USERNAME")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
GEN_API_KEY = os.getenv("GEN_API_KEY")

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
Ты — автор Telegram-канала про IT, 3D-моделирование и нейросети.

Твоя задача: создать красивый, информативный, живой пост на русском языке минимум 8 предложений.

Требования:
- Минимум 8 предложений в тексте.
- Используй живой, дружеский стиль общения.
- В начале используй эмодзи и выдели заголовок жирным тегом <b>.
- Затем укажи дату и источник публикации с эмодзи 📅.
- Дай краткое, но интересное изложение сути новости (7 предложений).
- Объясни почему это важно или может быть интересно читателю.
- В конце добавь вовлекающий вопрос с эмодзи 🤔.
- Ссылку на источник оформляй с текстом: 📖 Читать подробнее (через тег <a href="...">).
- Обязательно избегай политики, канцелярщины и сложных терминов.

Данные для новости:
Заголовок: {news['title']}
Описание: {news['summary']}
Ссылка: {news['link']}
Создай красивый, интересный пост на русском языке, в котором:

- Минимум 8 предложений.
- Живой стиль, будто общаешься с другом.
- Начни пост с эмодзи 🚀 и выдели заголовок с <b>жирным</b> тегом.
- Укажи дату 📅 и источник публикации.
- Объясни суть новости понятным языком в 5-8 предложениях.
- Расскажи, почему это важно или интересно.
- Заверши пост вовлекающим вопросом с эмодзи 🤔.
- Добавь ссылку: <a href="{news['link']}">📖 Читать подробнее</a>.

Избегай политики, сложных терминов и канцелярщины. Пиши понятно для новичков.

Данные новости:
- Заголовок: {news['title']}
- Описание: {news['summary']}
- Источник: {news['source']}
"""
# --- Отправка поста ---
def post_to_telegram(text, image_url=None):
    if not post_text or len(post_text.strip()) < 20:
        print("❌ Текст не сгенерирован или слишком короткий. Пропускаем.")
        return

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
