import secrets

import os
import datetime
import secrets
from typing import List

from fastapi import (
    FastAPI, Depends, Request, Header, HTTPException,
    WebSocket, WebSocketDisconnect
)
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from dotenv import load_dotenv

# Локальные импорты из вашего проекта
from . import crud, models, schemas
from .database import SessionLocal, engine

# -------------------- 1. ИНИЦИАЛИЗАЦИЯ И НАСТРОЙКА --------------------

# Создаем таблицы в БД (если их еще нет) при старте приложения
models.Base.metadata.create_all(bind=engine)

# Загружаем переменные из файла .env (или key.env)
# Если ваш файл называется key.env, используйте: load_dotenv(dotenv_path="key.env")
load_dotenv()
API_SECRET_KEY = os.getenv("API_SECRET_KEY")
SITE_USERNAME = os.getenv("SITE_USERNAME")
SITE_PASSWORD = os.getenv("SITE_PASSWORD")

# Проверяем, что секреты загружены (опционально, но полезно для отладки)
if not API_SECRET_KEY:
    print("!!! ВНИМАНИЕ: Секретный ключ API_SECRET_KEY не найден. API будет незащищенным. !!!")
if not (SITE_USERNAME and SITE_PASSWORD):
    print("!!! ВНИМАНИЕ: Логин/пароль для сайта не найдены. Аутентификация не будет работать. !!!")

# Создаем главный экземпляр приложения FastAPI
app = FastAPI(title="SMS Viewer")

# Создаем объект для HTTP Basic аутентификации
security = HTTPBasic()


# -------------------- 2. НАСТРОЙКА СТАТИКИ И ШАБЛОНОВ --------------------

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")


# -------------------- 3. МЕНЕДЖЕР WEBSOCKET СОЕДИНЕНИЙ --------------------

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()


# -------------------- 4. ЗАВИСИМОСТИ (DEPENDENCIES) --------------------

# Зависимость для получения сессии БД
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Зависимость для проверки API-ключа для эндпоинта /api/sms
async def verify_api_key(x_api_key: str = Header(None)):
    if not API_SECRET_KEY or x_api_key != API_SECRET_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")

# Зависимость для проверки логина/пароля для доступа к сайту
def verify_site_credentials(credentials: HTTPBasicCredentials = Depends(security)):
    is_username_correct = secrets.compare_digest(credentials.username, SITE_USERNAME or "")
    is_password_correct = secrets.compare_digest(credentials.password, SITE_PASSWORD or "")
    
    if not (is_username_correct and is_password_correct):
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


# -------------------- 5. ЭНДПОИНТЫ ПРИЛОЖЕНИЯ --------------------

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        print("Клиент отключился")


@app.post("/api/sms", response_model=schemas.Sms, dependencies=[Depends(verify_api_key)])
async def add_new_sms(sms: schemas.SmsCreate, db: Session = Depends(get_db)):
    """
    Принимает новое СМС, сохраняет в базу и транслирует через WebSocket.
    """
    db_sms = crud.create_sms(db=db, sms=sms)
    html_row = f"""
    <tr>
        <td class="timestamp">{db_sms.received_at.strftime('%Y-%m-%d %H:%M:%S')}</td>
        <td class="sender">{db_sms.sender}</td>
        <td class="text">{db_sms.text}</td>
    </tr>
    """
    await manager.broadcast(html_row)
    return db_sms


# Этот эндпоинт теперь защищен аутентификацией
@app.get("/", response_class=HTMLResponse, dependencies=[Depends(verify_site_credentials)])
def read_root(request: Request, db: Session = Depends(get_db)):
    """
    Отображает главную страницу со списком СМС.
    Доступ защищен HTTP Basic аутентификацией.
    """
    messages = crud.get_sms_list(db, limit=50) 
    return templates.TemplateResponse(
        "index.html", 
        {"request": request, "messages": messages}
    )

# Зависимость для проверки API-ключа для эндпоинта /api/sms
async def verify_api_key(x_api_key: str = Header(None)):
    print(f"--- DEBUG: Received 'x-api-key' header: '{x_api_key}'")
    print(f"--- DEBUG: Expected API_SECRET_KEY on server: '{API_SECRET_KEY}'")
    
    # Используем compare_digest для безопасного сравнения
    if not (API_SECRET_KEY and x_api_key and secrets.compare_digest(x_api_key, API_SECRET_KEY)):
        raise HTTPException(status_code=401, detail="Invalid API Key")