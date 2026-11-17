#!/usr/bin/env python3
"""
Diagnóstico y corrección del problema N+1 en SQLAlchemy ORM.
Parte 6: Estrategias de carga y control de rendimiento.

Compara la cantidad de sentencias SQL ejecutadas con Carga Diferida (Lazy Loading)
frente a Carga Ansiosa optimizada (Eager Loading con joinedload y selectinload).
"""

from decimal import Decimal
from sqlalchemy import create_engine
from sqlalchemy import event
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload
from sqlalchemy.orm import selectinload

from app.modelos.autor import Autor
from app.modelos.base import Base
from app.modelos.ejemplar import Ejemplar
from app.modelos.libro import Libro
from app.modelos.prestamo import DetallePrestamo, Prestamo
from app.modelos.socio import Socio


class ContadorConsultas:
    """Interceptor de eventos SQL para auditar la cantidad exacta de queries."""

    def __init__(self) -> None:
        self.consultas: list[str] = []

    def callback(self, conn, cursor, statement, parameters, context, executemany):
        # Excluir transacciones de control interno
        stmt_lower = statement.strip().lower()
        if not (stmt_lower.startswith("begin") or stmt_lower.startswith("commit") or stmt_lower.startswith("rollback")):
            self.consultas.append(statement)

    def reiniciar(self) -> None:
        self.consultas.clear()

    @property
    def total(self) -> int:
        return len(self.consultas)


def preparar_datos_prueba(session: Session) -> None:
    """Inserta datos de prueba si no existen."""
    if session.scalar(select(Autor)):
        return

    for idx_autor in range(1, 6):
        autor = Autor(nombre=f"Autor_{idx_autor}", apellidos=f"Apellido_{idx_autor}")
        session.add(autor)
        session.flush()

        for idx_libro in range(1, 4):
            libro = Libro(
                isbn=f"978000000{idx_autor}{idx_libro:02d}",
                titulo=f"Libro {idx_libro} de {autor.nombre}",
                precio=Decimal("21.50"),
                id_autor=autor.id_autor,
                activo=True
            )
            session.add(libro)
            session.flush()

            ejemplar = Ejemplar(
                codigo_inventario=f"EJ-{idx_autor}-{idx_libro}",
                id_libro=libro.id_libro,
                estado="DISPONIBLE"
            )
            session.add(ejemplar)

    socio = Socio(nombre="SocioPrueba", apellidos="N+1", activo=True)
    session.add(socio)
    session.flush()

    from datetime import date, timedelta
    hoy = date.today()
    prestamo = Prestamo(
        id_socio=socio.id_socio,
        fecha_prestamo=hoy,
        fecha_limite=hoy + timedelta(days=15)
    )
    session.add(prestamo)
    session.flush()

    primer_ejemplar = session.scalars(select(Ejemplar)).first()
    if primer_ejemplar:
        prestamo.ejemplares.append(primer_ejemplar)
        prestamo.detalles.append(DetallePrestamo(ejemplar=primer_ejemplar))

    session.commit()


def ejecutar_diagnostico():
    print("=" * 80)
    print("AUDITORÍA DE RENDIMIENTO: DIAGNÓSTICO Y CORRECCIÓN DEL PROBLEMA N+1")
    print("=" * 80)

    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)

    contador = ContadorConsultas()
    event.listen(engine, "before_cursor_execute", contador.callback)

    with Session(engine) as session:
        preparar_datos_prueba(session)

        # ---------------------------------------------------------------------
        # ESCENARIO 1: Autores con sus Libros (Relación 1 a N)
        # ---------------------------------------------------------------------
        print("\n" + "#" * 80)
        print("ESCENARIO 1: Listado de Autores con sus Libros (Relación 1 -> N)")
        print("#" * 80)

        # Caso 1.1: Lazy Loading (Provoca N+1)
        session.expire_all()
        contador.reiniciar()
        autores_lazy = session.scalars(select(Autor)).all()
        titulos_leidos = []
        for autor in autores_lazy:
            for libro in autor.libros:
                titulos_leidos.append(libro.titulo)
        total_lazy_1 = contador.total

        # Caso 1.2: Eager Loading con selectinload
        session.expire_all()
        contador.reiniciar()
        autores_eager = session.scalars(select(Autor).options(selectinload(Autor.libros))).all()
        for autor in autores_eager:
            for libro in autor.libros:
                _ = libro.titulo
        total_eager_1 = contador.total

        print(f"  • Sin optimizar (Lazy loading):    {total_lazy_1} consultas SQL (1 autores + {total_lazy_1 - 1} diferidas de libros)")
        print(f"  • Con selectinload (Eager loading): {total_eager_1} consultas SQL (1 autores + 1 agrupada con IN (...))")
        print(f"  --> Reducción de consultas:        -{(1 - total_eager_1 / total_lazy_1) * 100:.1f}%")

        # ---------------------------------------------------------------------
        # ESCENARIO 2: Listado de Libros con su Autor (Relación N a 1)
        # ---------------------------------------------------------------------
        print("\n" + "#" * 80)
        print("ESCENARIO 2: Listado de Libros con su Autor (Relación N -> 1)")
        print("#" * 80)

        # Caso 2.1: Lazy Loading
        session.expire_all()
        contador.reiniciar()
        libros_lazy = session.scalars(select(Libro)).all()
        for l in libros_lazy:
            _ = l.autor.nombre if l.autor else None
        total_lazy_2 = contador.total

        # Caso 2.2: Eager Loading con joinedload
        session.expire_all()
        contador.reiniciar()
        libros_eager = session.scalars(select(Libro).options(joinedload(Libro.autor))).all()
        for l in libros_eager:
            _ = l.autor.nombre if l.autor else None
        total_eager_2 = contador.total

        print(f"  • Sin optimizar (Lazy loading):    {total_lazy_2} consultas SQL (1 libros + accesos diferidos a autores)")
        print(f"  • Con joinedload (Eager loading):  {total_eager_2} consulta SQL (SELECT libros LEFT OUTER JOIN autores)")
        print(f"  --> Reducción de consultas:        -{(1 - total_eager_2 / total_lazy_2) * 100:.1f}%")

        # ---------------------------------------------------------------------
        # ESCENARIO 3: Préstamos con Socio y Ejemplares (Relación Compuesta N:1 y N:M)
        # ---------------------------------------------------------------------
        print("\n" + "#" * 80)
        print("ESCENARIO 3: Préstamos con Socio y Ejemplares")
        print("#" * 80)

        # Caso 3.1: Lazy
        session.expire_all()
        contador.reiniciar()
        prestamos_lazy = session.scalars(select(Prestamo)).all()
        for p in prestamos_lazy:
            _ = p.socio.nombre
            for e in p.ejemplares:
                _ = e.codigo_inventario
        total_lazy_3 = contador.total

        # Caso 3.2: Eager con joinedload + selectinload
        session.expire_all()
        contador.reiniciar()
        sentencia_p = select(Prestamo).options(
            joinedload(Prestamo.socio),
            selectinload(Prestamo.ejemplares)
        )
        prestamos_eager = session.scalars(sentencia_p).all()
        for p in prestamos_eager:
            _ = p.socio.nombre
            for e in p.ejemplares:
                _ = e.codigo_inventario
        total_eager_3 = contador.total

        print(f"  • Sin optimizar (Lazy loading):    {total_lazy_3} consultas SQL")
        print(f"  • Optimizado (joinedload + selectinload): {total_eager_3} consultas SQL")
        print(f"  --> Rendimiento óptimo garantizado.")

    print("\n" + "=" * 80)
    print("CONCLUSIÓN:")
    print("  - selectinload() resuelve relaciones de colección 1 a N y N a M mediante sentencias agrupadas IN (...).")
    print("  - joinedload() resuelve relaciones de cardinalidad 1 a 1 y N a 1 mediante un único JOIN en SQL.")
    print("=" * 80)


if __name__ == "__main__":
    ejecutar_diagnostico()
