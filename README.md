# BookHaven — Full Stack Online Bookstore Application

BookHaven is a full-stack, enterprise-grade online bookstore web application featuring a **FastAPI** backend REST API, **PostgreSQL** database with **Alembic** migrations, **LangChain & ChromaDB RAG AI Assistant**, and a modern **React + Vite** frontend.

---

## 🛠️ Technology Stack

- **Backend**: Python 3.12, FastAPI, SQLAlchemy 2.0 (Async), Alembic, Pydantic v2, Passlib (bcrypt), PyJWT
- **Database**: PostgreSQL 16
- **AI & RAG Architecture**: LangChain, ChromaDB, Sentence-Transformers
- **Frontend**: React 19, Vite, React Router DOM v7, Axios, Bootstrap 5, Chart.js, React Hook Form
- **Deployment & Containerization**: Docker, Docker Compose, Nginx

---

## 🔑 Environment Variables

Create a `.env` file in the root directory (refer to `.env.example`):

```env
# Database Settings
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=task2_db
DATABASE_USER=postgres
DATABASE_PASS=postgres

# Security & JWT Tokens
SECRET_KEY=super_secret_jwt_access_token_key_change_in_production
REFRESH_SECRET_KEY=super_secret_jwt_refresh_token_key_change_in_production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Admin Credentials
ADMIN_USERNAME=admin
ADMIN_EMAIL=admin@bookstore.com
ADMIN_PASSWORD=AdminPassword123!
```

Create a `frontend/.env` file:

```env
VITE_API_URL=/api/v1
```

---

## ⚙️ Local Development Setup

### 1. Prerequisites
- Python 3.12+
- Node.js 20+
- PostgreSQL 16

### 2. Running Backend (FastAPI)

```bash
# Create Python virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run Alembic Database Migrations
alembic upgrade head

# Seed Initial Database Records & Admin User
python seed.py

# Start FastAPI Uvicorn Development Server
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

FastAPI Swagger API Documentation: [http://localhost:8000/docs](http://localhost:8000/docs)

### 3. Running Frontend (React + Vite)

```bash
cd frontend

# Install Node dependencies
npm install

# Start Vite Development Server
npm run dev
```

React Web Application: [http://localhost:5173](http://localhost:5173)

---

## 🐳 Docker Deployment Commands

Run the entire application stack (PostgreSQL, FastAPI Backend, React Nginx Frontend) using Docker Compose:

```bash
# Build and start all containers in detached mode
docker-compose up --build -d

# View container logs
docker-compose logs -f

# Check container statuses
docker-compose ps

# Stop all containers
docker-compose down -v
```

App Access via Docker:
- **Frontend App**: [http://localhost](http://localhost)
- **Backend API**: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 🗄️ Database Migrations & Seeding

```bash
# Generate new Alembic migration script
alembic revision --autogenerate -m "Describe database changes"

# Apply pending migrations to database
alembic upgrade head

# Rollback last migration
alembic downgrade -1

# Seed admin account & initial book catalog
python seed.py
```

---

## 🏗️ Production Build

```bash
# Build frontend production bundle
cd frontend
npm run build

# Preview static production build locally
npm run preview
```

---

## 👤 Default Admin Credentials

- **Email**: `admin@bookstore.com`
- **Password**: `AdminPassword123!`
- **Admin Panel URL**: `/admin`
