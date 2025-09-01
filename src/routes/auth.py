from fastapi import Request

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi.security import OAuth2PasswordRequestForm

from ..utils.limiter import limiter
from ..database import get_async_session
from .. import schemas, models, auth
from sqlalchemy import select

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post('/register', response_model=schemas.Token)
@limiter.limit("5/minute")
async def register(request: Request, user_in: schemas.UserCreate, db: AsyncSession = Depends(get_async_session)):
    q = select(models.User).where(models.User.username == user_in.username)
    res = await db.execute(q)
    if res.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Username already registered")
    user = models.User(username=user_in.username, hashed_password=auth.get_password_hash(user_in.password))
    db.add(user)
    await db.commit()
    await db.refresh(user)
    access_token = auth.create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}




@router.post('/token', response_model=schemas.Token)
@limiter.limit("5/minute")
async def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_async_session)):
    user = await auth.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")
    token = auth.create_access_token(data={"sub": user.username})
    return {"access_token": token, "token_type": "bearer"}
