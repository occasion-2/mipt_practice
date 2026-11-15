import json
import re
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


def _create_session() -> requests.Session:
    """Создаёт HTTP-сессию с автоматическими повторами при сетевых сбоях."""
    session = requests.Session()
    retries = Retry(
        total=5,
        backoff_factor=0.5,
        status_forcelist=[429, 500, 502, 503, 504],
    )
    adapter = HTTPAdapter(max_retries=retries)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session


def get_book_data(
    book_url: str, session: requests.Session | None = None
) -> dict:
    """
    Парсит информацию о книге со страницы каталога Books to Scrape.

    Args:
        book_url (str): URL-адрес страницы конкретной книги.
        session (requests.Session | None): Опциональная HTTP-сессия.

    Returns:
        dict: Словарь с данными о книге.
    """
    requester = session or requests
    response = requester.get(book_url, timeout=15)
    response.raise_for_status()
    response.encoding = 'utf-8'

    soup = BeautifulSoup(response.text, 'html.parser')
    book_data = {}

    main_div = soup.find('div', class_='product_main')
    title_tag = main_div.find('h1') if main_div else None
    book_data['Title'] = title_tag.text.strip() if title_tag else None

    price_tag = soup.find('p', class_='price_color')
    book_data['Price'] = price_tag.text.strip() if price_tag else None

    rating_map = {'One': 1, 'Two': 2, 'Three': 3, 'Four': 4, 'Five': 5}
    rating_tag = soup.find('p', class_='star-rating')
    if rating_tag and len(rating_tag.get('class', [])) > 1:
        rating_word = rating_tag['class'][1]
        book_data['Rating'] = rating_map.get(rating_word, rating_word)
    else:
        book_data['Rating'] = None

    stock_tag = soup.find('p', class_='instock availability')
    if stock_tag:
        stock_text = stock_tag.text.strip()
        stock_match = re.search(r'\((\d+)\s+available\)', stock_text)
        book_data['Availability'] = (
            int(stock_match.group(1)) if stock_match else stock_text
        )
    else:
        book_data['Availability'] = None

    desc_header = soup.find('div', id='product_description')
    if desc_header:
        desc_tag = desc_header.find_next_sibling('p')
        book_data['Description'] = desc_tag.text.strip() if desc_tag else None
    else:
        book_data['Description'] = None

    table = soup.find('table', class_='table-striped')
    if table:
        for row in table.find_all('tr'):
            header = row.find('th')
            value = row.find('td')
            if header and value:
                book_data[header.text.strip()] = value.text.strip()

    return book_data


def scrape_books(is_save: bool = False) -> list[dict]:
    """
    Собирает информацию обо всех книгах из каталога Books to Scrape.

    Args:
        is_save (bool): Флаг сохранения результата в файл books_data.txt.

    Returns:
        list[dict]: Список словарей с данными обо всех книгах.
    """
    all_books = []
    page_num = 1

    with _create_session() as session:
        while True:
            page_url = (
                f'http://books.toscrape.com/catalogue/page-{page_num}.html'
            )
            response = session.get(page_url, timeout=15)

            if response.status_code == 404:
                break

            response.raise_for_status()
            response.encoding = 'utf-8'

            soup = BeautifulSoup(response.text, 'html.parser')
            book_cards = soup.find_all('article', class_='product_pod')

            if not book_cards:
                break

            for card in book_cards:
                h3_tag = card.find('h3')
                link_tag = h3_tag.find('a') if h3_tag else None
                if link_tag and link_tag.get('href'):
                    book_url = urljoin(page_url, link_tag['href'])
                    book_info = get_book_data(book_url, session=session)
                    all_books.append(book_info)

            page_num += 1

    if is_save:
        with open('books_data.txt', 'w', encoding='utf-8') as file:
            json.dump(all_books, file, ensure_ascii=False, indent=4)

    return all_books