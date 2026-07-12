"""Scraper service for seeding the BookHaven catalog from https://books.toscrape.com/.

books.toscrape.com is a public sandbox site built specifically for scraping
practice -- all data is fictional (no real ISBNs, no author data at all) and
the site has no terms-of-service restrictions against scraping.

Design: split into a pure, synchronous scraping layer (`scrape_toscrape_books`)
with no DB/async dependency, and an async import layer (`import_scraped_books`)
that does the actual DB writes. `import_books_from_toscrape` glues the two
together via `run_in_threadpool`, since `requests` is blocking and must not
run directly on the asyncio event loop.

This split is deliberate so the same `import_books_from_toscrape(db, limit)`
call can be used both by the one-off standalone script (see
`scripts/import_toscrape_books.py`) AND, later, by an admin-triggered API
endpoint -- no logic duplication needed when that's added.

Known data limitations of the source site (by design, not a scraping bug):
  - No author field exists anywhere on books.toscrape.com. We store a fixed
    placeholder ("Unknown Author") and flag this clearly here and in import
    output, rather than silently inventing author names.
  - "ISBN" doesn't exist either; the closest identifier is a 16-character
    hex "UPC" shown in the product table. We use that as `Book.isbn`, which
    conveniently also lets us treat it as a stable unique key for skipping
    already-imported books on repeat runs.
"""

import re
import time
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool

from app.models.genre import Genre
from app.models.inventory import Inventory
from app.repositories.genre_repository import GenreRepository
from app.schemas.book import BookCreate
from app.services.book_service import BookService, BookServiceError

BASE_URL = "https://books.toscrape.com/"
CATALOGUE_START_URL = urljoin(BASE_URL, "catalogue/page-1.html")
USER_AGENT = "BookHavenCatalogImporter/1.0 (educational scraping demo; contact: store admin)"
# Be polite to the target site: a small delay between every HTTP request.
REQUEST_DELAY_SECONDS = 0.3
REQUEST_TIMEOUT_SECONDS = 10


# ── Synchronous scraping layer (no DB access, safe to run in a thread) ──────

def scrape_toscrape_books(limit: int = 20) -> List[Dict[str, Any]]:
    """Scrape up to `limit` books from books.toscrape.com's catalogue.

    Returns a list of plain dicts (not ORM/Pydantic objects) so this
    function has zero framework/DB coupling and is easy to test or reuse.
    """
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})

    detail_urls = _collect_detail_urls(session, limit)

    books: List[Dict[str, Any]] = []
    for url in detail_urls:
        book = _scrape_book_detail(session, url)
        if book:
            books.append(book)
        time.sleep(REQUEST_DELAY_SECONDS)
    return books


def _collect_detail_urls(session: requests.Session, limit: int) -> List[str]:
    """Walk the paginated catalogue listing, collecting product detail page
    URLs until `limit` is reached or pages run out."""
    urls: List[str] = []
    page_url: Optional[str] = CATALOGUE_START_URL

    while page_url and len(urls) < limit:
        resp = session.get(page_url, timeout=REQUEST_TIMEOUT_SECONDS)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        for link in soup.select("article.product_pod h3 a"):
            href = link.get("href")
            if href:
                urls.append(urljoin(page_url, href))
            if len(urls) >= limit:
                break

        next_link = soup.select_one("li.next a")
        if next_link and len(urls) < limit:
            page_url = urljoin(page_url, next_link["href"])
            time.sleep(REQUEST_DELAY_SECONDS)
        else:
            page_url = None

    return urls[:limit]


def _scrape_book_detail(session: requests.Session, url: str) -> Optional[Dict[str, Any]]:
    """Scrape a single product detail page into a plain dict."""
    resp = session.get(url, timeout=REQUEST_TIMEOUT_SECONDS)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    title_tag = soup.select_one("div.product_main h1")
    if not title_tag:
        return None
    title = title_tag.get_text(strip=True)

    price_tag = soup.select_one("p.price_color")
    price = _parse_price(price_tag.get_text(strip=True)) if price_tag else 0.0

    desc_tag = soup.select_one("#product_description ~ p")
    description = desc_tag.get_text(strip=True) if desc_tag else None

    breadcrumb = soup.select("ul.breadcrumb li a")
    # Breadcrumb shape is: Home > Books > <Category> > <Title>
    genre_name = breadcrumb[2].get_text(strip=True) if len(breadcrumb) >= 3 else "General"

    img_tag = soup.select_one("#product_gallery img")
    cover_image_url = urljoin(url, img_tag["src"]) if img_tag and img_tag.get("src") else None

    upc: Optional[str] = None
    stock_quantity: Optional[int] = None
    for row in soup.select("table.table.table-striped tr"):
        header = row.select_one("th")
        value = row.select_one("td")
        if not header or not value:
            continue
        label = header.get_text(strip=True)
        text = value.get_text(strip=True)
        if label == "UPC":
            upc = text
        elif label == "Availability":
            match = re.search(r"(\d+)", text)
            stock_quantity = int(match.group(1)) if match else 0

    if not upc:
        # No stable identifier to key off -- skip rather than risk duplicates.
        return None

    return {
        "title": title,
        "author": "Unknown Author",  # books.toscrape.com publishes no author data
        "isbn": upc,
        "price": price,
        "description": description,
        "cover_image_url": cover_image_url,
        "genre_name": genre_name,
        "stock_quantity": stock_quantity,
    }


def _parse_price(price_text: str) -> float:
    """Extract a float from strings like '£51.77'."""
    match = re.search(r"[\d.]+", price_text)
    return float(match.group()) if match else 0.0


# ── Async DB import layer ────────────────────────────────────────────────

async def import_scraped_books(
    db: AsyncSession, scraped_books: List[Dict[str, Any]]
) -> Dict[str, List[str]]:
    """Insert scraped book dicts into the catalog.

    - Looks up (or creates) a Genre per scraped category name.
    - Skips any book whose ISBN (the scraped UPC) already exists, so this
      is safe to re-run without creating duplicates.
    - Sets real stock quantity on the auto-created Inventory row using the
      scraped availability count (BookService.create_book always starts
      inventory at 0).

    Returns a summary dict: {"created": [...], "skipped": [...], "errors": [...]}.
    """
    genre_repo = GenreRepository(db)
    book_service = BookService(db)

    created: List[str] = []
    skipped: List[str] = []
    errors: List[str] = []

    for item in scraped_books:
        title = item.get("title", "?")
        isbn = item.get("isbn")
        try:
            existing = await book_service.book_repo.get_by_isbn(isbn)
            if existing:
                skipped.append(f"{title} (isbn={isbn})")
                continue

            genre = await genre_repo.get_by_name(item["genre_name"])
            if not genre:
                genre = await genre_repo.create(Genre(name=item["genre_name"]))

            payload = BookCreate(
                title=title,
                author=item["author"],
                isbn=isbn,
                price=item["price"],
                description=item.get("description"),
                cover_image_url=item.get("cover_image_url"),
                genre_id=genre.id,
            )
            book = await book_service.create_book(payload)

            stock_quantity = item.get("stock_quantity")
            if stock_quantity is not None:
                inv_stmt = select(Inventory).where(Inventory.book_id == book.id)
                inv_result = await db.execute(inv_stmt)
                inventory = inv_result.scalars().first()
                if inventory:
                    inventory.stock_quantity = stock_quantity

            created.append(title)
        except BookServiceError as e:
            errors.append(f"{title}: {e.message}")
        except Exception as e:  # noqa: BLE001 - surface any scraping/data issue per-book, don't abort the batch
            errors.append(f"{title}: {e}")

    await db.commit()
    return {"created": created, "skipped": skipped, "errors": errors}


async def import_books_from_toscrape(db: AsyncSession, limit: int = 20) -> Dict[str, List[str]]:
    """Full pipeline: scrape books.toscrape.com (in a worker thread, since
    `requests` is blocking) then import the results into the catalog.

    This is the single entry point meant to be reused by both the
    standalone script and a future admin-triggered endpoint.
    """
    scraped_books = await run_in_threadpool(scrape_toscrape_books, limit)
    return await import_scraped_books(db, scraped_books)