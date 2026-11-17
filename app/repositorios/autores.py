from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.orm import selectinload

from app.modelos.autor import Autor


class AutorRepositorio:
    """Repositorio para la persistencia y consulta de entidades Autor."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def buscar(self, id_autor: int) -> Autor | None:
        return self.session.get(Autor, id_autor)

    def buscar_por_id(self, id_autor: int) -> Autor | None:
        return self.buscar(id_autor)

    def añadir(self, autor: Autor) -> None:
        self.session.add(autor)

    def listar_todos(self, precargar_libros: bool = False) -> list[Autor]:
        sentencia = select(Autor).order_by(Autor.apellidos, Autor.nombre)
        if precargar_libros:
            sentencia = sentencia.options(selectinload(Autor.libros))
        return list(self.session.scalars(sentencia).all())

    def eliminar(self, autor: Autor) -> None:
        self.session.delete(autor)
