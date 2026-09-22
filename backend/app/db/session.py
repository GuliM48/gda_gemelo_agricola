import os
from urllib.parse import quote_plus
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.base_class import Base
from config.settings import CONFIG_DB

_safe_password = quote_plus(str(CONFIG_DB["password"]))

SQLALCHEMY_DATABASE_URL = (
    f"postgresql+psycopg2://{CONFIG_DB['user']}:{_safe_password}"
    f"@{CONFIG_DB['host']}:{CONFIG_DB['port']}/{CONFIG_DB['database']}"
)

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
