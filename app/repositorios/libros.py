from decimal import Decimal
from sqlalchemy import func
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload

from app.dto.libros import FiltroLibros
from app.modelos.libro import Libro


class LibroRepositorio:
    """Repositorio para la gestión de libros en base de datos mediante SQLAlchemy."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def buscar(self, id_libro: int) -> Libro | None:
        return self.session.get(Libro, id_libro)

    def buscar_por_id(self, id_libro: int) -> Libro | None:
        return self.buscar(id_libro)

    def buscar_por_isbn(self, isbn: str) -> Libro | None:
        sentencia = select(Libro).where(Libro.isbn == isbn.strip())
        return self.session.scalars(sentencia).first()

    def añadir(self, libro: Libro) -> None:
        self.session.add(libro)

    def eliminar(self, libro: Libro) -> None:
        self.session.delete(libro)

    def listar_todos(self, precargar_autor: bool = True) -> list[Libro]:
        sentencia = select(Libro).order_by(Libro.titulo)
        if precargar_autor:
            sentencia = sentencia.options(joinedload(Libro.autor))
        return list(self.session.scalars(sentencia).all())

    def buscar_por_titulo(self, texto: str) -> list[Libro]:
        sentencia = (
            select(Libro)
            .options(joinedload(Libro.autor))
            .where(Libro.titulo.ilike(f"%{texto}%"))
            .order_by(Libro.titulo)
        )
        return list(self.session.scalars(sentencia).all())

    def buscar_por_precio(self, precio_minimo: Decimal, precio_maximo: Decimal) -> list[Libro]:
        sentencia = (
            select(Libro)
            .options(joinedload(Libro.autor))
            .where(Libro.precio >= precio_minimo, Libro.precio <= precio_maximo)
            .order_by(Libro.precio, Libro.titulo)
        )
        return list(self.session.scalars(sentencia).all())

    def listar_con_filtro(self, filtro: FiltroLibros) -> list[Libro]:
        """
        Construye dinámicamente la consulta añadiendo solo las condiciones que tengan valor.
        Aplica paginación segura y precarga ansiosa para evitar N+1.
        """
        sentencia = select(Libro).options(joinedload(Libro.autor))

        if filtro.solo_activos:
            sentencia = sentencia.where(Libro.activo.is_(True))

        if filtro.texto and filtro.texto.strip():
            texto_limpio = f"%{filtro.texto.strip()}%"
            sentencia = sentencia.where(Libro.titulo.ilike(texto_limpio))

        if filtro.precio_minimo is not None:
            sentencia = sentencia.where(Libro.precio >= filtro.precio_minimo)

        if filtro.precio_maximo is not None:
            sentencia = sentencia.where(Libro.precio <= filtro.precio_maximo)

        if filtro.id_autor is not None:
            sentencia = sentencia.where(Libro.id_autor == filtro.id_autor)

        pagina = max(1, filtro.pagina)
        tamano = max(1, min(filtro.tamano, 100))
        desplazamiento = (pagina - 1) * tamano

        sentencia = sentencia.order_by(Libro.id_libro).limit(tamano).offset(desplazamiento)
        return list(self.session.scalars(sentencia).all())

    def contar_con_filtro(self, filtro: FiltroLibros) -> int:
        """Devuelve el total de coincidencias para calcular la paginación."""
        sentencia = select(func.count(Libro.id_libro))

        if filtro.solo_activos:
            sentencia = sentencia.where(Libro.activo.is_(True))

        if filtro.texto and filtro.texto.strip():
            texto_limpio = f"%{filtro.texto.strip()}%"
            sentencia = sentencia.where(Libro.titulo.ilike(texto_limpio))

        if filtro.precio_minimo is not None:
            sentencia = sentencia.where(Libro.precio >= filtro.precio_minimo)

        if filtro.precio_maximo is not None:
            sentencia = sentencia.where(Libro.precio <= filtro.precio_maximo)

        if filtro.id_autor is not None:
            sentencia = sentencia.where(Libro.id_autor == filtro.id_autor)

        return int(self.session.scalar(sentencia) or 0)


# Compatibilidad de nombres para fixtures y pruebas de integración
SQLAlchemyLibroRepositorio = LibroRepositorio
