import datetime
from sqlalchemy import Column, Integer, String, DateTime
from .database import Base

class SMS(Base):
    # Имя таблицы в базе данных
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    sender = Column(String, index=True)
    text = Column(String)
    received_at = Column(DateTime, default=datetime.datetime.utcnow)
