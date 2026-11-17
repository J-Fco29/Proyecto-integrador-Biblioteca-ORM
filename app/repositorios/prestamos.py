from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload
from sqlalchemy.orm import selectinload

from app.modelos.prestamo import Prestamo


class PrestamoRepositorio:
    """Repositorio para la gestión de préstamos y su carga optimizada."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def buscar(self, id_prestamo: int) -> Prestamo | None:
        sentencia = (
            select(Prestamo)
            .options(
                joinedload(Prestamo.socio),
                selectinload(Prestamo.ejemplares),
                selectinload(Prestamo.detalles)
            )
            .where(Prestamo.id_prestamo == id_prestamo)
        )
        return self.session.scalars(sentencia).first()

    def buscar_por_id(self, id_prestamo: int) -> Prestamo | None:
        return self.buscar(id_prestamo)

    def añadir(self, prestamo: Prestamo) -> None:
        self.session.add(prestamo)

    def listar_abiertos(self) -> list[Prestamo]:
        sentencia = (
            select(Prestamo)
            .options(
                joinedload(Prestamo.socio),
                selectinload(Prestamo.ejemplares),
                selectinload(Prestamo.detalles)
            )
            .where(Prestamo.fecha_devolucion.is_(None))
            .order_by(Prestamo.fecha_prestamo.desc())
        )
        return list(self.session.scalars(sentencia).all())

    def listar_todos(self) -> list[Prestamo]:
        sentencia = (
            select(Prestamo)
            .options(
                joinedload(Prestamo.socio),
                selectinload(Prestamo.ejemplares),
                selectinload(Prestamo.detalles)
            )
            .order_by(Prestamo.fecha_prestamo.desc())
        )
        return list(self.session.scalars(sentencia).all())

    def eliminar(self, prestamo: Prestamo) -> None:
        self.session.delete(prestamo)
