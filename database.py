import os
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, Integer, String, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

from config import Config

os.makedirs("logs", exist_ok=True)

engine = create_engine(Config.DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


class Chat(Base):
    """Модель чата пользователя"""
    __tablename__ = 'chats'

    chat_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    chat_type: Mapped[str] = mapped_column(String, nullable=False)
    city: Mapped[str] = mapped_column(String, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    def __repr__(self) -> str:
        return f"Chat(chat_id={self.chat_id}, chat_type='{self.chat_type}', city='{self.city}')"


def log_exception(e: Exception) -> None:
    """Логирует исключение в файл"""
    now = datetime.now()
    filename = f"logs/error_{now.strftime('%Y-%m-%d_%H-%M-%S')}.log"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(f"=== Ошибка при работе с базой ===\n\n{str(e)}\n")


def save_chat(chat_id: int, chat_type: str, city: str = "Москва") -> bool:
    """Сохраняет или обновляет чат в базе данных"""
    try:
        with SessionLocal() as session:
            chat = Chat(chat_id=chat_id, chat_type=chat_type, city=city)
            session.merge(chat)
            session.commit()
            return True
    except Exception as e:
        log_exception(e)
        return False


def update_city(chat_id: int, city_name: str) -> bool:
    """Обновляет город для указанного чата"""
    try:
        with SessionLocal() as session:
            stmt = select(Chat).where(Chat.chat_id == chat_id)
            chat = session.execute(stmt).scalar_one_or_none()
            if chat is None:
                return False
            chat.city = city_name
            session.commit()
            return True
    except Exception as e:
        log_exception(e)
        return False


def is_active_chat(chat_id: int) -> bool:
    """Проверяет, активен ли чат"""
    with SessionLocal() as session:
        stmt = select(Chat).where(Chat.chat_id == chat_id, Chat.is_active == True)
        result = session.execute(stmt).scalar_one_or_none()
        return result is not None


def deactivate_chat(chat_id: int) -> bool:
    """Деактивирует чат"""
    try:
        with SessionLocal() as session:
            stmt = select(Chat).where(Chat.chat_id == chat_id)
            chat = session.execute(stmt).scalar_one_or_none()
            if chat:
                chat.is_active = False
                session.commit()
                return True
            return False
    except Exception as e:
        log_exception(e)
        return False


if __name__ == '__main__':
    Base.metadata.create_all(engine)
