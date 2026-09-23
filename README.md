# 📋 Todo + Reminder App — Version 1 (Local)

A full-stack **Todo + Reminder** application built with **FastAPI** (backend) and vanilla **HTML/CSS/JS** (frontend), using **SQLite** as the database.

---

## 🗂️ Project Structure

```
version1/
│
├── backend/
│   ├── main.py           ← FastAPI app + all API routes
│   ├── database.py       ← SQLAlchemy engine & session setup
│   ├── models.py         ← SQLAlchemy ORM models (Todo table)
│   ├── schemas.py        ← Pydantic request/response schemas
│   └── requirements.txt  ← Python dependencies
│
├── frontend/
│   ├── index.html        ← Main HTML page
│   ├── style.css         ← Styling
│   └── app.js            ← Frontend logic (fetch API calls)
│
└── README.md             ← This file
```

---

## 🚀 Getting Started

### 1. Create & activate a virtual environment

```powershell
cd version1
python -m venv venv
.\venv\Scripts\activate
```

### 2. Install dependencies

```powershell
pip install -r backend/requirements.txt
```

### 3. Start the API server

```powershell
uvicorn backend.main:app --reload
```

The API will be available at **http://127.0.0.1:8000**

### 4. Open the frontend

Simply open `frontend/index.html` in your browser **OR** navigate to http://127.0.0.1:8000/docs for the interactive Swagger UI.

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Health check |
| GET | `/health` | Status + timestamp |
| POST | `/todos` | Create a new todo |
| GET | `/todos` | List all todos (filter by `?completed=true/false`) |
| GET | `/todos/{id}` | Get a single todo |
| PUT | `/todos/{id}` | Update a todo |
| DELETE | `/todos/{id}` | Delete a todo |
| PATCH | `/todos/{id}/complete` | Toggle completed status |
| GET | `/reminders/due` | Get all overdue/today todos |

---

## 🗺️ Roadmap

- **Version 1** ✅ — Local app with SQLite
- **Version 2** — User accounts (register/login, JWT auth)
- **Version 3** — Real notifications (browser push + email)
- **Version 4** — Deploy to Render + PostgreSQL
