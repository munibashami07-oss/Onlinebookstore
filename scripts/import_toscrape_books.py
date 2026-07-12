"""
Standalone script to seed the BookHaven catalog with sample data scraped
from https://books.toscrape.com/ -- a public sandbox site built for
scraping practice. All scraped data is fictional: there are no real ISBNs
and no author information on the source site at all (see
app/services/scraper_service.py for details on how those gaps are handled).

Usage (run from the project root, with your venv activated):

    python scripts/import_toscrape_books.py
    python scripts/import_toscrape_books.py --limit 20
"""

import argparse
import asyncio
import sys
from pathlib import Path

# Make the `app` package importable when this script is run directly
# (e.g. `python scripts/import_toscrape_books.py` from the project root).
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.session import SessionLocal  # noqa: E402
from app.services.scraper_service import import_books_from_toscrape  # noqa: E402


async def main(limit: int) -> None:
    print(f"Scraping up to {limit} books from books.toscrape.com ...")

    async with SessionLocal() as db:
        result = await import_books_from_toscrape(db, limit=limit)

    print("\nImport complete.")

    print(f"\nCreated ({len(result['created'])}):")
    for title in result["created"]:
        print(f"  + {title}")

    if result["skipped"]:
        print(f"\nSkipped -- already in catalog ({len(result['skipped'])}):")
        for entry in result["skipped"]:
            print(f"  - {entry}")

    if result["errors"]:
        print(f"\nErrors ({len(result['errors'])}):")
        for err in result["errors"]:
            print(f"  ! {err}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Import sample books scraped from books.toscrape.com into the BookHaven catalog."
    )
    parser.add_argument(
        "--limit", type=int, default=20, help="Number of books to import (default: 20)"
    )
    args = parser.parse_args()
    asyncio.run(main(args.limit))