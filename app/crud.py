from sqlalchemy.orm import Session
import models, schemas

# Функция для создания (Create) нового СМС в базе
def create_sms(db: Session, sms: schemas.SmsCreate):
    # Создаем объект модели SQLAlchemy из данных Pydantic
    db_sms = models.SMS(sender=sms.sender, text=sms.text)
    db.add(db_sms)    # Добавляем в сессию
    db.commit()       # Сохраняем изменения в БД
    db.refresh(db_sms) # Обновляем объект, чтобы получить id из БД
    return db_sms

# Функция для получения (Read) списка СМС
def get_sms_list(db: Session, skip: int = 0, limit: int = 100):
    # Запрашиваем из БД, сортируем по дате (сначала новые), пропускаем и ограничиваем количество
    return db.query(models.SMS).order_by(models.SMS.received_at.desc()).offset(skip).limit(limit).all()
