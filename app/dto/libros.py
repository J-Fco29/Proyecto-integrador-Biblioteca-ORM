from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class DatosLibro:
    """DTO para la creación o registro de un nuevo libro."""
    isbn: str
    titulo: str
    precio: Decimal
    id_autor: int
    observaciones: str | None = None


@dataclass(frozen=True)
class LibroResumen:
    """DTO para la visualización y consulta desacoplada de libros."""
    id_libro: int
    titulo: str
    autor: str
    precio: Decimal
    isbn: str = ""
    activo: bool = True
    observaciones: str | None = None


@dataclass(frozen=True)
class FiltroLibros:
    """DTO de parámetros de búsqueda dinámica y paginación para el catálogo."""
    texto: str | None = None
    precio_minimo: Decimal | None = None
    precio_maximo: Decimal | None = None
    id_autor: int | None = None
    solo_activos: bool = True
    pagina: int = 1
    tamano: int = 10
