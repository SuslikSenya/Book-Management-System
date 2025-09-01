import uvicorn
from fastapi import FastAPI
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from .utils.limiter import limiter
from .database import engine
from .models import Base
from .routes.auth import router as operations_auth
from .routes.books import router as operations_books


app = FastAPI(
    title='Book Management System'
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.include_router(operations_auth)
app.include_router(operations_books)

@app.on_event('startup')
async def on_startup():
    # optionally create tables in dev (use alembic in prod)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


if __name__ == '__main__':
    uvicorn.run(app, host="127.0.0.1", port=8000)
