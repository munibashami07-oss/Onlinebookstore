def scrape_toscrape_books(limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """Scrape books from books.toscrape.com's catalogue.

    If `limit` is None, walks every catalogue page and scrapes every book
    (~1000 on the real site). Pass an int to cap it (useful for testing).
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


def _collect_detail_urls(session: requests.Session, limit: Optional[int]) -> List[str]:
    """Walk every paginated catalogue page, collecting product detail URLs.
    Stops early only if `limit` is set and reached; otherwise walks until
    there is no more 'next' page."""
    urls: List[str] = []
    page_url: Optional[str] = CATALOGUE_START_URL

    while page_url and (limit is None or len(urls) < limit):
        resp = session.get(page_url, timeout=REQUEST_TIMEOUT_SECONDS)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        for link in soup.select("article.product_pod h3 a"):
            href = link.get("href")
            if href:
                urls.append(urljoin(page_url, href))
            if limit is not None and len(urls) >= limit:
                break

        next_link = soup.select_one("li.next a")
        if next_link and (limit is None or len(urls) < limit):
            page_url = urljoin(page_url, next_link["href"])
            time.sleep(REQUEST_DELAY_SECONDS)
        else:
            page_url = None

    return urls[:limit] if limit is not None else urls


async def import_books_from_toscrape(db: AsyncSession, limit: Optional[int] = None) -> Dict[str, List[str]]:
    """Full pipeline: scrape books.toscrape.com (in a worker thread) then
    import results into the catalog. `limit=None` (default) scrapes every
    book on the site instead of capping at 20."""
    scraped_books = await run_in_threadpool(scrape_toscrape_books, limit)
    return await import_scraped_books(db, scraped_books)