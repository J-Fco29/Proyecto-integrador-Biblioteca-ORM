from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modelos.socio import Socio


class SocioRepositorio:
    """Repositorio para la persistencia y consulta de socios."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def buscar(self, id_socio: int) -> Socio | None:
        return self.session.get(Socio, id_socio)

    def buscar_por_id(self, id_socio: int) -> Socio | None:
        return self.buscar(id_socio)

    def buscar_por_dni(self, dni: str) -> Socio | None:
        sentencia = select(Socio).where(Socio.dni == dni.strip())
        return self.session.scalars(sentencia).first()

    def añadir(self, socio: Socio) -> None:
        self.session.add(socio)

    def listar_todos(self) -> list[Socio]:
        sentencia = select(Socio).order_by(Socio.apellidos, Socio.nombre)
        return list(self.session.scalars(sentencia).all())

    def eliminar(self, socio: Socio) -> None:
        self.session.delete(socio)
