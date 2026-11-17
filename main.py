#!/usr/bin/env python3
"""
Interfaz de consola de la Biblioteca ORM.
Capa de presentación: interactúa exclusivamente con los Servicios mediante DTOs.
No contiene consultas ORM ni administra directamente la Session de SQLAlchemy.
"""

from decimal import Decimal, InvalidOperation
import sys

from app.conexion import engine
from app.dto.libros import DatosLibro, FiltroLibros
from app.excepciones import (
    AutorNoEncontrado,
    EjemplarNoDisponible,
    EjemplarNoEncontrado,
    ErrorBiblioteca,
    IsbnDuplicado,
    LibroNoEncontrado,
    PrecioInvalido,
    PrestamoNoEncontrado,
    PrestamoYaDevuelto,
    SocioInactivo,
    SocioNoEncontrado,
)
from app.modelos.base import Base
from app.servicios.catalogo import CatalogoServicio
from app.servicios.prestamos import PrestamoServicio
from app.unidad_trabajo import UnidadTrabajoSQLAlchemy


def inicializar_base_datos() -> None:
    """Garantiza la existencia de las tablas y ofrece sembrar datos iniciales si está vacía."""
    try:
        Base.metadata.create_all(engine)
    except Exception as exc:
        print(f"\033[93m[AVISO] No se pudo conectar a PostgreSQL ({exc}). Utilizando entorno local.\033[0m")


def sembrar_datos_si_vacio(uow: UnidadTrabajoSQLAlchemy) -> None:
    """Puebla la base con autores, libros, socios y ejemplares iniciales si no existen."""
    with uow:
        if uow.autores.listar_todos():
            return

        from app.modelos.autor import Autor
        from app.modelos.ejemplar import Ejemplar
        from app.modelos.libro import Libro
        from app.modelos.socio import Socio

        # Autores
        a1 = Autor(nombre="Miguel", apellidos="de Cervantes")
        a2 = Autor(nombre="Gabriel", apellidos="García Márquez")
        a3 = Autor(nombre="Jane", apellidos="Austen")
        uow.autores.añadir(a1)
        uow.autores.añadir(a2)
        uow.autores.añadir(a3)
        uow.flush()

        # Libros
        l1 = Libro(isbn="9788420471839", titulo="Don Quijote de la Mancha", precio=Decimal("18.50"), id_autor=a1.id_autor, activo=True, observaciones="Clásico universal")
        l2 = Libro(isbn="9780307474728", titulo="Cien años de soledad", precio=Decimal("21.90"), id_autor=a2.id_autor, activo=True, observaciones="Realismo mágico")
        l3 = Libro(isbn="9788497940863", titulo="Orgullo y prejuicio", precio=Decimal("15.00"), id_autor=a3.id_autor, activo=True, observaciones="Novela romántica histórica")
        l4 = Libro(isbn="9788437604947", titulo="Novelas ejemplares", precio=Decimal("12.00"), id_autor=a1.id_autor, activo=True, observaciones="Antología cervantina")
        uow.libros.añadir(l1)
        uow.libros.añadir(l2)
        uow.libros.añadir(l3)
        uow.libros.añadir(l4)
        uow.flush()

        # Ejemplares físicos
        e1 = Ejemplar(codigo_inventario="EJ-QUIJOTE-01", id_libro=l1.id_libro, ubicacion="Pasillo 1 - Balda A", estado="DISPONIBLE")
        e2 = Ejemplar(codigo_inventario="EJ-QUIJOTE-02", id_libro=l1.id_libro, ubicacion="Pasillo 1 - Balda A", estado="DISPONIBLE")
        e3 = Ejemplar(codigo_inventario="EJ-SOLEDAD-01", id_libro=l2.id_libro, ubicacion="Pasillo 2 - Balda C", estado="DISPONIBLE")
        e4 = Ejemplar(codigo_inventario="EJ-ORGULLO-01", id_libro=l3.id_libro, ubicacion="Pasillo 3 - Balda B", estado="DISPONIBLE")
        uow.ejemplares.añadir(e1)
        uow.ejemplares.añadir(e2)
        uow.ejemplares.añadir(e3)
        uow.ejemplares.añadir(e4)

        # Socios
        s1 = Socio(nombre="Carlos", apellidos="Martínez", email="carlos@correo.es", dni="11223344A", activo=True)
        s2 = Socio(nombre="Ana", apellidos="García", email="ana@correo.es", dni="22334455B", activo=True)
        s3 = Socio(nombre="Pedro", apellidos="López", email="pedro@correo.es", dni="33445566C", activo=False)
        uow.socios.añadir(s1)
        uow.socios.añadir(s2)
        uow.socios.añadir(s3)

        uow.commit()


# =============================================================================
# MANEJADORES DEL MENÚ DE CONSOLA
# =============================================================================

def menu_listar_libros(servicio: CatalogoServicio) -> None:
    print("\n" + "=" * 90)
    print("CATÁLOGO COMPLETO DE LIBROS")
    print("=" * 90)
    libros = servicio.listar_catalogo()
    if not libros:
        print("  No existen libros registrados en el catálogo.")
        return

    print(f"{'ID':<5} | {'ISBN':<15} | {'TÍTULO':<32} | {'AUTOR':<22} | {'PRECIO':<9} | {'ESTADO':<8}")
    print("-" * 90)
    for l in libros:
        estado = "Activo" if l.activo else "Inactivo"
        print(f"{l.id_libro:<5} | {l.isbn:<15} | {l.titulo[:30]:<32} | {l.autor[:20]:<22} | {l.precio:>6.2f} € | {estado:<8}")
    print("-" * 90)
    print(f"Total: {len(libros)} libros.")


def menu_buscar_libros(servicio: CatalogoServicio) -> None:
    print("\n" + "=" * 90)
    print("BÚSQUEDA DINÁMICA Y PAGINADA EN EL CATÁLOGO")
    print("=" * 90)

    texto = input("Texto a buscar en el título [Enter para omitir]: ").strip() or None

    p_min_raw = input("Precio mínimo en € [Enter para omitir]: ").strip()
    precio_minimo = Decimal(p_min_raw) if p_min_raw else None

    p_max_raw = input("Precio máximo en € [Enter para omitir]: ").strip()
    precio_maximo = Decimal(p_max_raw) if p_max_raw else None

    id_autor_raw = input("Identificador de autor [Enter para omitir]: ").strip()
    id_autor = int(id_autor_raw) if id_autor_raw else None

    solo_act = input("¿Mostrar únicamente libros activos? (S/n): ").strip().lower()
    solo_activos = False if solo_act == "n" else True

    pag_raw = input("Número de página [1 por defecto]: ").strip()
    pagina = int(pag_raw) if pag_raw and pag_raw.isdigit() else 1

    tam_raw = input("Libros por página [5 por defecto]: ").strip()
    tamano = int(tam_raw) if tam_raw and tam_raw.isdigit() else 5

    filtro = FiltroLibros(
        texto=texto,
        precio_minimo=precio_minimo,
        precio_maximo=precio_maximo,
        id_autor=id_autor,
        solo_activos=solo_activos,
        pagina=pagina,
        tamano=tamano
    )

    libros, total = servicio.buscar_con_filtro(filtro)

    print("\n" + "-" * 90)
    if not libros:
        print(f"  No se encontraron libros que coincidan con los criterios (Página {pagina}).")
    else:
        print(f"{'ID':<5} | {'ISBN':<15} | {'TÍTULO':<32} | {'AUTOR':<22} | {'PRECIO':<9} | {'ESTADO':<8}")
        print("-" * 90)
        for l in libros:
            estado = "Activo" if l.activo else "Inactivo"
            print(f"{l.id_libro:<5} | {l.isbn:<15} | {l.titulo[:30]:<32} | {l.autor[:20]:<22} | {l.precio:>6.2f} € | {estado:<8}")

    paginas_totales = (total + tamano - 1) // tamano if tamano > 0 else 1
    print("-" * 90)
    print(f"Página {pagina} de {paginas_totales} (Coincidencias totales: {total})")


def menu_crear_libro(servicio: CatalogoServicio) -> None:
    print("\n" + "=" * 90)
    print("ALTA DE NUEVO LIBRO")
    print("=" * 90)

    try:
        isbn = input("ISBN (ej. 9781234567890): ").strip()
        titulo = input("Título del libro: ").strip()
        precio_str = input("Precio en € (ej. 19.95): ").strip()
        precio = Decimal(precio_str)
        id_autor = int(input("ID del autor: ").strip())
        observaciones = input("Observaciones [Opcional]: ").strip() or None

        datos = DatosLibro(
            isbn=isbn,
            titulo=titulo,
            precio=precio,
            id_autor=id_autor,
            observaciones=observaciones
        )

        id_creado = servicio.crear_libro(datos)
        print(f"\033[92m✔ Libro creado exitosamente con ID {id_creado}.\033[0m")

    except (ValueError, InvalidOperation):
        print("\033[91m✖ Error: Datos numéricos o de formato no válidos.\033[0m")
    except AutorNoEncontrado as exc:
        print(f"\033[91m✖ Error de Negocio: {exc}\033[0m")
    except IsbnDuplicado as exc:
        print(f"\033[91m✖ Error de Integridad: {exc}\033[0m")
    except PrecioInvalido as exc:
        print(f"\033[91m✖ Validación de Precio: {exc}\033[0m")


def menu_actualizar_precio(servicio: CatalogoServicio) -> None:
    print("\n" + "=" * 90)
    print("ACTUALIZACIÓN DE PRECIO")
    print("=" * 90)

    try:
        id_libro = int(input("ID del libro a modificar: ").strip())
        precio_str = input("Nuevo precio en €: ").strip()
        nuevo_precio = Decimal(precio_str)

        exito = servicio.actualizar_precio(id_libro, nuevo_precio)
        if exito:
            print(f"\033[92m✔ Precio actualizado correctamente a {nuevo_precio:.2f} €.\033[0m")
        else:
            print(f"\033[91m✖ No se encontró ningún libro con ID {id_libro}.\033[0m")

    except (ValueError, InvalidOperation):
        print("\033[91m✖ Error: Ingrese valores numéricos válidos.\033[0m")
    except PrecioInvalido as exc:
        print(f"\033[91m✖ Validación de Precio: {exc}\033[0m")


def menu_desactivar_libro(servicio: CatalogoServicio) -> None:
    print("\n" + "=" * 90)
    print("DESACTIVACIÓN LÓGICA DE LIBRO (SOFT DELETE)")
    print("=" * 90)

    try:
        id_libro = int(input("ID del libro a desactivar: ").strip())
        servicio.desactivar_libro(id_libro)
        print(f"\033[92m✔ El libro con ID {id_libro} ha sido marcado como INACTIVO en el catálogo.\033[0m")

    except ValueError:
        print("\033[91m✖ Error: Identificador no válido.\033[0m")
    except LibroNoEncontrado as exc:
        print(f"\033[91m✖ Error de Negocio: {exc}\033[0m")


def menu_registrar_prestamo(servicio: PrestamoServicio) -> None:
    print("\n" + "=" * 90)
    print("REGISTRO DE PRÉSTAMO (OPERACIÓN ATÓMICA)")
    print("=" * 90)

    try:
        id_socio = int(input("ID del socio solicitante: ").strip())
        id_ejemplar = int(input("ID del ejemplar a prestar: ").strip())

        id_prestamo = servicio.registrar_prestamo(id_socio, id_ejemplar)
        print(f"\033[92m✔ Préstamo #{id_prestamo} registrado con éxito. Ejemplar #{id_ejemplar} marcado como PRESTADO.\033[0m")

    except ValueError:
        print("\033[91m✖ Error: Los identificadores deben ser enteros válidos.\033[0m")
    except SocioNoEncontrado as exc:
        print(f"\033[91m✖ Error de Negocio: {exc}\033[0m")
    except SocioInactivo as exc:
        print(f"\033[91m✖ Error de Validación: {exc}\033[0m")
    except EjemplarNoEncontrado as exc:
        print(f"\033[91m✖ Error de Negocio: {exc}\033[0m")
    except EjemplarNoDisponible as exc:
        print(f"\033[91m✖ Error de Disponibilidad: {exc}\033[0m")


def menu_devolver_prestamo(servicio: PrestamoServicio) -> None:
    print("\n" + "=" * 90)
    print("DEVOLUCIÓN DE PRÉSTAMO")
    print("=" * 90)

    try:
        id_prestamo = int(input("ID del préstamo a devolver: ").strip())
        servicio.devolver_prestamo(id_prestamo)
        print(f"\033[92m✔ Préstamo #{id_prestamo} devuelto satisfactoriamente. Ejemplares reincorporados como DISPONIBLE.\033[0m")

    except ValueError:
        print("\033[91m✖ Error: Ingrese un ID numérico válido.\033[0m")
    except PrestamoNoEncontrado as exc:
        print(f"\033[91m✖ Error de Negocio: {exc}\033[0m")
    except PrestamoYaDevuelto as exc:
        print(f"\033[91m✖ Advertencia de Estado: {exc}\033[0m")


def menu_mostrar_prestamos_abiertos(servicio: PrestamoServicio) -> None:
    print("\n" + "=" * 90)
    print("PRÉSTAMOS VIGENTES (ABIERTOS)")
    print("=" * 90)
    prestamos = servicio.listar_prestamos_abiertos()
    if not prestamos:
        print("  No hay préstamos pendientes de devolución.")
        return

    print(f"{'PRÉSTAMO':<9} | {'SOCIO':<20} | {'CÓDIGO':<16} | {'TÍTULO LIBRO':<24} | {'FECHA':<11} | {'LÍMITE':<11}")
    print("-" * 90)
    for p in prestamos:
        print(f"#{p.id_prestamo:<8} | {p.socio[:18]:<20} | {p.codigo_ejemplar:<16} | {p.titulo_libro[:22]:<24} | {str(p.fecha_prestamo):<11} | {str(p.fecha_limite):<11}")
    print("-" * 90)
    print(f"Total préstamos activos: {len(prestamos)}")


# =============================================================================
# BUCLE PRINCIPAL
# =============================================================================

def main() -> None:
    inicializar_base_datos()
    uow = UnidadTrabajoSQLAlchemy()
    sembrar_datos_si_vacio(uow)

    servicio_catalogo = CatalogoServicio(uow)
    servicio_prestamos = PrestamoServicio(uow)

    while True:
        print("\n" + "╔" + "═" * 46 + "╗")
        print("║              BIBLIOTECA ORM                  ║")
        print("╠" + "═" * 46 + "╣")
        print("║  1. Listar libros                            ║")
        print("║  2. Buscar libros                            ║")
        print("║  3. Crear libro                              ║")
        print("║  4. Actualizar precio                        ║")
        print("║  5. Desactivar libro                         ║")
        print("║  6. Registrar préstamo                       ║")
        print("║  7. Devolver préstamo                        ║")
        print("║  8. Mostrar préstamos abiertos               ║")
        print("║  9. Salir                                    ║")
        print("╚" + "═" * 46 + "╝")

        opcion = input("Seleccione una opción (1-9): ").strip()

        if opcion == "1":
            menu_listar_libros(servicio_catalogo)
        elif opcion == "2":
            menu_buscar_libros(servicio_catalogo)
        elif opcion == "3":
            menu_crear_libro(servicio_catalogo)
        elif opcion == "4":
            menu_actualizar_precio(servicio_catalogo)
        elif opcion == "5":
            menu_desactivar_libro(servicio_catalogo)
        elif opcion == "6":
            menu_registrar_prestamo(servicio_prestamos)
        elif opcion == "7":
            menu_devolver_prestamo(servicio_prestamos)
        elif opcion == "8":
            menu_mostrar_prestamos_abiertos(servicio_prestamos)
        elif opcion == "9":
            print("\n¡Gracias por utilizar el Sistema de Gestión de Biblioteca ORM!\n")
            sys.exit(0)
        else:
            print("\033[93mOpción no válida. Por favor, seleccione un número entre 1 y 9.\033[0m")


if __name__ == "__main__":
    main()
