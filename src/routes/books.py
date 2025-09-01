from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, Response, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from typing import List, Optional
import tempfile, io, csv

from ..utils.limiter import limiter
from .. import schemas, auth, models
from ..database import get_async_session
from ..crud import ALLOWED_GENRES, get_or_create_author, bulk_import

router = APIRouter(prefix="/books", tags=["books"])

# ---------------------------
# CREATE BOOK
# ---------------------------
@router.post('/', response_model=schemas.BookRead)
@limiter.limit("5/minute")
async def create_book(
        request: Request,
        book_in: schemas.BookCreate,
        db: AsyncSession = Depends(get_async_session),
        current_user=Depends(auth.get_current_user)
):
    author = await get_or_create_author(db, book_in.author)
    book = models.Book(
        title=book_in.title,
        genre=book_in.genre,
        published_year=book_in.published_year,
        author=author
    )
    db.add(book)
    await db.commit()
    await db.refresh(book)
    return schemas.BookRead.from_orm(book)


# ---------------------------
# LIST BOOKS WITH FILTERS
# ---------------------------
@router.get('/', response_model=List[schemas.BookRead])
@limiter.limit("5/minute")
async def read_books(
        request: Request,
        skip: int = 0,
        limit: int = 20,
        sort: Optional[str] = Query(None, description="Sort field e.g. title or published_year"),
        title: Optional[str] = None,
        author: Optional[str] = None,
        genre: Optional[str] = None,
        year_from: Optional[int] = None,
        year_to: Optional[int] = None,
        db: AsyncSession = Depends(get_async_session)
):
    q = select(models.Book).options(selectinload(models.Book.author))
    if title:
        q = q.where(models.Book.title.ilike(f"%{title}%"))
    if author:
        q = q.join(models.Book.author).where(models.Author.name.ilike(f"%{author}%"))
    if genre:
        q = q.where(models.Book.genre == genre)
    if year_from:
        q = q.where(models.Book.published_year >= year_from)
    if year_to:
        q = q.where(models.Book.published_year <= year_to)
    if sort:
        sort_col = getattr(models.Book, sort, models.Book.id)
        q = q.order_by(sort_col)
    else:
        q = q.order_by(models.Book.id)
    q = q.offset(skip).limit(limit)
    result = await db.execute(q)
    books = result.scalars().all()
    return [schemas.BookRead.from_orm(b) for b in books]


# ---------------------------
# BULK IMPORT BOOKS
# ---------------------------
@router.post('/import')
@limiter.limit("5/minute")
async def import_books(request: Request,
                       file: UploadFile = File(...),
                       db: AsyncSession = Depends(get_async_session),
                       current_user=Depends(auth.get_current_user)
):
    suffix = '.csv' if file.filename.endswith('.csv') else '.json'
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    with tmp as f:
        content = await file.read()
        f.write(content)
    created = await bulk_import(db, tmp.name)
    return {"imported": len(created)}


# ---------------------------
# EXPORT BOOKS CSV
# ---------------------------
@router.get('/export')
@limiter.limit("5/minute")
async def export_books(request: Request, db: AsyncSession = Depends(get_async_session)):
    q = select(models.Book).options(selectinload(models.Book.author)).limit(10000)
    result = await db.execute(q)
    books = result.scalars().all()

    stream = io.StringIO()
    writer = csv.writer(stream)
    writer.writerow(['id', 'title', 'genre', 'published_year', 'author'])
    for book in books:
        writer.writerow([book.id, book.title, book.genre, book.published_year, book.author.name])
    stream.seek(0)
    return Response(stream.getvalue(), media_type='text/csv',
                    headers={"Content-Disposition": "attachment; filename=books.csv"})


# ---------------------------
# RECOMMENDATION ENDPOINT (по автору/жанру)
# ---------------------------
@router.get('/{book_id}/recommend', response_model=List[schemas.BookRead])
async def recommend(request: Request, book_id: int, db: AsyncSession = Depends(get_async_session)):
    q = select(models.Book).options(selectinload(models.Book.author))
    # простая рекомендация: книги того же автора
    book_res = await db.execute(select(models.Book).options(selectinload(models.Book.author))
                                .where(models.Book.id == book_id))
    book = book_res.scalar_one_or_none()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    q = q.where((models.Book.author_id == book.author_id) & (models.Book.id != book.id)).limit(5)
    result = await db.execute(q)
    recs = result.scalars().all()
    return [schemas.BookRead.from_orm(b) for b in recs]


# ---------------------------
# GET BOOK BY ID
# ---------------------------
@router.get('/{book_id}', response_model=schemas.BookRead)
@limiter.limit("5/minute")
async def get_book(request: Request, book_id: int, db: AsyncSession = Depends(get_async_session)):
    q = select(models.Book).options(selectinload(models.Book.author)).where(models.Book.id == book_id)
    result = await db.execute(q)
    book = result.scalar_one_or_none()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return schemas.BookRead.from_orm(book)


# ---------------------------
# UPDATE BOOK
# ---------------------------
@router.put('/{book_id}', response_model=schemas.BookRead)
@limiter.limit("5/minute")
async def update_book(
        request: Request,
        book_id: int,
        book_in: schemas.BookUpdate,
        db: AsyncSession = Depends(get_async_session),
        current_user=Depends(auth.get_current_user)
):
    q = select(models.Book).options(selectinload(models.Book.author)).where(models.Book.id == book_id)
    result = await db.execute(q)
    book = result.scalar_one_or_none()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    if book_in.title:
        book.title = book_in.title
    if book_in.genre:
        if book_in.genre not in ALLOWED_GENRES:
            raise HTTPException(status_code=400, detail="Invalid genre")
        book.genre = book_in.genre
    if book_in.published_year:
        book.published_year = book_in.published_year
    if book_in.author:
        author = await get_or_create_author(db, book_in.author)
        book.author = author

    db.add(book)
    await db.commit()
    await db.refresh(book)
    return schemas.BookRead.from_orm(book)


# ---------------------------
# DELETE BOOK
# ---------------------------
@router.delete('/{book_id}', status_code=204)
async def delete_book(
        request: Request,
        book_id: int,
        db: AsyncSession = Depends(get_async_session),
        current_user=Depends(auth.get_current_user)
):
    q = select(models.Book).where(models.Book.id == book_id)
    result = await db.execute(q)
    book = result.scalar_one_or_none()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    await db.delete(book)
    await db.commit()
    return Response(status_code=204)
