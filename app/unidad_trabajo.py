from __future__ import annotations

from typing import Any
from sqlalchemy.orm import Session
from sqlalchemy.orm import sessionmaker

from app.conexion import SessionLocal
from app.repositorios.autores import AutorRepositorio
from app.repositorios.ejemplares import EjemplarRepositorio
from app.repositorios.libros import LibroRepositorio
from app.repositorios.prestamos import PrestamoRepositorio
from app.repositorios.socios import SocioRepositorio


class UnidadTrabajoSQLAlchemy:
    """
    Patrón Unit of Work (Unidad de Trabajo) implementado sobre SQLAlchemy.
    Coordina los repositorios compartiendo una única Session y encapsula
    el ciclo de vida de la transacción (commit / rollback / close).
    """

    def __init__(self, fabrica_sesiones: sessionmaker | None = None) -> None:
        self.fabrica_sesiones = fabrica_sesiones or SessionLocal
        self.session: Session | None = None
        self.autores: AutorRepositorio | None = None
        self.libros: LibroRepositorio | None = None
        self.socios: SocioRepositorio | None = None
        self.ejemplares: EjemplarRepositorio | None = None
        self.prestamos: PrestamoRepositorio | None = None
        self.confirmado: bool = False
        self.revertido: bool = False

    def __enter__(self) -> UnidadTrabajoSQLAlchemy:
        self.session = self.fabrica_sesiones()
        self.autores = AutorRepositorio(self.session)
        self.libros = LibroRepositorio(self.session)
        self.socios = SocioRepositorio(self.session)
        self.ejemplares = EjemplarRepositorio(self.session)
        self.prestamos = PrestamoRepositorio(self.session)
        self.confirmado = False
        self.revertido = False
        return self

    def __exit__(
        self,
        tipo_error: type[BaseException] | None,
        error: BaseException | None,
        traceback: Any
    ) -> None:
        try:
            if error is not None:
                self.rollback()
        finally:
            if self.session is not None:
                self.session.close()

    def flush(self) -> None:
        """Sincroniza los cambios en memoria con la base de datos sin confirmar la transacción."""
        if self.session is not None:
            self.session.flush()

    def commit(self) -> None:
        """Confirma de forma atómica todas las operaciones realizadas durante la transacción."""
        if self.session is not None:
            self.session.commit()
            self.confirmado = True

    def rollback(self) -> None:
        """Revierte cualquier modificación pendiente devolviendo la base de datos a su estado previo."""
        if self.session is not None:
            self.session.rollback()
            self.revertido = True


# Aliases para compatibilidad amplia
UnitOfWorkSQLAlchemy = UnidadTrabajoSQLAlchemy
UnidadTrabajo = UnidadTrabajoSQLAlchemy
