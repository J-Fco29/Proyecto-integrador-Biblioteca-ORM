from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING
from sqlalchemy import Boolean
from sqlalchemy import ForeignKey
from sqlalchemy import Numeric
from sqlalchemy import String
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from app.modelos.base import Base

if TYPE_CHECKING:
    from app.modelos.autor import Autor
    from app.modelos.ejemplar import Ejemplar


class Libro(Base):
    __tablename__ = "libros"

    id_libro: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True
    )

    isbn: Mapped[str] = mapped_column(
        String(30),
        unique=True,
        nullable=False
    )

    titulo: Mapped[str] = mapped_column(
        String(200),
        nullable=False
    )

    precio: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False
    )

    id_autor: Mapped[int] = mapped_column(
        ForeignKey("autores.id_autor"),
        nullable=False
    )

    activo: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )

    # Atributo añadido y versionado mediante migración Alembic
    observaciones: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True
    )

    # Relación N a 1: Cada libro pertenece a un autor
    autor: Mapped[Autor] = relationship(
        back_populates="libros"
    )

    # Relación 1 a N: Un libro posee múltiples copias físicas (ejemplares)
    ejemplares: Mapped[list[Ejemplar]] = relationship(
        back_populates="libro",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return (
            f"Libro("
            f"id_libro={self.id_libro!r}, "
            f"isbn={self.isbn!r}, "
            f"titulo={self.titulo!r}, "
            f"precio={self.precio!r}, "
            f"activo={self.activo!r}"
            f")"
        )
