import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.configuracion import obtener_url_bd

try:
    engine = create_engine(
        obtener_url_bd(),
        echo=os.getenv("SQL_ECHO", "false").lower() in ("true", "1")
    )
    with engine.connect():
        pass
except Exception:
    # Si PostgreSQL no está activo o accesible, fallback inmediato a SQLite local
    engine = create_engine(
        "sqlite:///biblioteca.db",
        echo=os.getenv("SQL_ECHO", "false").lower() in ("true", "1")
    )

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False
)
