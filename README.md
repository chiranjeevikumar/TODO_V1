# 📋 Todo + Reminder App — Version 1

A modern, full-stack **Todo + Reminder** web application built with **FastAPI** (Python backend) and vanilla **HTML5 / CSS3 / JavaScript** (frontend), featuring **SQLite / PostgreSQL** support, **Vercel Serverless deployment**, and **automated Gmail reminder email alerts**.

---

## ✨ Features

- **Todo Management**: Create, view, filter (All / Pending / Due Today / Completed), mark complete, and delete tasks.
- **Smart Reminders**: Set due dates and exact reminder times. Overdue tasks are highlighted automatically.
- **📧 Gmail Email Alerts**: Dispatches automated email alerts via Gmail SMTP when tasks reach their reminder time or become overdue.
  - Urgent red template for overdue tasks ("Action Required / Please complete ASAP").
  - Clean alert template for scheduled reminder times.
  - Prevents duplicate alerts via `email_sent` state tracking.
- **Dual Deployment**:
  - **Local Development**: Runs with FastAPI + SQLite and serves frontend directly at `http://127.0.0.1:8000`.
  - **Production on Vercel**: Fully serverless architecture with `@vercel/python` and `@vercel/static`.

---

## 🗂️ Project Structure

```text
version1/
│
├── api/
│   └── index.py          ← Vercel serverless entry point
│
├── backend/
│   ├── main.py           ← FastAPI application, middleware, and routes
│   ├── email_service.py  ← Gmail SMTP email delivery engine
│   ├── database.py       ← SQLAlchemy engine & session setup (SQLite / PostgreSQL)
│   ├── models.py         ← SQLAlchemy models (Todo table with email_sent tracking)
│   ├── schemas.py        ← Pydantic request and response schemas
│   └── requirements.txt  ← Python dependencies
│
├── frontend/
│   ├── index.html        ← Modern UI layout with reminder modal & email status badge
│   ├── style.css         ← Glassmorphic styling, animations, and responsive layout
│   └── app.js            ← Frontend logic, polling engine, and toast notifications
│
├── vercel.json           ← Vercel deployment routing & daily cron config
├── requirements.txt      ← Root requirements for Vercel Python runtime
├── .env.example          ← Template for Gmail and database credentials
└── README.md             ← Project documentation
```

---

## 🚀 Local Quickstart

### 1. Clone & Setup Virtual Environment

```powershell
git clone https://github.com/chiranjeevikumar/TODO_V1.git
cd TODO_V1
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Copy `.env.example` to `.env`:

```ini
GMAIL_USER=your_email@gmail.com
GMAIL_APP_PASSWORD=your_16_char_app_password
NOTIFICATION_EMAIL=recipient_email@gmail.com
```

> **Note**: Generate a 16-character App Password via **Google Account → Security → 2-Step Verification → App Passwords**.

### 3. Run the App

```powershell
uvicorn backend.main:app --reload --port 8000
```

Open your browser to:
- **Web App**: [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **Interactive Swagger Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## 🌐 Deploy to Vercel

The project is pre-configured for Vercel with GitHub integration.

1. Push your repository to GitHub.
2. In the [Vercel Dashboard](https://vercel.com) or via CLI (`vercel git connect`), link your repository.
3. Add the following **Environment Variables** in Vercel Project Settings:
   - `GMAIL_USER`
   - `GMAIL_APP_PASSWORD`
   - `NOTIFICATION_EMAIL`
   - *(Optional)* `DATABASE_URL` (for PostgreSQL / Neon persistence)
4. Deploy! Vercel will automatically build the static frontend and serverless Python function.

---

## 📡 API Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/health` | Health check & server timestamp |
| `GET` | `/todos` | List todos (filter with `?completed=true/false`) |
| `POST` | `/todos` | Create a new task (`title`, `description`, `due_date`, `reminder_time`) |
| `GET` | `/todos/{id}` | Get single task by ID |
| `PUT` | `/todos/{id}` | Update task details |
| `DELETE` | `/todos/{id}` | Delete task |
| `PATCH` | `/todos/{id}/complete` | Toggle task completion |
| `GET` | `/reminders/due` | Retrieve all pending tasks due today or overdue |
| `POST / GET` | `/reminders/send-emails` | Evaluates due/overdue tasks and sends Gmail alerts |
| `GET` | `/reminders/email-status` | Returns Gmail alert configuration status |
