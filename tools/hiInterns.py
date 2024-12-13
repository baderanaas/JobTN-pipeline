import re
import pymongo
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

from .tools import convert_date

url = "https://hi-interns.com/internships?facets=%5B%22Company.City%22%2C%22Keywords.Value%22%5D&facetFilters=%5B%5D"

client = pymongo.MongoClient("mongodb://host.docker.internal:27017/")
# client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["embedding_db"]

job_embeddings_collection = db["job_embeddings"]


def get_number_of_pages():
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    number_pages = soup.find_all(
        "button",
        class_="inline-flex h-10 w-10 items-center justify-center rounded-full text-sm font-medium text-gray-500 hover:text-indigo-900",
    )[-2].text
    return int(number_pages)


def get_latest_post():
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    post = soup.find("section", class_="relative overflow-clip")
    return post


def get_posts_links(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    posts = soup.find_all("section", class_="relative overflow-clip")
    links = ["https://hi-interns.com" + post.a["href"] for post in posts]
    return links


def get_post_content(link):
    response = requests.get(link)
    soup = BeautifulSoup(response.text, "html.parser")
    content = soup.find(
        "div",
        class_="relative mx-auto flex flex-col items-center justify-between gap-4 md:flex-row-reverse md:items-start",
    )
    return content


def get_all_data():
    n = get_number_of_pages()
    current_date = datetime.now()
    six_months_ago = current_date - timedelta(days=180)
    # for i in range(n):
    for i in range(3):
        if i == 0:
            page_url = url
        else:
            page_url = f"{url}&page={i}"
        links = []
        data = {}
        links = get_posts_links(page_url)
        for link in links:
            if job_embeddings_collection.find_one(
                {"link": link, "expiration_date": {"$lt": six_months_ago}}
            ):
                return data
            content = get_post_content(link)
            details = get_post_details(content)
            details["link"] = link
            data[link] = details
        return data


def get_post_details(content):
    details = {}
    details["Company"] = content.find("p", class_="text-center text-xl font-bold").text
    details["Workplace"] = content.find(
        "div", class_="flex flex-wrap justify-center gap-4"
    ).text.strip()
    details["Title"] = content.find(
        "h1", class_="mb-8 text-2xl font-bold lg:text-2xl"
    ).text.strip()
    description = content.find("div", class_="prose text-black").text.strip()
    details["Description"] = re.sub(r"[\s\n\t\xa0]+", " ", description).strip()
    details["expiration_date"] = convert_date(
        content.find("p", class_="text-sm text-gray-500 md:hidden")
        .text.strip()
        .split(":")[1]
        .strip()
    )

    return details
