from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING
from sqlalchemy import Date
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from app.modelos.base import Base

if TYPE_CHECKING:
    from app.modelos.ejemplar import Ejemplar
    from app.modelos.socio import Socio


class DetallePrestamo(Base):
    __tablename__ = "detalle_prestamo"

    id_detalle: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True
    )

    id_prestamo: Mapped[int] = mapped_column(
        ForeignKey("prestamos.id_prestamo"),
        nullable=False
    )

    id_ejemplar: Mapped[int] = mapped_column(
        ForeignKey("ejemplares.id_ejemplar"),
        nullable=False
    )

    prestamo: Mapped[Prestamo] = relationship(
        back_populates="detalles",
        overlaps="prestamos,ejemplares"
    )

    ejemplar: Mapped[Ejemplar] = relationship(
        back_populates="detalles",
        overlaps="prestamos,ejemplares"
    )

    def __repr__(self) -> str:
        return (
            f"DetallePrestamo("
            f"id_detalle={self.id_detalle!r}, "
            f"id_prestamo={self.id_prestamo!r}, "
            f"id_ejemplar={self.id_ejemplar!r}"
            f")"
        )


class Prestamo(Base):
    __tablename__ = "prestamos"

    id_prestamo: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True
    )

    id_socio: Mapped[int] = mapped_column(
        ForeignKey("socios.id_socio"),
        nullable=False
    )

    fecha_prestamo: Mapped[date] = mapped_column(
        Date,
        default=date.today,
        nullable=False
    )

    fecha_limite: Mapped[date] = mapped_column(
        Date,
        nullable=False
    )

    fecha_devolucion: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        default=None
    )

    # Relación N a 1: Cada préstamo pertenece a un socio
    socio: Mapped[Socio] = relationship(
        back_populates="prestamos"
    )

    # Relación 1 a N con los detalles del préstamo
    detalles: Mapped[list[DetallePrestamo]] = relationship(
        back_populates="prestamo",
        cascade="all, delete-orphan",
        overlaps="ejemplares"
    )

    # Relación N a M directa: Colección de ejemplares incluidos en el préstamo
    ejemplares: Mapped[list[Ejemplar]] = relationship(
        secondary="detalle_prestamo",
        back_populates="prestamos",
        overlaps="detalles,ejemplar,prestamo"
    )

    def __repr__(self) -> str:
        return (
            f"Prestamo("
            f"id_prestamo={self.id_prestamo!r}, "
            f"id_socio={self.id_socio!r}, "
            f"fecha_prestamo={self.fecha_prestamo!r}, "
            f"fecha_limite={self.fecha_limite!r}, "
            f"fecha_devolucion={self.fecha_devolucion!r}"
            f")"
        )
