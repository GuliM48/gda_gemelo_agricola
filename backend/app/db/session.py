import os
from urllib.parse import quote_plus
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.base_class import Base
from config.settings import CONFIG_DB

_safe_password = quote_plus(str(CONFIG_DB.get("password", "")))

SQLALCHEMY_DATABASE_URL = (
    f"postgresql+psycopg2://{CONFIG_DB.get('user', 'postgres')}:{_safe_password}"
    f"@{CONFIG_DB.get('host', 'localhost')}:{CONFIG_DB.get('port', 5432)}/{CONFIG_DB.get('database', 'gda_gemelo')}"
)

# Intentar conectar con PostgreSQL; si no está disponible, usar SQLite local
try:
    _test_engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        pool_pre_ping=True,
        connect_args={"connect_timeout": 2},
    )
    with _test_engine.connect() as _conn:
        pass
    engine = create_engine(SQLALCHEMY_DATABASE_URL, pool_pre_ping=True, pool_size=10, max_overflow=20)
except Exception:
    import logging
    from config.settings import RUTA_DATOS
    RUTA_DATOS.mkdir(exist_ok=True)
    _sqlite_path = (RUTA_DATOS / "gda_gemelo.db").as_posix()
    logging.getLogger(__name__).info(f"PostgreSQL no disponible. Usando SQLite local: {_sqlite_path}")
    engine = create_engine(f"sqlite:///{_sqlite_path}", connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
