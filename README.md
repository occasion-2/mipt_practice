# mipt_practice

A small book scraper for MIPT practice.

## Run

```bash
pip install -r requirements.txt
python -c "from scraper import scrape_books; scrape_books(is_save=True)"
```

The data is saved to `books_data.txt`. Run tests with `pytest`.

Uses `requests`, `BeautifulSoup`, `schedule`, and `pytest`.
