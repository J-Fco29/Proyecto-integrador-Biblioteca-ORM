import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.configuracion import obtener_url_bd

try:
    engine = create_engine(
        obtener_url_bd(),
        echo=os.getenv("SQL_ECHO", "false").lower() in ("true", "1")
    )
except Exception:
    # Fallback seguro para entornos sin motor PostgreSQL activo
    engine = create_engine("sqlite:///biblioteca.db", echo=False)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False
)
