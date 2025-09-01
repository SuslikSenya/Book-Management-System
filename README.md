# Book Management System

A feature-rich Book Management System built with **FastAPI**, **SQLAlchemy**, and **PostgreSQL/SQLite**. Supports user registration, login, CRUD operations on books, recommendations, CSV/JSON export, and rate-limiting.

---

## Features

- **User authentication & authorization**
  - Register new users
  - Login and token-based authentication (JWT)
- **Book management**
  - Create, read, update, delete books
  - Filter and sort books by title, author, genre, and year
- **Recommendations**
  - Suggest books by genre or author
- **Data import/export**
  - Bulk import books from CSV/JSON
  - Export books as CSV
- **Rate-limiting**
  - Prevent API abuse with configurable limits
- **Testing**
  - Unit and integration tests using `pytest` and `httpx`

---

## Tech Stack

- Python 3.12
- FastAPI
- SQLAlchemy (async)
- PostgreSQL or SQLite
- httpx (for async tests)
- pytest + pytest-asyncio

---

## Installation

1. **Clone repository**

```bash
git clone https://github.com/yourusername/book-management-system.git
cd book-management-system
```

2. **Create virtual environment & install dependencies**
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate     # Windows

pip install -r requirements.txt
```

3. **Set up environment variables**
```bash
export DATABASE_URL="postgresql+asyncpg://user:password@localhost:5432/dbname"
# or for Windows
set DATABASE_URL="postgresql+asyncpg://user:password@localhost:5432/dbname"
```

4. **Run database migrations (optional)**
```bash
alembic upgrade head
```
---

## Running the Application

```bash
uvicorn src.main:app --reload
```
- API will be available at http://127.0.0.1:8000
- Swagger UI: http://127.0.0.1:8000/docs

---

## API Endpoints

### Auth

- POST /auth/register - register a new user

- POST /auth/token - login, returns JWT token

### Books

- POST /books/ - create a book

- GET /books/ - list books (filters: title, author, genre, year_from, year_to)

- GET /books/{id} - get a book by ID

- PUT /books/{id} - update a book

- DELETE /books/{id} - delete a book

- POST /books/import - bulk import from CSV/JSON

- GET /books/export - export books to CSV

- GET /books/{id}/recommend - get book recommendations
---
## Testing
1. Run tests
```bash
pytest -v
```
2. Fixtures

- Uses an in-memory SQLite database for tests.

- AsyncClient from httpx for testing API endpoints.
---
## Notes

- Rate-limiting is enabled via slowapi.

- Use unique usernames in tests to avoid 400 Bad Request errors due to duplicate registration.

- Tables are auto-created on startup in development; production should use migrations.

---

## License

### MIT License

---

## Author

### https://github.com/SuslikSenya
