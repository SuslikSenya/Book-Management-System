from typing import List, Optional
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from . import models, schemas
import pandas as pd

ALLOWED_GENRES = schemas.ALLOWED_GENRES


async def get_or_create_author(session: AsyncSession, name: str) -> models.Author:
    """Returns the author by name or creates a new one"""
    q = select(models.Author).where(models.Author.name == name)
    res = await session.execute(q)
    author = res.scalar_one_or_none()
    if author:
        return author

    new_author = models.Author(name=name)
    session.add(new_author)
    await session.commit()
    await session.refresh(new_author)
    return new_author


async def create_book(session: AsyncSession, book_in: schemas.BookCreate) -> models.Book:
    """Creates a new book"""
    if book_in.genre not in ALLOWED_GENRES:
        raise ValueError(f"Unknown genre: {book_in.genre}")

    author = await get_or_create_author(session, book_in.author)

    new_book = models.Book(
        title=book_in.title,
        genre=book_in.genre,
        published_year=book_in.published_year,
        author_id=author.id
    )
    session.add(new_book)
    await session.commit()
    await session.refresh(new_book)
    return new_book


async def get_book(session: AsyncSession, book_id: int) -> Optional[models.Book]:
    """Get the book with the authors"""
    q = select(models.Book).where(models.Book.id == book_id).options(
        selectinload(models.Book.author)
    )
    res = await session.execute(q)
    return res.scalar_one_or_none()


async def list_books(
    session: AsyncSession,
    skip: int = 0,
    limit: int = 20,
    sort: Optional[str] = "b.id",
    filters: Optional[dict] = None
) -> List[dict]:
    """List of books with filtering and sorting"""
    base_sql = """
        SELECT b.id, b.title, b.genre, b.published_year,
               a.id AS author_id, a.name AS author_name
        FROM books b
        JOIN authors a ON b.author_id = a.id
    """
    params = {}
    where_clauses = []

    if filters:
        if 'title' in filters:
            where_clauses.append("b.title ILIKE :title")
            params['title'] = f"%{filters['title']}%"
        if 'author' in filters:
            where_clauses.append("a.name ILIKE :author")
            params['author'] = f"%{filters['author']}%"
        if 'genre' in filters:
            where_clauses.append("b.genre = :genre")
            params['genre'] = filters['genre']
        if 'year_from' in filters:
            where_clauses.append("b.published_year >= :year_from")
            params['year_from'] = filters['year_from']
        if 'year_to' in filters:
            where_clauses.append("b.published_year <= :year_to")
            params['year_to'] = filters['year_to']

    if where_clauses:
        base_sql += " WHERE " + " AND ".join(where_clauses)

    if sort:
        allowed_sort = ["b.id", "b.title", "b.published_year", "b.genre"]
        if sort not in allowed_sort:
            sort = "b.id"
        base_sql += f" ORDER BY {sort}"

    base_sql += " LIMIT :limit OFFSET :skip"
    params.update({'limit': limit, 'skip': skip})

    result = await session.execute(text(base_sql), params)
    rows = result.fetchall()
    return [
        {
            "id": r.id,
            "title": r.title,
            "genre": r.genre,
            "published_year": r.published_year,
            "author": {"id": r.author_id, "name": r.author_name}
        } for r in rows
    ]


async def bulk_import(session: AsyncSession, file_path: str) -> List[models.Book]:
    """Import from CSV or JSON"""
    if file_path.endswith(".csv"):
        df = pd.read_csv(file_path)
    else:
        df = pd.read_json(file_path)

    created = []
    for _, row in df.iterrows():
        try:
            book_in = schemas.BookCreate(
                title=str(row['title']),
                author=str(row['author']),
                genre=str(row['genre']),
                published_year=int(row['published_year'])
            )
            new_book = await create_book(session, book_in)
            created.append(new_book)
        except Exception:
            continue

    return created


async def recommend_books(session: AsyncSession, book_id: int, limit: int = 10) -> List[dict]:
    """Recommendations by genre or author"""
    query = text("""
        SELECT b.id, b.title, b.genre, b.published_year,
               a.id AS author_id, a.name AS author_name
        FROM books b
        JOIN authors a ON b.author_id = a.id
        WHERE b.id != :book_id
          AND (b.genre = (SELECT genre FROM books WHERE id = :book_id)
               OR b.author_id = (SELECT author_id FROM books WHERE id = :book_id))
        LIMIT :limit
    """)
    result = await session.execute(query, {"book_id": book_id, "limit": limit})
    rows = result.mappings().all()
    return [
        {
            "id": r['id'],
            "title": r['title'],
            "genre": r['genre'],
            "published_year": r['published_year'],
            "author": {"id": r['author_id'], "name": r['author_name']}
        } for r in rows
    ]
