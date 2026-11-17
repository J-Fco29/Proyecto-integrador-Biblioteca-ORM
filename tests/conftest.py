import os
from decimal import Decimal
from datetime import date, timedelta
from typing import Any

try:
    import pytest
except ImportError:
    class _FakeMark:
        def parametrize(self, argnames, argvalues):
            def decorator(fn):
                fn._parametrized = (argnames, argvalues)
                return fn
            return decorator

    class _FakePytest:
        mark = _FakeMark()

        @staticmethod
        def fixture(*args, **kwargs):
            def decorator(fn):
                return fn
            if args and callable(args[0]):
                return args[0]
            return decorator

        class raises:
            def __init__(self, expected_exception):
                self.expected = expected_exception

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc_val, exc_tb):
                if exc_type is None:
                    raise AssertionError(f"Se esperaba la excepción {self.expected} pero no fue lanzada.")
                return issubclass(exc_type, self.expected)

    pytest = _FakePytest()

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.configuracion import obtener_url_bd
from app.dto.libros import FiltroLibros
from app.modelos.autor import Autor
from app.modelos.base import Base
from app.modelos.ejemplar import Ejemplar
from app.modelos.libro import Libro
from app.modelos.prestamo import Prestamo
from app.modelos.socio import Socio
from app.unidad_trabajo import UnidadTrabajoSQLAlchemy


# =============================================================================
# REPOSITORIOS FALSOS (IN-MEMORY TEST DOUBLES)
# =============================================================================

class FalsoAutorRepositorio:
    def __init__(self, autores: list[Autor] | None = None) -> None:
        self._datos: dict[int, Autor] = {a.id_autor: a for a in (autores or []) if a.id_autor is not None}

    def buscar(self, id_autor: int) -> Autor | None:
        return self._datos.get(id_autor)

    def buscar_por_id(self, id_autor: int) -> Autor | None:
        return self.buscar(id_autor)

    def añadir(self, autor: Autor) -> None:
        if autor.id_autor is None:
            siguiente = max(self._datos.keys(), default=0) + 1
            autor.id_autor = siguiente
        self._datos[autor.id_autor] = autor

    def listar_todos(self, precargar_libros: bool = False) -> list[Autor]:
        return list(self._datos.values())


class FalsoLibroRepositorio:
    def __init__(self, libros: list[Libro] | None = None) -> None:
        self._datos: dict[int, Libro] = {l.id_libro: l for l in (libros or []) if l.id_libro is not None}

    def buscar(self, id_libro: int) -> Libro | None:
        return self._datos.get(id_libro)

    def buscar_por_id(self, id_libro: int) -> Libro | None:
        return self.buscar(id_libro)

    def buscar_por_isbn(self, isbn: str) -> Libro | None:
        for libro in self._datos.values():
            if libro.isbn == isbn.strip():
                return libro
        return None

    def añadir(self, libro: Libro) -> None:
        if libro.id_libro is None:
            siguiente = max(self._datos.keys(), default=0) + 1
            libro.id_libro = siguiente
        self._datos[libro.id_libro] = libro

    def listar_todos(self, precargar_autor: bool = True) -> list[Libro]:
        return list(self._datos.values())

    def listar_con_filtro(self, filtro: FiltroLibros) -> list[Libro]:
        resultado = list(self._datos.values())
        if filtro.solo_activos:
            resultado = [l for l in resultado if l.activo]
        if filtro.texto:
            resultado = [l for l in resultado if filtro.texto.lower() in l.titulo.lower()]
        if filtro.precio_minimo is not None:
            resultado = [l for l in resultado if l.precio >= filtro.precio_minimo]
        if filtro.precio_maximo is not None:
            resultado = [l for l in resultado if l.precio <= filtro.precio_maximo]
        if filtro.id_autor is not None:
            resultado = [l for l in resultado if l.id_autor == filtro.id_autor]
        inicio = (filtro.pagina - 1) * filtro.tamano
        return resultado[inicio : inicio + filtro.tamano]

    def contar_con_filtro(self, filtro: FiltroLibros) -> int:
        return len(self.listar_con_filtro(FiltroLibros(
            texto=filtro.texto,
            precio_minimo=filtro.precio_minimo,
            precio_maximo=filtro.precio_maximo,
            id_autor=filtro.id_autor,
            solo_activos=filtro.solo_activos,
            pagina=1,
            tamano=1000000
        )))

    def eliminar(self, libro: Libro) -> None:
        if libro.id_libro in self._datos:
            del self._datos[libro.id_libro]


class FalsoSocioRepositorio:
    def __init__(self, socios: list[Socio] | None = None) -> None:
        self._datos: dict[int, Socio] = {s.id_socio: s for s in (socios or []) if s.id_socio is not None}

    def buscar(self, id_socio: int) -> Socio | None:
        return self._datos.get(id_socio)

    def buscar_por_id(self, id_socio: int) -> Socio | None:
        return self.buscar(id_socio)

    def buscar_por_dni(self, dni: str) -> Socio | None:
        for s in self._datos.values():
            if s.dni == dni.strip():
                return s
        return None

    def añadir(self, socio: Socio) -> None:
        if socio.id_socio is None:
            siguiente = max(self._datos.keys(), default=0) + 1
            socio.id_socio = siguiente
        self._datos[socio.id_socio] = socio

    def listar_todos(self) -> list[Socio]:
        return list(self._datos.values())


class FalsoEjemplarRepositorio:
    def __init__(self, ejemplares: list[Ejemplar] | None = None) -> None:
        self._datos: dict[int, Ejemplar] = {e.id_ejemplar: e for e in (ejemplares or []) if e.id_ejemplar is not None}

    def buscar(self, id_ejemplar: int) -> Ejemplar | None:
        return self._datos.get(id_ejemplar)

    def buscar_por_id(self, id_ejemplar: int) -> Ejemplar | None:
        return self.buscar(id_ejemplar)

    def buscar_por_codigo(self, codigo: str) -> Ejemplar | None:
        for e in self._datos.values():
            if e.codigo_inventario == codigo.strip():
                return e
        return None

    def añadir(self, ejemplar: Ejemplar) -> None:
        if ejemplar.id_ejemplar is None:
            siguiente = max(self._datos.keys(), default=0) + 1
            ejemplar.id_ejemplar = siguiente
        self._datos[ejemplar.id_ejemplar] = ejemplar

    def listar_por_libro(self, id_libro: int) -> list[Ejemplar]:
        return [e for e in self._datos.values() if e.id_libro == id_libro]

    def listar_todos(self) -> list[Ejemplar]:
        return list(self._datos.values())


class FalsoPrestamoRepositorio:
    def __init__(self, prestamos: list[Prestamo] | None = None) -> None:
        self._datos: dict[int, Prestamo] = {p.id_prestamo: p for p in (prestamos or []) if p.id_prestamo is not None}

    def buscar(self, id_prestamo: int) -> Prestamo | None:
        return self._datos.get(id_prestamo)

    def buscar_por_id(self, id_prestamo: int) -> Prestamo | None:
        return self.buscar(id_prestamo)

    def añadir(self, prestamo: Prestamo) -> None:
        if prestamo.id_prestamo is None:
            siguiente = max(self._datos.keys(), default=0) + 1
            prestamo.id_prestamo = siguiente
        self._datos[prestamo.id_prestamo] = prestamo

    def listar_abiertos(self) -> list[Prestamo]:
        return [p for p in self._datos.values() if p.fecha_devolucion is None]

    def listar_todos(self) -> list[Prestamo]:
        return list(self._datos.values())


# =============================================================================
# UNIT OF WORK FALSA
# =============================================================================

class FalsaUnidadTrabajo:
    """Implementación simulada de Unit of Work para pruebas unitarias sin BD."""

    def __init__(
        self,
        libro_inicial: Libro | None = None,
        autor_inicial: Autor | None = None,
        socio_inicial: Socio | None = None,
        ejemplar_inicial: Ejemplar | None = None,
        prestamo_inicial: Prestamo | None = None
    ) -> None:
        self.libros = FalsoLibroRepositorio([libro_inicial] if libro_inicial else [])
        self.autores = FalsoAutorRepositorio([autor_inicial] if autor_inicial else [])
        self.socios = FalsoSocioRepositorio([socio_inicial] if socio_inicial else [])
        self.ejemplares = FalsoEjemplarRepositorio([ejemplar_inicial] if ejemplar_inicial else [])
        self.prestamos = FalsoPrestamoRepositorio([prestamo_inicial] if prestamo_inicial else [])
        self.confirmado = False
        self.revertido = False

    def __enter__(self) -> "FalsaUnidadTrabajo":
        self.confirmado = False
        self.revertido = False
        return self

    def __exit__(self, tipo_error: Any, error: Any, traceback: Any) -> None:
        if error is not None:
            self.rollback()

    def flush(self) -> None:
        pass

    def commit(self) -> None:
        self.confirmado = True

    def rollback(self) -> None:
        self.revertido = True


# =============================================================================
# FIXTURES PARA PRUEBAS UNITARIAS
# =============================================================================

@pytest.fixture
def autor_demo():
    return Autor(
        id_autor=1,
        nombre="Gabriel",
        apellidos="García Márquez"
    )


@pytest.fixture
def libro(autor_demo):
    l = Libro(
        id_libro=1,
        isbn="9780000000001",
        titulo="Cien años de soledad",
        precio=Decimal("19.90"),
        id_autor=1,
        activo=True,
        observaciones="Edición especial"
    )
    l.autor = autor_demo
    return l


@pytest.fixture
def socio_activo():
    return Socio(
        id_socio=10,
        nombre="Laura",
        apellidos="Gómez",
        email="laura@example.com",
        activo=True
    )


@pytest.fixture
def socio_inactivo():
    return Socio(
        id_socio=20,
        nombre="Carlos",
        apellidos="Ruiz",
        email="carlos@example.com",
        activo=False
    )


@pytest.fixture
def ejemplar_disponible(libro):
    e = Ejemplar(
        id_ejemplar=100,
        codigo_inventario="EJ-001",
        id_libro=1,
        ubicacion="Pasillo 3 - Balda B",
        estado="DISPONIBLE"
    )
    e.libro = libro
    return e


@pytest.fixture
def ejemplar_prestado(libro):
    e = Ejemplar(
        id_ejemplar=101,
        codigo_inventario="EJ-002",
        id_libro=1,
        ubicacion="Pasillo 3 - Balda B",
        estado="PRESTADO"
    )
    e.libro = libro
    return e


@pytest.fixture
def uow_falsa(libro, autor_demo):
    return FalsaUnidadTrabajo(libro_inicial=libro, autor_inicial=autor_demo)


@pytest.fixture
def uow_falsa_prestamos(socio_activo, ejemplar_disponible):
    return FalsaUnidadTrabajo(
        socio_inicial=socio_activo,
        ejemplar_inicial=ejemplar_disponible
    )


# =============================================================================
# FIXTURES PARA PRUEBAS DE INTEGRACIÓN (BASE DE DATOS REAL)
# =============================================================================

@pytest.fixture(scope="session")
def engine_test():
    """
    Proporciona el motor de base de datos para pruebas de integración.
    Prioriza 'biblioteca_test' en PostgreSQL; si no hay servidor activo,
    hace fallback a SQLite en memoria para garantizar ejecución completa.
    """
    try:
        url = obtener_url_bd(solo_test=True)
        engine = create_engine(url)
        with engine.connect():
            pass
    except Exception:
        engine = create_engine("sqlite:///:memory:")

    Base.metadata.create_all(engine)
    return engine


@pytest.fixture
def session(engine_test):
    """
    Sesión aislada para pruebas de integración.
    Envuelve cada prueba en una transacción y ejecuta rollback() en el teardown.
    """
    conexion = engine_test.connect()
    transaccion = conexion.begin()
    session = Session(bind=conexion)

    # Asegura autor base para las pruebas de libros
    autor_base = session.get(Autor, 1)
    if autor_base is None:
        autor_base = Autor(id_autor=1, nombre="Miguel", apellidos="de Cervantes")
        session.add(autor_base)
        session.flush()

    try:
        yield session
    finally:
        session.close()
        transaccion.rollback()
        conexion.close()


@pytest.fixture
def uow_integracion(session):
    """Unit of Work conectada a la sesión transaccional de integración."""
    fabrica = sessionmaker(bind=session.connection())
    return UnidadTrabajoSQLAlchemy(fabrica_sesiones=fabrica)
