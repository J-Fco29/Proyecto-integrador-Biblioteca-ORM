from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class DatosPrestamo:
    """DTO para la solicitud de registro de préstamo."""
    id_socio: int
    id_ejemplar: int
    dias_prestamo: int = 15


@dataclass(frozen=True)
class PrestamoResumen:
    """DTO para la visualización desacoplada de préstamos."""
    id_prestamo: int
    id_socio: int
    socio: str
    id_ejemplar: int
    codigo_ejemplar: str
    titulo_libro: str
    fecha_prestamo: date
    fecha_limite: date
    fecha_devolucion: date | None
    abierto: bool
