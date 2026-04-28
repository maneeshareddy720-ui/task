from fastapi import FastAPI, Depends, HTTPException, Query, Path
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from .database import Base, engine, get_db
from . import models, schemas
from .auth import (
    hash_password, verify_password, create_access_token,
    get_current_user, require_role
)

app = FastAPI(title="Task Manager API")

@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)

@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse("/docs")

# ---------------- AUTH ----------------
@app.post("/auth/register", response_model=schemas.UserOut, status_code=201)
def register(payload: schemas.UserCreate, db: Session = Depends(get_db)):
    dup = db.execute(
        select(models.User).where(
            (models.User.username == payload.username) | (models.User.email == payload.email)
        )
    ).scalar_one_or_none()
    if dup:
        raise HTTPException(status_code=409, detail="Username or email already exists")
    user = models.User(
        username=payload.username,
        email=payload.email,
        password_hash=hash_password(payload.password),
        role="user",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@app.post("/auth/login", response_model=schemas.Token)
def login(username: str, password: str, db: Session = Depends(get_db)):
    user = db.execute(
        select(models.User).where(models.User.username == username)
    ).scalar_one_or_none()
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token({"sub": str(user.id)})
    return {"access_token": token, "token_type": "bearer"}

@app.get("/auth/me", response_model=schemas.UserOut)
def me(user: models.User = Depends(get_current_user)):
    return user

# ---------------- TASKS ----------------
@app.post("/tasks", response_model=schemas.TaskOut, status_code=201)
def create_task(
    payload: schemas.TaskCreate,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    task = models.Task(
        title=payload.title,
        description=payload.description or "",
        status=payload.status,
        priority=payload.priority,
        due_date=payload.due_date,
        owner_id=user.id,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task

@app.get("/tasks", response_model=schemas.PaginatedTasks)
def list_tasks(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    status: schemas.TaskStatus | None = Query(None),
    mine: bool = Query(True, description="If true, only your tasks; admin can set false to see all"),
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    stmt = select(models.Task)
    count_stmt = select(func.count(models.Task.id))

    if mine or user.role != "admin":
        stmt = stmt.where(models.Task.owner_id == user.id)
        count_stmt = count_stmt.where(models.Task.owner_id == user.id)
    if status is not None:
        stmt = stmt.where(models.Task.status == status)
        count_stmt = count_stmt.where(models.Task.status == status)

    total = db.execute(count_stmt).scalar_one()
    items = db.execute(stmt.offset(skip).limit(limit)).scalars().all()
    return {"items": items, "total": total, "skip": skip, "limit": limit}

@app.get("/tasks/{task_id}", response_model=schemas.TaskOut)
def get_task(
    task_id: int = Path(..., ge=1),
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    task = db.get(models.Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if user.role != "admin" and task.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Not allowed")
    return task

@app.put("/tasks/{task_id}", response_model=schemas.TaskOut)
def update_task(
    task_id: int,
    payload: schemas.TaskUpdate,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    task = db.get(models.Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if user.role != "admin" and task.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Not allowed")

    task.title = payload.title
    task.description = payload.description or ""
    task.status = payload.status
    task.priority = payload.priority
    task.due_date = payload.due_date
    db.commit()
    db.refresh(task)
    return task

@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    task = db.get(models.Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if user.role != "admin" and task.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Not allowed")
    db.delete(task)
    db.commit()
    return None

# Admin-only example
@app.get("/users", response_model=list[schemas.UserOut])
def list_users(
    db: Session = Depends(get_db),
    _: models.User = Depends(require_role("admin")),
):
    return db.execute(select(models.User)).scalars().all()
