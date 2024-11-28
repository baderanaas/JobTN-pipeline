import re
import requests
from bs4 import BeautifulSoup


from tools import convert_date

url = "https://www.keepjob.com"


def get_number_of_pages(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    pages = soup.find_all("li", class_="page-item")
    page_number = pages[3].find("a")["aria-label"].split()[-1]
    return int(page_number)


def get_posts_links(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    posts = soup.select(
        "div.block_white_a.post.clearfix.silver-job-block > div.content.row-fluid > div.span8"
    )
    links = [post.find("a")["href"] for post in posts if post.find("a")]
    return links


def get_post_content(link):
    request = requests.get(link)
    soup = BeautifulSoup(request.text, "html.parser")
    content = soup.find("div", {"id": "main", "class": "span12 page image-preloader"})

    return content


def get_all_data(url, old_links=[]):
    links = []
    data = {}
    n = get_number_of_pages(url + "/offres-emploi/")
    for i in range(1, n + 1):
        page_url = f"{url}/page/{i}"
        links += get_posts_links(page_url, old_links)
        for link in links:
            if link in old_links:
                return data
            data[link] = get_post_content(url + link)
    return data


def get_post_details(content):
    details = {}
    block = content.find("div", {"class": "span9 content"}).text
    text = re.sub(r"\t+", "", block)
    text = text.strip().split("\n")
    text = [line for line in text if line != ""]
    details["company"] = text[0]
    details["job_title"] = content.find("h2", class_="job-title").text
    details["description"] = content.find(
        "div", class_="block_a span12 no-margin-left"
    ).text
    items = content.find_all("div", class_="meta")
    data = {}
    for meta in items:
        label = meta.find("b").text.strip().replace(":", "")
        value = meta.find("br").next_sibling.strip() if meta.find("br") else ""
        value = re.sub(r"[\s\n\t]+", " ", value).strip()
        data[label] = value
    details["expiration_date"] = convert_date(data["Publiée le"])
    details["workplace"] = data["Lieu de travail"]
    for key, value in data.items():
        if key not in ["Publiée le", "Lieu de travail"]:
            details["description"] += f"\n{key}: {value}"

    return details
