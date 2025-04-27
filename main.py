import os
import requests
from dotenv import load_dotenv
from utils import get_new_news, format_post, generate_image

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHANNEL = os.getenv("CHANNEL_USERNAME")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
UNSPLASH_KEY = os.getenv("UNSPLASH_ACCESS_KEY")

def send_post(caption, image_url):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
    payload = {
        "chat_id": CHANNEL_USERNAME,
        "photo": image_url,
        "caption": caption,
        "parse_mode": "HTML"
    }
    response = requests.post(url, data=payload)
    if response.status_code == 200:
        print("✅ Пост успешно отправлен!")
    else:
        print(f"⚠️ Ошибка отправки: {response.status_code} - {response.text}")

def main():
    news = get_new_news()
    if not news:
        print("😐 Нет новых новостей.")
        return

    title, summary, link, published, source = news
    print(f"📰 Новость найдена: {title}")

    caption = format_post(title, summary, link, published, source)
    print("✍️ Пост оформлен.")

    image_url = generate_image(summary)
    if image_url:
        send_post(caption, image_url)
    else:
        print("⚠️ Картинка не сгенерирована. Пропускаем публикацию.")

if __name__ == "__main__":
    main()
