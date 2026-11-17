from __future__ import annotations

from typing import TYPE_CHECKING
from sqlalchemy import ForeignKey
from sqlalchemy import String
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from app.modelos.base import Base

if TYPE_CHECKING:
    from app.modelos.libro import Libro
    from app.modelos.prestamo import DetallePrestamo
    from app.modelos.prestamo import Prestamo


class Ejemplar(Base):
    __tablename__ = "ejemplares"

    id_ejemplar: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True
    )

    codigo_inventario: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False
    )

    id_libro: Mapped[int] = mapped_column(
        ForeignKey("libros.id_libro"),
        nullable=False
    )

    ubicacion: Mapped[str] = mapped_column(
        String(100),
        default="Planta Principal",
        nullable=False
    )

    estado: Mapped[str] = mapped_column(
        String(50),
        default="DISPONIBLE",
        nullable=False
    )

    # Relación N a 1: Cada ejemplar físico corresponde a un Libro del catálogo
    libro: Mapped[Libro] = relationship(
        back_populates="ejemplares"
    )

    # Relación N a M directa a través de la tabla intermedia
    prestamos: Mapped[list[Prestamo]] = relationship(
        secondary="detalle_prestamo",
        back_populates="ejemplares",
        overlaps="detalles"
    )

    # Relación con la entidad asociativa
    detalles: Mapped[list[DetallePrestamo]] = relationship(
        back_populates="ejemplar",
        cascade="all, delete-orphan",
        overlaps="prestamos"
    )

    def __repr__(self) -> str:
        return (
            f"Ejemplar("
            f"id_ejemplar={self.id_ejemplar!r}, "
            f"codigo={self.codigo_inventario!r}, "
            f"estado={self.estado!r}"
            f")"
        )
