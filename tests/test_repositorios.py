from datetime import date, timedelta
from decimal import Decimal

try:
    import pytest
except ImportError:
    from tests import conftest
    pytest = conftest.pytest

from sqlalchemy.exc import IntegrityError

from app.dto.libros import FiltroLibros
from app.modelos.autor import Autor
from app.modelos.ejemplar import Ejemplar
from app.modelos.libro import Libro
from app.modelos.prestamo import DetallePrestamo, Prestamo
from app.modelos.socio import Socio
from app.repositorios.ejemplares import EjemplarRepositorio
from app.repositorios.libros import LibroRepositorio, SQLAlchemyLibroRepositorio
from app.repositorios.prestamos import PrestamoRepositorio
from app.repositorios.socios import SocioRepositorio


def test_insertar_y_recuperar_libro(session):
    """
    Prueba 1 de Integración: Insertar y recuperar un libro en base de datos.
    1. Instancia el repositorio real sobre la sesión transaccional.
    2. Inserta una nueva entidad Libro.
    3. Ejecuta session.flush() para sincronizar con la BD.
    4. Recupera el libro mediante su id generado.
    5. Comprueba integridad de datos y tipos mapeados.
    """
    repositorio = SQLAlchemyLibroRepositorio(session)

    libro = Libro(
        isbn="9780000000999",
        titulo="Fundamentos de Bases de Datos Relacionales",
        precio=Decimal("38.50"),
        id_autor=1,
        activo=True,
        observaciones="Copia de referencia para docencia"
    )

    repositorio.añadir(libro)
    session.flush()

    assert libro.id_libro is not None
    recuperado = repositorio.buscar(libro.id_libro)

    assert recuperado is not None
    assert recuperado.isbn == "9780000000999"
    assert recuperado.titulo == "Fundamentos de Bases de Datos Relacionales"
    assert recuperado.precio == Decimal("38.50")
    assert recuperado.id_autor == 1
    assert recuperado.activo is True


def test_comprobar_isbn_duplicado(session):
    """
    Prueba 2 de Integración: Violación de la restricción de unicidad del ISBN.
    1. Crea dos libros distintos con el mismo ISBN.
    2. Añade ambos dentro de la misma transacción.
    3. Al ejecutar flush(), el motor relacional debe rechazar el duplicado.
    4. Comprueba que se produce IntegrityError.
    """
    repositorio = SQLAlchemyLibroRepositorio(session)
    isbn_repetido = "9788448199999"

    libro_1 = Libro(
        isbn=isbn_repetido,
        titulo="Edición Original",
        precio=Decimal("20.00"),
        id_autor=1,
        activo=True
    )
    libro_2 = Libro(
        isbn=isbn_repetido,
        titulo="Edición Duplicada Ilegal",
        precio=Decimal("25.00"),
        id_autor=1,
        activo=True
    )

    repositorio.añadir(libro_1)
    session.flush()

    with pytest.raises(IntegrityError):
        repositorio.añadir(libro_2)
        session.flush()


def test_registrar_prestamo_y_comprobar_estado_ejemplar(session):
    """
    Prueba 3 de Integración: Registro persistente de préstamo y actualización del ejemplar.
    1. Inserta un socio activo y un ejemplar disponible.
    2. Registra el préstamo asociando el ejemplar y cambia su estado a 'PRESTADO'.
    3. Realiza flush() para persistir las relaciones y claves ajenas.
    4. Consulta el ejemplar y el préstamo desde la base de datos comprobando consistencia.
    """
    repo_socios = SocioRepositorio(session)
    repo_libros = LibroRepositorio(session)
    repo_ejemplares = EjemplarRepositorio(session)
    repo_prestamos = PrestamoRepositorio(session)

    socio = Socio(
        nombre="Elena",
        apellidos="Vidal",
        email="elena.vidal@example.com",
        dni="12345678A",
        activo=True
    )
    repo_socios.añadir(socio)

    libro = Libro(
        isbn="9788437604947",
        titulo="Rinconete y Cortadillo",
        precio=Decimal("12.00"),
        id_autor=1,
        activo=True
    )
    repo_libros.añadir(libro)
    session.flush()

    ejemplar = Ejemplar(
        codigo_inventario="EJ-RINCONETE-01",
        id_libro=libro.id_libro,
        ubicacion="Sección Clásicos",
        estado="DISPONIBLE"
    )
    repo_ejemplares.añadir(ejemplar)
    session.flush()

    # Registro de préstamo
    prestamo = Prestamo(
        id_socio=socio.id_socio,
        fecha_prestamo=date.today(),
        fecha_limite=date.today() + timedelta(days=15)
    )
    prestamo.detalles.append(DetallePrestamo(ejemplar=ejemplar))
    prestamo.ejemplares.append(ejemplar)
    ejemplar.estado = "PRESTADO"

    repo_prestamos.añadir(prestamo)
    session.flush()

    # Verificación en BD
    prestamo_recuperado = repo_prestamos.buscar(prestamo.id_prestamo)
    assert prestamo_recuperado is not None
    assert prestamo_recuperado.socio.id_socio == socio.id_socio

    ejemplar_recuperado = repo_ejemplares.buscar(ejemplar.id_ejemplar)
    assert ejemplar_recuperado is not None
    assert ejemplar_recuperado.estado == "PRESTADO"


def test_devolucion_prestamo_integracion(session):
    """
    Prueba 4 de Integración: Cierre de préstamo y liberación del ejemplar en BD.
    Comprueba que la fecha de devolución queda fijada y el ejemplar pasa a 'DISPONIBLE'.
    """
    repo_socios = SocioRepositorio(session)
    repo_libros = LibroRepositorio(session)
    repo_ejemplares = EjemplarRepositorio(session)
    repo_prestamos = PrestamoRepositorio(session)

    socio = Socio(nombre="Marcos", apellidos="Pardo", activo=True)
    repo_socios.añadir(socio)

    libro = Libro(isbn="9788424912345", titulo="La Galatea", precio=Decimal("14.50"), id_autor=1)
    repo_libros.añadir(libro)
    session.flush()

    ejemplar = Ejemplar(codigo_inventario="EJ-GALATEA-01", id_libro=libro.id_libro, estado="PRESTADO")
    repo_ejemplares.añadir(ejemplar)
    session.flush()

    prestamo = Prestamo(
        id_socio=socio.id_socio,
        fecha_prestamo=date.today() - timedelta(days=5),
        fecha_limite=date.today() + timedelta(days=10)
    )
    prestamo.ejemplares.append(ejemplar)
    prestamo.detalles.append(DetallePrestamo(ejemplar=ejemplar))
    repo_prestamos.añadir(prestamo)
    session.flush()

    # Ejecución de la devolución
    prestamo.fecha_devolucion = date.today()
    ejemplar.estado = "DISPONIBLE"
    session.flush()

    p_check = repo_prestamos.buscar(prestamo.id_prestamo)
    assert p_check.fecha_devolucion == date.today()
    e_check = repo_ejemplares.buscar(ejemplar.id_ejemplar)
    assert e_check.estado == "DISPONIBLE"


def test_consulta_filtro_y_paginacion_libros(session):
    """
    Prueba 5 de Integración: Comprobación de consulta dinámica y paginación en SQL real.
    """
    repo = LibroRepositorio(session)
    for idx in range(1, 8):
        repo.añadir(Libro(
            isbn=f"97899990000{idx}",
            titulo=f"Manual de Programación Tomo {idx}",
            precio=Decimal(f"{10 + idx * 5}.00"),
            id_autor=1,
            activo=True
        ))
    session.flush()

    # Página 1 de 3 elementos
    filtro_p1 = FiltroLibros(texto="Programación", pagina=1, tamano=3)
    p1 = repo.listar_con_filtro(filtro_p1)
    assert len(p1) == 3

    # Total de coincidencias
    total = repo.contar_con_filtro(filtro_p1)
    assert total >= 7
