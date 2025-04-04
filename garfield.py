import os
import random
from datetime import datetime, timedelta

import requests
from atproto import Client, models
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from PIL import Image
from io import BytesIO
from math import gcd

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

    session = requests.Session()
    # Headers update to simulate a browser version
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9',
        'Accept-Language': 'en-US,en;q=0.5',
        'Referer': 'https://www.gocomics.com/',
        'DNT': '1',  # Do Not Track
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    })

    response = session.get(url)
    if response.status_code != 200:
        return None

    soup = BeautifulSoup(response.text, 'html.parser')
    image_tags = soup.find_all('img', class_='Comic_comic__image__6e_Fw')

    if len(image_tags) > 1 and 'src' in image_tags[5].attrs:
        return image_tags[5]['src']
    return None


# Posts the image and the date in Bluesky:
def post_to_bluesky(comic_image_url, comic_date):
    date = comic_date.strftime("%d/%m/%Y")
    text = f"#Garfield {date} 🐱"
    tag = "Garfield"
    hash_len = len(tag.encode('UTF-8')) + 1
    facets = [
        models.AppBskyRichtextFacet.Main(
            features=[models.AppBskyRichtextFacet.Tag(tag=tag)],
            index=models.AppBskyRichtextFacet.ByteSlice(byte_start=0, byte_end=hash_len)
        )
    ]
    alt = f"Garfield published on {date}"

    response = requests.get(comic_image_url)
    if response.status_code != 200:
        print("Failed to download image.")
        return

    image_data = response.content
    aspect_width, aspect_height = get_image_space_ratio(image_data)
    uploaded_blob = client.upload_blob(image_data)

    embed = {
        "$type": "app.bsky.embed.images",
        "images": [
            {
                "image": uploaded_blob['blob'],
                "alt": alt,
                "aspectRatio": {
                    "width": aspect_width,
                    "height": aspect_height
                }
            }
        ]
    }

    client.send_post(text=text, facets=facets, embed=embed)


# Gets the aspect ratio of the comic strip:
def get_image_space_ratio(image_data):
    image = Image.open(BytesIO(image_data))
    width, height = image.size

    common_divisor = gcd(width, height)

    aspect_width = width // common_divisor
    aspect_height = height // common_divisor

    return aspect_width, aspect_height


# Main function, it will publish a random Garfield comic in Bluesky:
def main():
    random_date = get_random_date()
    comic_url = f"{BASE_URL}/{random_date.year}/{random_date.month:02}/{random_date.day:02}"
    image_url = fetch_comic_image(comic_url)

    if image_url:
        post_to_bluesky(image_url, random_date)

if __name__ == "__main__":
    main()