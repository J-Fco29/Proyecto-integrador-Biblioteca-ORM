from datetime import date
from datetime import timedelta
from typing import Any

from app.dto.prestamos import PrestamoResumen
from app.excepciones import EjemplarNoDisponible
from app.excepciones import EjemplarNoEncontrado
from app.excepciones import PrestamoNoEncontrado
from app.excepciones import PrestamoYaDevuelto
from app.excepciones import SocioInactivo
from app.excepciones import SocioNoEncontrado
from app.modelos.prestamo import DetallePrestamo
from app.modelos.prestamo import Prestamo


class PrestamoServicio:
    """
    Servicio de aplicación para la gestión de préstamos bibliotecarios.
    Asegura la atomicidad transaccional coordinando los repositorios mediante Unit of Work.
    """

    def __init__(self, unidad_trabajo: Any) -> None:
        self.unidad_trabajo = unidad_trabajo

    def registrar_prestamo(
        self,
        id_socio: int,
        id_ejemplar: int,
        dias_prestamo: int = 15
    ) -> int:
        """
        Registra un nuevo préstamo garantizando atomicidad y validaciones de negocio:
        1. Comprueba existencia del socio.
        2. Comprueba que el socio se encuentre activo.
        3. Comprueba existencia del ejemplar físico.
        4. Comprueba que el ejemplar esté 'DISPONIBLE'.
        5. Crea la entidad Prestamo.
        6. Asocia el ejemplar al préstamo (mediante relación y detalle).
        7. Cambia el estado del ejemplar a 'PRESTADO'.
        8. Confirma toda la operación en una única transacción atómica.
        """
        with self.unidad_trabajo as uow:
            socio = uow.socios.buscar(id_socio)
            if socio is None:
                raise SocioNoEncontrado(f"No existe el socio con identificador {id_socio}.")

            if not socio.activo:
                raise SocioInactivo(f"El socio {socio.nombre} {socio.apellidos} no está activo.")

            ejemplar = uow.ejemplares.buscar(id_ejemplar)
            if ejemplar is None:
                raise EjemplarNoEncontrado(f"No existe el ejemplar con identificador {id_ejemplar}.")

            if ejemplar.estado != "DISPONIBLE":
                raise EjemplarNoDisponible(
                    f"El ejemplar '{ejemplar.codigo_inventario}' no está disponible (estado: {ejemplar.estado})."
                )

            hoy = date.today()
            fecha_limite = hoy + timedelta(days=dias_prestamo)

            prestamo = Prestamo(
                id_socio=socio.id_socio,
                fecha_prestamo=hoy,
                fecha_limite=fecha_limite,
                fecha_devolucion=None
            )

            # Vinculación del ejemplar mediante la relación directa N:M
            if ejemplar not in prestamo.ejemplares:
                prestamo.ejemplares.append(ejemplar)

            # Actualización del estado físico del ejemplar
            ejemplar.estado = "PRESTADO"

            uow.prestamos.añadir(prestamo)
            uow.flush()

            id_generado = prestamo.id_prestamo
            uow.commit()

            return id_generado

    def devolver_prestamo(self, id_prestamo: int) -> bool:
        """
        Registra la devolución de un préstamo:
        1. Comprueba que el préstamo exista.
        2. Comprueba que no esté cerrado previamente.
        3. Registra la fecha de devolución actual.
        4. Cambia el estado de los ejemplares a 'DISPONIBLE'.
        5. Confirma todos los cambios en un único commit.
        """
        with self.unidad_trabajo as uow:
            prestamo = uow.prestamos.buscar(id_prestamo)
            if prestamo is None:
                raise PrestamoNoEncontrado(f"No existe el préstamo con identificador {id_prestamo}.")

            if prestamo.fecha_devolucion is not None:
                raise PrestamoYaDevuelto(
                    f"El préstamo {id_prestamo} ya fue devuelto en fecha {prestamo.fecha_devolucion}."
                )

            prestamo.fecha_devolucion = date.today()

            for ejemplar in prestamo.ejemplares:
                ejemplar.estado = "DISPONIBLE"

            uow.commit()
            return True

    def listar_prestamos_abiertos(self) -> list[PrestamoResumen]:
        """Devuelve todos los préstamos que aún no han sido devueltos."""
        with self.unidad_trabajo as uow:
            prestamos = uow.prestamos.listar_abiertos()
            resumenes: list[PrestamoResumen] = []
            for p in prestamos:
                nombre_socio = f"{p.socio.nombre} {p.socio.apellidos}".strip() if p.socio else "Desconocido"
                ejemplares_unicos = {e.id_ejemplar: e for e in p.ejemplares}.values()
                for e in ejemplares_unicos:
                    titulo_libro = e.libro.titulo if e.libro else "Sin título"
                    resumenes.append(
                        PrestamoResumen(
                            id_prestamo=p.id_prestamo,
                            id_socio=p.id_socio,
                            socio=nombre_socio,
                            id_ejemplar=e.id_ejemplar,
                            codigo_ejemplar=e.codigo_inventario,
                            titulo_libro=titulo_libro,
                            fecha_prestamo=p.fecha_prestamo,
                            fecha_limite=p.fecha_limite,
                            fecha_devolucion=p.fecha_devolucion,
                            abierto=(p.fecha_devolucion is None)
                        )
                    )
            return resumenes
