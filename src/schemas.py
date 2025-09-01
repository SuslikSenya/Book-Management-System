from pydantic import BaseModel, constr, conint
from typing import Optional
import datetime

CURRENT_YEAR = datetime.date.today().year
ALLOWED_GENRES = ["Fiction", "Non-Fiction", "Science", "History", "Fantasy", "Mystery"]


class AuthorCreate(BaseModel):
    name: constr(strip_whitespace=True, min_length=1)


class AuthorRead(BaseModel):
    id: int
    name: str

    model_config = {"from_attributes": True}


class BookBase(BaseModel):
    title: constr(strip_whitespace=True, min_length=1)
    genre: constr(strip_whitespace=True)
    published_year: conint(ge=1800, le=CURRENT_YEAR)


class BookCreate(BookBase):
    author: constr(strip_whitespace=True, min_length=1)


class BookUpdate(BaseModel):
    title: Optional[constr(strip_whitespace=True, min_length=1)]
    genre: Optional[constr(strip_whitespace=True)]
    published_year: Optional[conint(ge=1800, le=CURRENT_YEAR)]
    author: Optional[constr(strip_whitespace=True, min_length=1)]


class BookRead(BaseModel):
    id: int
    title: str
    genre: str
    published_year: int
    author: AuthorRead

    model_config = {"from_attributes": True}


class UserCreate(BaseModel):
    username: constr(strip_whitespace=True, min_length=3)
    password: constr(min_length=6)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
