from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload

from app.modelos.ejemplar import Ejemplar


class EjemplarRepositorio:
    """Repositorio para la gestión de ejemplares físicos."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def buscar(self, id_ejemplar: int) -> Ejemplar | None:
        return self.session.get(Ejemplar, id_ejemplar)

    def buscar_por_id(self, id_ejemplar: int) -> Ejemplar | None:
        return self.buscar(id_ejemplar)

    def buscar_por_codigo(self, codigo_inventario: str) -> Ejemplar | None:
        sentencia = select(Ejemplar).where(
            Ejemplar.codigo_inventario == codigo_inventario.strip()
        )
        return self.session.scalars(sentencia).first()

    def añadir(self, ejemplar: Ejemplar) -> None:
        self.session.add(ejemplar)

    def listar_por_libro(self, id_libro: int) -> list[Ejemplar]:
        sentencia = (
            select(Ejemplar)
            .where(Ejemplar.id_libro == id_libro)
            .order_by(Ejemplar.id_ejemplar)
        )
        return list(self.session.scalars(sentencia).all())

    def listar_todos(self) -> list[Ejemplar]:
        sentencia = (
            select(Ejemplar)
            .options(joinedload(Ejemplar.libro))
            .order_by(Ejemplar.codigo_inventario)
        )
        return list(self.session.scalars(sentencia).all())

    def eliminar(self, ejemplar: Ejemplar) -> None:
        self.session.delete(ejemplar)
