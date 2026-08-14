"""Book recommendations: public listing + admin CRUD.

Books power the /books page: cover, title, author, short description and a
purchase link. The author's own book is seeded on startup so the shelf is
never empty; everything else is managed from the admin panel.
"""
import uuid
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from config import logger
from db import db
from security import get_admin_user
from utils import now_utc, iso

router = APIRouter(prefix='/api')

SEED_BOOKS = [{
    'seed_key': 'how-trading-can-make-you-money-v1',
    'title': 'How Trading Can Make You Money',
    'author': 'Anish Pujari',
    'description': 'Trading can generate real income, but roughly 90% of retail traders lose money, '
                   "SEBI's own F&O data says so. Not because trading doesn't work, but because they "
                   'skip risk management, trade too big, and have no process. This book teaches the '
                   'habits of the profitable 10% from day one: strategies, AI prompts, and a 12-month plan.',
    'cover_image': '/book-cover.webp',
    'buy_url': 'https://www.amazon.in/dp/B0HBR9THSX',
    'featured': True,
}]


async def ensure_seed_books():
    """Insert seed books once (keyed by seed_key) so the shelf self-heals."""
    for b in SEED_BOOKS:
        if await db.books.find_one({'seed_key': b['seed_key']}):
            continue
        await db.books.insert_one({
            'id': str(uuid.uuid4()), **b, 'sort': 0, 'created_at': iso(now_utc()),
        })
        logger.info(f"Books: seeded '{b['title']}'")


class BookIn(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    author: str = Field(min_length=1, max_length=120)
    description: str = Field(default='', max_length=1200)
    cover_image: str = Field(default='', max_length=600)
    buy_url: str = Field(min_length=4, max_length=600)
    featured: bool = False
    sort: int = 0


def _public(b: dict) -> dict:
    return {k: b.get(k) for k in
            ('id', 'title', 'author', 'description', 'cover_image', 'buy_url', 'featured', 'sort', 'created_at')}


@router.get('/books')
async def list_books():
    books = await db.books.find({}).sort([('featured', -1), ('sort', 1), ('created_at', 1)]).to_list(200)
    return {'books': [_public(b) for b in books]}


@router.post('/admin/books')
async def create_book(body: BookIn, admin=Depends(get_admin_user)):
    book = {'id': str(uuid.uuid4()), **body.model_dump(), 'created_at': iso(now_utc())}
    await db.books.insert_one(dict(book))
    return _public(book)


@router.put('/admin/books/{book_id}')
async def update_book(book_id: str, body: BookIn, admin=Depends(get_admin_user)):
    res = await db.books.update_one({'id': book_id}, {'$set': body.model_dump()})
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail='Book not found')
    updated = await db.books.find_one({'id': book_id})
    return _public(updated)


@router.delete('/admin/books/{book_id}')
async def delete_book(book_id: str, admin=Depends(get_admin_user)):
    res = await db.books.delete_one({'id': book_id})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail='Book not found')
    return {'ok': True}
