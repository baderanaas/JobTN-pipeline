import requests
from bs4 import BeautifulSoup
from .tools import convert_date

url = "https://www.farojob.net/jobs/?s&type&paged="


def get_number_of_pages():
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    return int(soup.find_all("a", class_="page-numbers")[-2].text)


def get_latest_post():
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    post = soup.find("a", class_="job-details-link")
    return post


def get_posts_links(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    posts = soup.find_all("a", class_="job-details-link")
    links = [post["href"] for post in posts]
    return links


def get_post_content(link):
    response = requests.get(link)
    soup = BeautifulSoup(response.text, "html.parser")
    content = soup.find("div", class_="job-desc")
    post_date = soup.find("span", class_="job-date__posted").text
    post_date = convert_date(post_date)
    return [content, post_date]


def get_all_data(old_links=[]):
    n = get_number_of_pages()
    # for i in range(n):
    for i in range(3):
        page_url = f"{url}{i+1}"
        links = []
        data = {}
        links += get_posts_links(page_url)
        for link in links:
            if link in old_links:
                return data, old_links
            data[link] = get_post_content(link)
            old_links.insert(0, link)
        return data, old_links


def get_post_details(content):
    paragraphs = content.find_all("p")
    post = {}
    post["company"] = " ".join(paragraphs[0].text.split()[:-1])
    post["title"] = paragraphs[1].text
    post["description"] = " ".join([paragraph.text for paragraph in paragraphs[2:]])
    post["workplace"] = "Tunisie"
    return post
