from datetime import date

try:
    import pytest
except ImportError:
    from tests import conftest
    pytest = conftest.pytest

from app.excepciones import (
    EjemplarNoDisponible,
    EjemplarNoEncontrado,
    PrestamoNoEncontrado,
    PrestamoYaDevuelto,
    SocioInactivo,
    SocioNoEncontrado,
)
from app.modelos.prestamo import DetallePrestamo, Prestamo
from app.servicios.prestamos import PrestamoServicio
from tests.conftest import FalsaUnidadTrabajo


def test_confirmar_prestamo_correcto(socio_activo, ejemplar_disponible):
    """
    Prueba Unitaria: Confirmar una operación de préstamo correcta.
    Comprueba:
    - Se crea el préstamo.
    - Se asocia el ejemplar.
    - El ejemplar pasa a 'PRESTADO'.
    - Se ejecuta commit() en la Unit of Work.
    """
    uow_falsa = FalsaUnidadTrabajo(
        socio_inicial=socio_activo,
        ejemplar_inicial=ejemplar_disponible
    )
    servicio = PrestamoServicio(uow_falsa)

    id_prestamo = servicio.registrar_prestamo(
        socio_activo.id_socio,
        ejemplar_disponible.id_ejemplar
    )

    assert id_prestamo is not None
    assert ejemplar_disponible.estado == "PRESTADO"
    assert uow_falsa.confirmado is True


def test_rechaza_socio_inactivo(socio_inactivo, ejemplar_disponible):
    """
    Prueba Unitaria: Rechazar préstamo a un socio inactivo.
    Debe lanzar SocioInactivo y no confirmar la transacción.
    """
    uow_falsa = FalsaUnidadTrabajo(
        socio_inicial=socio_inactivo,
        ejemplar_inicial=ejemplar_disponible
    )
    servicio = PrestamoServicio(uow_falsa)

    with pytest.raises(SocioInactivo):
        servicio.registrar_prestamo(
            socio_inactivo.id_socio,
            ejemplar_disponible.id_ejemplar
        )

    assert ejemplar_disponible.estado == "DISPONIBLE"
    assert uow_falsa.confirmado is False


def test_rechaza_ejemplar_no_disponible(socio_activo, ejemplar_prestado):
    """
    Prueba Unitaria: Rechazar préstamo sobre ejemplar ya prestado.
    Debe lanzar EjemplarNoDisponible y no confirmar la transacción.
    """
    uow_falsa = FalsaUnidadTrabajo(
        socio_inicial=socio_activo,
        ejemplar_inicial=ejemplar_prestado
    )
    servicio = PrestamoServicio(uow_falsa)

    with pytest.raises(EjemplarNoDisponible):
        servicio.registrar_prestamo(
            socio_activo.id_socio,
            ejemplar_prestado.id_ejemplar
        )

    assert uow_falsa.confirmado is False


def test_rechaza_socio_inexistente(ejemplar_disponible):
    """
    Prueba Unitaria: Socio no encontrado.
    Debe lanzar SocioNoEncontrado.
    """
    uow_falsa = FalsaUnidadTrabajo(
        ejemplar_inicial=ejemplar_disponible
    )
    servicio = PrestamoServicio(uow_falsa)

    with pytest.raises(SocioNoEncontrado):
        servicio.registrar_prestamo(
            9999,
            ejemplar_disponible.id_ejemplar
        )

    assert uow_falsa.confirmado is False


def test_rechaza_ejemplar_inexistente(socio_activo):
    """
    Prueba Unitaria: Ejemplar no encontrado.
    Debe lanzar EjemplarNoEncontrado.
    """
    uow_falsa = FalsaUnidadTrabajo(
        socio_inicial=socio_activo
    )
    servicio = PrestamoServicio(uow_falsa)

    with pytest.raises(EjemplarNoEncontrado):
        servicio.registrar_prestamo(
            socio_activo.id_socio,
            9999
        )

    assert uow_falsa.confirmado is False


def test_devolver_prestamo_correcto(socio_activo, ejemplar_prestado):
    """
    Prueba Unitaria: Devolución de préstamo correcta.
    Comprueba:
    - Se registra la fecha de devolución.
    - Los ejemplares vuelven a 'DISPONIBLE'.
    - Se confirma con commit().
    """
    prestamo = Prestamo(
        id_prestamo=50,
        id_socio=socio_activo.id_socio,
        fecha_prestamo=date.today(),
        fecha_limite=date.today(),
        fecha_devolucion=None
    )
    prestamo.ejemplares.append(ejemplar_prestado)

    uow_falsa = FalsaUnidadTrabajo(
        socio_inicial=socio_activo,
        ejemplar_inicial=ejemplar_prestado,
        prestamo_inicial=prestamo
    )
    servicio = PrestamoServicio(uow_falsa)

    exito = servicio.devolver_prestamo(prestamo.id_prestamo)

    assert exito is True
    assert prestamo.fecha_devolucion == date.today()
    assert ejemplar_prestado.estado == "DISPONIBLE"
    assert uow_falsa.confirmado is True


def test_devolver_prestamo_inexistente():
    """
    Prueba Unitaria: Devolver un préstamo que no existe en el repositorio.
    Debe lanzar PrestamoNoEncontrado.
    """
    uow_falsa = FalsaUnidadTrabajo()
    servicio = PrestamoServicio(uow_falsa)

    with pytest.raises(PrestamoNoEncontrado):
        servicio.devolver_prestamo(8888)

    assert uow_falsa.confirmado is False


def test_rechaza_devolucion_prestamo_ya_devuelto(socio_activo, ejemplar_disponible):
    """
    Prueba Unitaria: Intentar devolver un préstamo ya cerrado.
    Debe lanzar PrestamoYaDevuelto.
    """
    prestamo = Prestamo(
        id_prestamo=60,
        id_socio=socio_activo.id_socio,
        fecha_prestamo=date.today(),
        fecha_limite=date.today(),
        fecha_devolucion=date.today()
    )
    prestamo.ejemplares.append(ejemplar_disponible)

    uow_falsa = FalsaUnidadTrabajo(
        socio_inicial=socio_activo,
        ejemplar_inicial=ejemplar_disponible,
        prestamo_inicial=prestamo
    )
    servicio = PrestamoServicio(uow_falsa)

    with pytest.raises(PrestamoYaDevuelto):
        servicio.devolver_prestamo(prestamo.id_prestamo)

    assert uow_falsa.confirmado is False
