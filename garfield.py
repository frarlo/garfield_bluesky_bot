import requests
from bs4 import BeautifulSoup
from atproto import Client
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os
import random
import time

load_dotenv()

# Bot configuration:
USERNAME = os.environ.get('BLUESKY_USERNAME') or os.getenv("BLUESKY_USERNAME")
PASSWORD = os.environ.get('BLUESKY_PASSWORD') or os.getenv("BLUESKY_PASSWORD")
BASE_URL = "https://www.gocomics.com/garfield"
START_DATE = datetime(1978, 6, 19) # Garfield first comic
END_DATE = datetime.now()

# Bluesky client init
client = Client()
client.login(USERNAME, PASSWORD)


# Returns a random date between today and Garfield's first comic:
def get_random_date():
    date = START_DATE + timedelta(days=random.randint(0, (END_DATE - START_DATE).days))
    return date


# Returns the url of the Garfield comic in the random date:
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


# Posts the image and the date in Bluesky:
def post_to_bluesky(comic_image_url, comic_date):
    date = comic_date.strftime("%d/%m/%Y")
    text = f"#Garfield {date} 🐱"

    response = requests.get(comic_image_url)
    if response.status_code != 200:
        print("Failed to download image.")
        return

    image_data = response.content
    uploaded_blob = client.upload_blob(image_data)

    embed = {
        "$type": "app.bsky.embed.images",
        "images": [
            {
                "image": uploaded_blob['blob'],
                "alt": "Garfield comic"
            }
        ]
    }

    client.send_post(text=text, embed=embed)
    print(f"Posted comic from {comic_url}")


# Main function, it will publish Garfield comics every six hours:
while True:
    random_date = get_random_date()
    comic_url = f"{BASE_URL}/{random_date.year}/{random_date.month:02}/{random_date.day:02}"
    image_url = fetch_comic_image(comic_url)

    if image_url:
        post_to_bluesky(image_url, random_date)
    else:
        print(f"Failed to fetch comic from {comic_url}")

    time.sleep(7200)