"""One-off / re-runnable script to index all books from Postgres into ChromaDB.

Run this any time books are added/updated so the AI chatbot can answer
questions using real store catalog data instead of generic knowledge.

Usage (from project root, venv activated):
    python index_books.py
"""

import asyncio

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.ai.embeddings import EmbeddingService
from app.ai.vector_db import VectorDatabase
from app.models.book import Book
from app.models.genre import Genre


async def main() -> None:
    engine = create_async_engine(
        f"postgresql+asyncpg://{settings.DATABASE_USER}:{settings.DATABASE_PASS}"
        f"@{settings.DATABASE_HOST}:{settings.DATABASE_PORT}/{settings.DATABASE_NAME}"
    )
    session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        result = await session.execute(select(Book))
        books = result.scalars().all()

        genre_result = await session.execute(select(Genre))
        genres_by_id = {g.id: g.name for g in genre_result.scalars().all()}

    if not books:
        print("No books found in the database — add some books first, then re-run this script.")
        await engine.dispose()
        return

    documents = []
    metadatas = []
    ids = []

    for book in books:
        genre_name = genres_by_id.get(book.genre_id, "Unknown genre")
        doc_text = (
            f"Title: {book.title}\n"
            f"Author: {book.author}\n"
            f"Genre: {genre_name}\n"
            f"ISBN: {book.isbn}\n"
            f"Price: ${book.price}\n"
            f"Description: {book.description or 'No description available.'}"
        )
        documents.append(doc_text)
        metadatas.append({"source": f"book_catalog:{book.title}", "book_id": book.id})
        ids.append(f"book_{book.id}")

    print(f"Embedding {len(documents)} book(s)...")
    embedding_service = EmbeddingService()
    embeddings = embedding_service.embed_documents(documents)

    vector_db = VectorDatabase()
    vector_db.add_documents(
        documents=documents, embeddings=embeddings, metadatas=metadatas, ids=ids
    )

    print(f"Indexed {len(documents)} book(s) into the vector database.")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())