from __future__ import annotations

from typing import TYPE_CHECKING
from sqlalchemy import String
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from app.modelos.base import Base

if TYPE_CHECKING:
    from app.modelos.libro import Libro


class Autor(Base):
    __tablename__ = "autores"

    id_autor: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True
    )

    nombre: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    apellidos: Mapped[str] = mapped_column(
        String(150),
        nullable=False
    )

    # Relación 1 a N: Un autor posee múltiples libros
    libros: Mapped[list[Libro]] = relationship(
        back_populates="autor",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return (
            f"Autor("
            f"id_autor={self.id_autor!r}, "
            f"nombre={self.nombre!r}, "
            f"apellidos={self.apellidos!r}"
            f")"
        )
