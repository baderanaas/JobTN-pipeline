import requests
from bs4 import BeautifulSoup

from .tools import format_date

url = "https://www.optioncarriere.tn/emploi?s=&l="


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
    current_page = 1
    base_url = url

    # while True:
    while current_page <= 2:
        job_links = get_jobs_links(base_url)

        if not job_links:
            print("No more job offers found. Scraping complete.")
            break

        for link in job_links:
            if link in old_links:
                return all_jobs, old_links
            try:
                all_jobs[link] = get_post_content(link)
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

    return all_jobs, old_links


def get_post_detail(content):
    soup = BeautifulSoup(content, "html.parser")
    job_details = {}
    job_details["Title"] = soup.find("h1").text.strip() if soup.find("h1") else "N/A"
    job_details["Company"] = (
        soup.find("p", class_="company").text.strip()
        if soup.find("p", class_="company")
        else "N/A"
    )
    job_details["Location"] = (
        soup.find("span").text.strip() if soup.find("span") else "N/A"
    )
    job_details["Description"] = (
        soup.find("section", class_="content").text.strip()
        if soup.find("section", class_="content")
        else "N/A"
    )

    date_badge = soup.find("ul", class_="tags")
    date_ = date_badge.text.strip().split("\n")[0] if date_badge else "N/A"
    if date_ != "N/A":
        job_details["expiration_date"] = format_date(date_)
    else:
        job_details["expiration_date"] = date_

    return job_details
