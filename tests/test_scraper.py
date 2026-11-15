import json
import os
import sys
from pathlib import Path
import pytest

# Добавляем корневую директорию проекта в sys.path для корректного импорта
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scraper import get_book_data, scrape_books  # noqa: E402

SAMPLE_BOOK_URL = (
    'http://books.toscrape.com/catalogue/'
    'a-light-in-the-attic_1000/index.html'
)


@pytest.fixture(scope='module')
def sample_book() -> dict:
    """Фикстура, один раз загружающая данные тестовой книги для проверок."""
    return get_book_data(SAMPLE_BOOK_URL)


def test_get_book_data_returns_dict_with_required_keys(
    sample_book: dict,
) -> None:
    """Проверяет, что get_book_data возвращает словарь со всеми ключами."""
    expected_keys = {
        'Title',
        'Price',
        'Rating',
        'Availability',
        'Description',
        'UPC',
        'Product Type',
        'Price (excl. tax)',
        'Price (incl. tax)',
        'Tax',
        'Number of reviews',
    }
    assert isinstance(sample_book, dict)
    assert expected_keys.issubset(sample_book.keys())


def test_get_book_data_field_values(sample_book: dict) -> None:
    """Проверяет корректность парсинга конкретных полей известной книги."""
    assert sample_book['Title'] == 'A Light in the Attic'
    assert sample_book['Price'] == '£51.77'
    assert sample_book['Rating'] == 3
    assert sample_book['Availability'] == 'In stock (22 available)'
    assert sample_book['UPC'] == 'a897fe39b1053632'


def test_get_book_data_invalid_url_raises() -> None:
    """Проверяет, что при несуществующей странице выбрасывается исключение."""
    invalid_url = 'http://books.toscrape.com/catalogue/non-existent-book.html'
    with pytest.raises(Exception):
        get_book_data(invalid_url)


def test_scrape_books_count_and_save(tmp_path: Path, monkeypatch) -> None:
    """Проверяет сбор всех 1000 книг из каталога и сохранение в файл."""
    monkeypatch.chdir(tmp_path)
    books = scrape_books(is_save=True)

    assert isinstance(books, list)
    assert len(books) == 1000

    saved_file = tmp_path / 'books_data.txt'
    assert os.path.exists(saved_file)

    with open(saved_file, 'r', encoding='utf-8') as file:
        loaded_books = json.load(file)
    assert len(loaded_books) == 1000