import re
import requests
from bs4 import BeautifulSoup


from .tools import convert_date

url = "https://www.keejob.com"


def get_number_of_pages():
    response = requests.get(url + "/offres-emploi/")
    soup = BeautifulSoup(response.text, "html.parser")
    pages = soup.find_all("li", class_="page-item")
    page_number = pages[3].find("a")["aria-label"].split()[-1]
    return int(page_number)


def get_latest_post():
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    post = soup.select_one(
        "div.block_white_a.post.clearfix.silver-job-block > div.content.row-fluid > div.span8"
    )
    return post


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


def get_all_data(old_links=[]):
    links = []
    data = {}
    n = get_number_of_pages()
    # for i in range(1, n + 1):
    for i in range(1, 4):
        page_url = f"{url}/offres-emploi/?page/{i}"
        links = get_posts_links(page_url)
        for link in links:
            if link in old_links:
                return data, old_links
            content = get_post_content(url + link)
            details = get_post_details(content)
            details["link"] = link
            data[link] = details
            old_links.insert(0, link)
    return data, old_links


def get_post_details(content):
    details = {}
    block = content.find("div", {"class": "span9 content"}).text
    text = re.sub(r"\t+", "", block)
    text = text.strip().split("\n")
    text = [line for line in text if line != ""]
    details["Company"] = text[0]
    details["Title"] = content.find("h2", class_="job-title").text
    details["Description"] = content.find(
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
    details["Workplace"] = data["Lieu de travail"]
    for key, value in data.items():
        if key not in ["Publiée le", "Lieu de travail"]:
            details["Description"] += f"\n{key}: {value}"

    return details
