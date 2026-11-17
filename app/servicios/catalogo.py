from decimal import Decimal
from typing import Any

from app.dto.libros import DatosLibro
from app.dto.libros import FiltroLibros
from app.dto.libros import LibroResumen
from app.excepciones import AutorNoEncontrado
from app.excepciones import IsbnDuplicado
from app.excepciones import LibroNoEncontrado
from app.excepciones import PrecioInvalido
from app.modelos.libro import Libro


class CatalogoServicio:
    """
    Servicio de aplicación para la gestión del catálogo de libros.
    Centraliza las reglas de negocio de catálogo y transforma entidades ORM a DTOs.
    """

    def __init__(self, unidad_trabajo: Any) -> None:
        self.unidad_trabajo = unidad_trabajo

    def listar_catalogo(self) -> list[LibroResumen]:
        """Obtiene la lista completa de libros con sus autores mediante DTO."""
        with self.unidad_trabajo as uow:
            libros = uow.libros.listar_todos(precargar_autor=True)
            return [self._a_dto(libro) for libro in libros]

    def buscar_por_id(self, id_libro: int) -> LibroResumen | None:
        """Busca un libro por su identificador único."""
        with self.unidad_trabajo as uow:
            libro = uow.libros.buscar(id_libro)
            if libro is None:
                return None
            return self._a_dto(libro)

    def buscar_libro(self, id_libro: int) -> Libro | None:
        """Compatibilidad para inspección de entidad o pruebas directas."""
        with self.unidad_trabajo as uow:
            return uow.libros.buscar(id_libro)

    def buscar_con_filtro(
        self, filtro: FiltroLibros
    ) -> tuple[list[LibroResumen], int]:
        """Aplica filtros dinámicos y paginación, retornando la página de DTOs y el total."""
        with self.unidad_trabajo as uow:
            libros = uow.libros.listar_con_filtro(filtro)
            total = uow.libros.contar_con_filtro(filtro)
            return [self._a_dto(l) for l in libros], total

    def crear_libro(self, datos: DatosLibro) -> int:
        """
        Crea un nuevo libro aplicando validaciones de negocio:
        - ISBN y título no vacíos.
        - Precio estrictamente positivo.
        - Existencia del autor.
        - Unicidad del ISBN.
        """
        if not datos.isbn or not datos.isbn.strip():
            raise ValueError("El ISBN no puede estar vacío.")

        if not datos.titulo or not datos.titulo.strip():
            raise ValueError("El título no puede estar vacío.")

        if datos.precio <= Decimal("0"):
            raise PrecioInvalido("El precio debe ser un valor positivo mayor que cero.")

        with self.unidad_trabajo as uow:
            autor = uow.autores.buscar(datos.id_autor)
            if autor is None:
                raise AutorNoEncontrado(f"No existe el autor con identificador {datos.id_autor}.")

            existente = uow.libros.buscar_por_isbn(datos.isbn.strip())
            if existente is not None:
                raise IsbnDuplicado(f"Ya existe un libro registrado con el ISBN {datos.isbn.strip()}.")

            nuevo_libro = Libro(
                isbn=datos.isbn.strip(),
                titulo=datos.titulo.strip(),
                precio=datos.precio,
                id_autor=datos.id_autor,
                observaciones=datos.observaciones,
                activo=True
            )

            uow.libros.añadir(nuevo_libro)
            uow.flush()
            id_generado = nuevo_libro.id_libro
            uow.commit()

            return id_generado

    def cambiar_precio(self, id_libro: int, nuevo_precio: Decimal) -> bool:
        """Actualiza el precio de un libro (alias para compatibilidad con pruebas previas)."""
        return self.actualizar_precio(id_libro, nuevo_precio)

    def actualizar_precio(self, id_libro: int, nuevo_precio: Decimal) -> bool:
        """Actualiza el precio de un libro con validación y transacción atómica."""
        if nuevo_precio <= Decimal("0"):
            raise PrecioInvalido("El precio debe ser un valor positivo mayor que cero.")

        with self.unidad_trabajo as uow:
            libro = uow.libros.buscar(id_libro)
            if libro is None:
                return False

            libro.precio = nuevo_precio
            uow.commit()
            return True

    def desactivar_libro(self, id_libro: int) -> bool:
        """Realiza una eliminación lógica (soft delete) del libro."""
        with self.unidad_trabajo as uow:
            libro = uow.libros.buscar(id_libro)
            if libro is None:
                raise LibroNoEncontrado(f"No existe el libro con identificador {id_libro}.")

            libro.activo = False
            uow.commit()
            return True

    @staticmethod
    def _a_dto(libro: Libro) -> LibroResumen:
        nombre_autor = (
            f"{libro.autor.nombre} {libro.autor.apellidos}".strip()
            if libro.autor
            else "Autor no asignado"
        )
        return LibroResumen(
            id_libro=libro.id_libro,
            titulo=libro.titulo,
            autor=nombre_autor,
            precio=libro.precio,
            isbn=libro.isbn,
            activo=libro.activo,
            observaciones=libro.observaciones
        )
