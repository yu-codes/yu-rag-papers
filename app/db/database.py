# app/db/database.py
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.environ["DATABASE_URL"]  # 若沒有會直接 KeyError

# echo=True 可印 SQL 方便除錯，正式環境請關掉
engine = create_engine(DATABASE_URL, pool_pre_ping=True, echo=False)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

Base = declarative_base()


def init_db() -> None:
    """在 APP 啟動時呼叫，確保資料表存在。"""
    import app.db.models  # noqa: F401 – 讓 Base 掃到 model 定義

    Base.metadata.create_all(bind=engine)
