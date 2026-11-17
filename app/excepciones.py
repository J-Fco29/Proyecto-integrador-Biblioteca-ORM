"""
Excepciones de dominio para la aplicación de Biblioteca ORM.
Aíslan las reglas de negocio de la capa de persistencia o presentación.
"""


class ErrorBiblioteca(Exception):
    """Excepción raíz para errores de la biblioteca."""


class SocioNoEncontrado(ErrorBiblioteca):
    """Se lanza cuando un socio no existe en el sistema."""
    def __init__(self, mensaje: str = "El socio especificado no existe.") -> None:
        super().__init__(mensaje)


class SocioInactivo(ErrorBiblioteca):
    """Se lanza cuando se intenta realizar una operación con un socio deshabilitado."""
    def __init__(self, mensaje: str = "El socio no se encuentra activo.") -> None:
        super().__init__(mensaje)


class EjemplarNoEncontrado(ErrorBiblioteca):
    """Se lanza cuando un ejemplar no existe en el catálogo físico."""
    def __init__(self, mensaje: str = "El ejemplar especificado no existe.") -> None:
        super().__init__(mensaje)


class EjemplarNoDisponible(ErrorBiblioteca):
    """Se lanza cuando el ejemplar ya está prestado, extraviado o en reparación."""
    def __init__(self, mensaje: str = "El ejemplar no está disponible para préstamo.") -> None:
        super().__init__(mensaje)


class PrestamoNoEncontrado(ErrorBiblioteca):
    """Se lanza cuando no existe el identificador de préstamo solicitado."""
    def __init__(self, mensaje: str = "El préstamo especificado no existe.") -> None:
        super().__init__(mensaje)


class PrestamoYaDevuelto(ErrorBiblioteca):
    """Se lanza al intentar devolver un préstamo que ya fue cerrado anteriormente."""
    def __init__(self, mensaje: str = "El préstamo ya fue devuelto previamente.") -> None:
        super().__init__(mensaje)


class AutorNoEncontrado(ErrorBiblioteca):
    """Se lanza cuando se hace referencia a un autor inexistente."""
    def __init__(self, mensaje: str = "El autor especificado no existe.") -> None:
        super().__init__(mensaje)


class LibroNoEncontrado(ErrorBiblioteca):
    """Se lanza cuando un libro no se encuentra en el catálogo."""
    def __init__(self, mensaje: str = "El libro especificado no existe.") -> None:
        super().__init__(mensaje)


class PrecioInvalido(ErrorBiblioteca, ValueError):
    """Se lanza cuando el precio asignado a un libro es menor o igual a cero."""
    def __init__(self, mensaje: str = "El precio debe ser un valor positivo mayor que cero.") -> None:
        super().__init__(mensaje)


class IsbnDuplicado(ErrorBiblioteca):
    """Se lanza cuando se intenta registrar un libro con un ISBN que ya existe."""
    def __init__(self, mensaje: str = "Ya existe un libro registrado con este ISBN.") -> None:
        super().__init__(mensaje)
