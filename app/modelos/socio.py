from __future__ import annotations

from typing import TYPE_CHECKING
from sqlalchemy import Boolean
from sqlalchemy import String
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from app.modelos.base import Base

if TYPE_CHECKING:
    from app.modelos.prestamo import Prestamo


class Socio(Base):
    __tablename__ = "socios"

    id_socio: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True
    )

    nombre: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    apellidos: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    email: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )

    telefono: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True
    )

    dni: Mapped[str | None] = mapped_column(
        String(20),
        unique=True,
        nullable=True
    )

    activo: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )

    # Relación 1 a N: Un socio realiza múltiples préstamos
    prestamos: Mapped[list[Prestamo]] = relationship(
        back_populates="socio"
    )

    def __repr__(self) -> str:
        return (
            f"Socio("
            f"id_socio={self.id_socio!r}, "
            f"nombre={self.nombre!r}, "
            f"apellidos={self.apellidos!r}, "
            f"activo={self.activo!r}"
            f")"
        )
