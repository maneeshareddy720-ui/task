
# Task Manager API (FastAPI + SQLAlchemy + JWT)

A minimal Task Manager REST API with **authentication (JWT)**, **CRUD**, **validation**, and a **SQLite** database (via SQLAlchemy 2.0). Ship it locally the Uvicorn.

## Features
- Users: register, login (JWT), get profile
- Tasks: create, read (single/list + pagination + filter by status), update, delete
- Ownership & authorization: users see their own tasks; admins can see all
- SQLite by default; switch DB via `DATABASE_URL`
- OpenAPI docs at `/docs` (Swagger) and `/redoc`

## Tech
- FastAPI, Uvicorn
- SQLAlchemy 2.0 (ORM)
- Pydantic v2
- PyJWT (tokens), passlib (password hashing)

## Project layout
```
task-manager/
├─ requirements.txt
├─ .gitignore
└─ app/
      ├─ init.py
      ├─ database.py
      ├─ models.py
      ├─ schemas.py
      ├─ auth.py
      └─ main.py
```

## Prerequisites
```
- Python **3.10+**
- Git
```
## Quick start (local)

### Windows PowerShell
```powershell
cd task-manager
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt

# run
python -m uvicorn app.main:app --reload
```

### MacOS/Linux
```terminal
cd task-manager
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# run
uvicorn app.main:app --reload
```
### Open from here 
```http://127.0.0.1:8000/docs```


<img width="1920" height="1200" alt="image" src="https://github.com/user-attachments/assets/ea49d6a3-e125-4bdf-96fc-83758e26ed55" />


