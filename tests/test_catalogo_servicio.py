from decimal import Decimal

try:
    import pytest
except ImportError:
    from tests import conftest
    pytest = conftest.pytest

from app.dto.libros import DatosLibro, FiltroLibros
from app.excepciones import AutorNoEncontrado, PrecioInvalido
from app.servicios.catalogo import CatalogoServicio


def test_actualizar_precio_correcto(libro, uow_falsa):
    """
    Prueba Unitaria 1: Actualización exitosa del precio.
    Comprueba que el libro existe, el precio cambia y la UoW ejecuta commit().
    """
    servicio = CatalogoServicio(uow_falsa)

    resultado = servicio.cambiar_precio(libro.id_libro, Decimal("29.90"))

    assert resultado is True
    assert libro.precio == Decimal("29.90")
    assert uow_falsa.confirmado is True


def test_rechaza_precio_negativo(libro, uow_falsa):
    """
    Prueba Unitaria 2: Rechazar un precio negativo o cero.
    Debe lanzar PrecioInvalido (que hereda de ValueError) y no confirmar la UoW.
    """
    precio_original = libro.precio
    servicio = CatalogoServicio(uow_falsa)

    with pytest.raises(ValueError):
        servicio.actualizar_precio(libro.id_libro, Decimal("-5.00"))

    assert libro.precio == precio_original
    assert uow_falsa.confirmado is False


def test_no_crear_libro_si_autor_no_existe(uow_falsa):
    """
    Prueba Unitaria 3: No crear un libro si el autor no existe.
    Debe lanzar AutorNoEncontrado y no confirmar la UoW.
    """
    servicio = CatalogoServicio(uow_falsa)
    datos = DatosLibro(
        isbn="9788420471839",
        titulo="Libro Huérfano",
        precio=Decimal("22.50"),
        id_autor=999  # Autor inexistente en el repositorio simulado
    )

    with pytest.raises(AutorNoEncontrado):
        servicio.crear_libro(datos)

    assert uow_falsa.confirmado is False


def test_crear_libro_correcto(autor_demo, uow_falsa):
    """
    Prueba Unitaria 4: Creación de libro válida.
    Comprueba la asignación de campos, llamada a añadir y commit().
    """
    servicio = CatalogoServicio(uow_falsa)
    datos = DatosLibro(
        isbn="9780142437230",
        titulo="Don Quijote de la Mancha",
        precio=Decimal("15.00"),
        id_autor=autor_demo.id_autor,
        observaciones="Clásico universal"
    )

    id_creado = servicio.crear_libro(datos)

    assert id_creado is not None
    assert uow_falsa.confirmado is True
    libro_creado = uow_falsa.libros.buscar(id_creado)
    assert libro_creado.titulo == "Don Quijote de la Mancha"


def test_libro_inexistente(uow_falsa):
    """
    Prueba Unitaria 5: Operación sobre libro no encontrado.
    El servicio debe devolver False y no confirmar la UoW.
    """
    servicio = CatalogoServicio(uow_falsa)

    resultado = servicio.actualizar_precio(99999, Decimal("25.00"))

    assert resultado is False
    assert uow_falsa.confirmado is False


def test_desactivar_libro_borrado_logico(libro, uow_falsa):
    """
    Prueba Unitaria 6: Borrado lógico.
    El campo activo pasa a False y se confirma con commit().
    """
    servicio = CatalogoServicio(uow_falsa)

    resultado = servicio.desactivar_libro(libro.id_libro)

    assert resultado is True
    assert libro.activo is False
    assert uow_falsa.confirmado is True


def test_filtrar_libros_por_precio_y_texto(libro, uow_falsa):
    """
    Prueba Unitaria 7: Filtrado dinámico y paginación en memoria.
    """
    servicio = CatalogoServicio(uow_falsa)
    filtro = FiltroLibros(
        texto="soledad",
        precio_minimo=Decimal("10.00"),
        precio_maximo=Decimal("30.00"),
        solo_activos=True,
        pagina=1,
        tamano=5
    )

    items, total = servicio.buscar_con_filtro(filtro)

    assert total == 1
    assert len(items) == 1
    assert items[0].id_libro == libro.id_libro
