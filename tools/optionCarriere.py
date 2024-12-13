import re
import pymongo
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

from .tools import format_date

url = "https://www.optioncarriere.tn/emploi?s=&l="

client = pymongo.MongoClient("mongodb://host.docker.internal:27017/")
# client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["embedding_db"]

job_embeddings_collection = db["job_embeddings"]


def get_latest_post():
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    post = soup.find("article", class_="job clicky")
    return post


def get_jobs_links(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    job_articles = soup.find_all("article", class_="job clicky")
    links = []

    for job in job_articles:
        if "data-url" in job.attrs:
            links.append("https://www.optioncarriere.tn" + job["data-url"])
    return links


def get_post_content(link):
    response = requests.get(link)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    return soup


def get_all_data(old_links=[]):
    all_jobs = {}
    current_date = datetime.now()
    six_months_ago = current_date - timedelta(days=180)
    current_page = 1
    base_url = url

    # while True:
    while current_page <= 2:
        job_links = get_jobs_links(base_url)

        if not job_links:
            print("No more job offers found. Scraping complete.")
            break

        for link in job_links:
            if job_embeddings_collection.find_one(
                {"link": link, "expiration_date": {"$lt": six_months_ago}}
            ):
                return all_jobs
            try:
                content = get_post_content(link)
                details = get_post_details(content)
                details["link"] = link
                all_jobs[link] = details
                old_links.insert(0, link)
            except Exception as e:
                print(f"Failed to scrape job details from {link}: {e}")

        soup = BeautifulSoup(requests.get(base_url).text, "html.parser")

        next_button = soup.find(
            "button",
            {"class": "ves-control ves-add btn btn-r btn-primary-inverted next"},
        )

        if next_button and "data-value" in next_button.attrs:
            next_page_value = next_button["data-value"]
            base_url = f"https://www.optioncarriere.tn/emploi?s=&l=&p={next_page_value}"
            current_page += 1
        else:
            print("No more pages found. Ending scraping.")
            break

    return all_jobs


def get_post_details(soup):
    job_details = {}
    job_details["Title"] = soup.find("h1").text.strip() if soup.find("h1") else "N/A"
    job_details["Company"] = (
        soup.find("p", class_="company").text.strip()
        if soup.find("p", class_="company")
        else "N/A"
    )
    job_details["Workplace"] = (
        soup.find("span").text.strip() if soup.find("span") else "N/A"
    )
    description = (
        soup.find("section", class_="content").text.strip()
        if soup.find("section", class_="content")
        else "N/A"
    )
    job_details["Description"] = re.sub(r"[\s\n\t\xa0]+", " ", description).strip()

    try:
        date_badge = str(soup.find("span", class_="badge badge-r badge-s").text)
        job_details["expiration_date"] = format_date(date_badge)
    except Exception as e:
        print(f"Failed to get expiration date: {e}")
        job_details["expiration_date"] = "0000-00-00T00:00:00"
    return job_details
