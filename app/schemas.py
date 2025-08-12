from pydantic import BaseModel
import datetime

# Базовая схема, описывающая основные поля СМС
class SmsBase(BaseModel):
    sender: str
    text: str

# Схема для создания нового СМС (то, что мы ждем от телефона)
class SmsCreate(SmsBase):
    pass

# Схема для отображения СМС (то, что мы отдаем на сайт)
# Включает поля, которые генерирует сама база данных (id, received_at)
class Sms(SmsBase):
    id: int
    received_at: datetime.datetime

    # Позволяет Pydantic работать с объектами SQLAlchemy напрямую
class Config:
    from_attributes = True

