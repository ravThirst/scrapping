import json
from dataclasses import dataclass

import requests
from bs4 import BeautifulSoup
from fake_headers import Headers

HOST = "https://spb.hh.ru"
ARTICLES = f"{HOST}/search/vacancy?text=python&area=1&area=2"
ARTICLES_HREF = "/search/vacancy?text=python&area=1&area=2"
MAX_PAGES = 0
VACANCIES_PROGRESS = 0


@dataclass
class Vacancy:
    reference: str
    salary: str
    company_name: str
    city: str


def get_headers():
    return Headers(browser="firefox", os="win").generate()


def get_text(url):
    r = requests.get(url, headers=get_headers())
    r.encoding = r.apparent_encoding
    return r.text


def parse_vacancy_by_ref(ref, page):
    html = get_text(ref)
    soup = BeautifulSoup(html, features="html5lib")

    description = str(soup.find(attrs={"class": "vacancy-description"})).lower()
    if "flask" not in description or "django" not in description:
        update_progress(page)
        return None

    salary = soup.find(attrs={"data-qa": "vacancy-salary-compensation-type-net"})

    if salary:
        salary = salary.text
    else:
        salary = "N/A"

    company_name = (
        soup.find(attrs={"data-qa": "vacancy-company-name"}).find("span").text
    )

    city = soup.find(attrs={"data-qa": "vacancy-view-location"})
    if city is None:
        city = soup.find(attrs={"data-qa": "vacancy-view-raw-address"})
    city = city.text

    update_progress(page)

    return Vacancy(
        ref, salary.replace("\xa0", " "), company_name.replace("\xa0", " "), city
    )


def update_progress(page):
    global VACANCIES_PROGRESS
    VACANCIES_PROGRESS += 1
    print(f"{VACANCIES_PROGRESS} vacancy, page {page} of {MAX_PAGES}")


def parse_search_page(page):
    html = get_text(f"{ARTICLES}&page={page}&hhtmFrom=vacancy_search_list")
    soup = BeautifulSoup(html, features="html5lib")
    vacancies = soup.find_all(attrs={"class": "serp-item__title"})
    vacancy_list = [parse_vacancy_by_ref(i["href"], page) for i in vacancies]
    print(f"All articles in page {page} are processed")
    return [i for i in vacancy_list if i is not None]


def get_search_params():
    html = get_text(f"{ARTICLES}")
    soup = BeautifulSoup(html, features="html5lib")
    page_buttons = soup.find_all(
        attrs={"class": "bloko-button", "data-qa": "pager-page"}
    )
    max_page_number = max([int(i.find("span").text) for i in page_buttons])
    print(f"Search contains {max_page_number} pages")
    global MAX_PAGES
    MAX_PAGES = max_page_number
    return max_page_number


def program():
    scan_mode = input(
        "Do you want to scan all pages (may take a long time)? Y/N\n"
    ).lower()
    vacancies_list_of_lists = []
    if scan_mode == "y":
        vacancies_list_of_lists = [
            parse_search_page(page) for page in range(1, get_search_params())
        ]
    else:
        global MAX_PAGES
        MAX_PAGES = 1
        vacancies_list_of_lists = [parse_search_page(1)]

    vacancies = [
        item.__dict__ for sublist in vacancies_list_of_lists for item in sublist
    ]
    json_string = json.dumps(vacancies, ensure_ascii=False)
    with open("vacancies.json", "w", encoding="utf-8") as outfile:
        outfile.write(json_string)


if __name__ == "__main__":
    program()
