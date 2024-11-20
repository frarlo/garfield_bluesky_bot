import os
import requests
from bs4 import BeautifulSoup
from atproto import Client
from datetime import datetime, timedelta
import random
import time

# Bot configuration:
USERNAME = os.environ.get('BLUESKY_USERNAME')
PASSWORD = os.environ.get('BLUESKY_PASSWORD')
BASE_URL = "https://www.gocomics.com/garfield"
START_DATE = datetime(1978, 6, 19) # Garfield first comic
END_DATE = datetime.now()

# Bluesky client init
client = Client()
client.login(USERNAME, PASSWORD)


def get_random_comic_url():
    date = START_DATE + timedelta(days=random.randint(0, (END_DATE - START_DATE).days))
    return date


def fetch_comic_image(url):
    response = requests.get(url)
    if response.status_code != 200:
        return None

    soup = BeautifulSoup(response.text, 'html.parser')
    comic_container = soup.find('div', class_='comic__container')

    if comic_container:
        image_tag = comic_container.find('picture').find('img', class_='img-fluid')
        if image_tag:
            return image_tag['src']
    return None


def post_to_bluesky(image_url, comic_date):

    text = f"#Garfield {comic_date} 🐱"

    response = requests.get(image_url)
    if response.status_code != 200:
        print("Failed to download image.")
        return

    image_data = response.content
    uploaded_blob = client.upload_blob(image_data)  # Sin content_type

    embed = {
        "$type": "app.bsky.embed.images",
        "images": [
            {
                "image": uploaded_blob['blob'],  # Usar el BlobRef de la imagen subida
                "alt": "Garfield comic"
            }
        ]
    }

    client.send_post(text=text, embed=embed)
    print(f"Posted comic from {comic_url}")


while True:
    random_date = get_random_comic_url()
    comic_url = f"{BASE_URL}/{random_date.year}/{random_date.month:02}/{random_date.day:02}"
    image_url = fetch_comic_image(comic_url)

    if image_url:
        post_to_bluesky(image_url, random_date)
    else:
        print(f"Failed to fetch comic from {comic_url}")

    time.sleep(21600)  # Repeats every six hours
