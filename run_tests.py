#!/usr/bin/env python3
"""
Ejecutor de pruebas unitarias y de integración para la Biblioteca ORM.
Permite ejecutar la suite completa tanto con 'pytest -q' como directamente con 'python3 run_tests.py'.
"""

import sys
import time

try:
    import pytest
    TIENE_PYTEST = True
except ImportError:
    TIENE_PYTEST = False


def ejecutar_con_runner_nativo():
    import tests.conftest as c
    import tests.test_catalogo_servicio as tc
    import tests.test_prestamo_servicio as tp
    import tests.test_repositorios as tr

    print("=" * 70)
    print("SUITE DE PRUEBAS AUTOMATIZADAS - BIBLIOTECA ORM")
    print("=" * 70)

    total_pruebas = 0
    superadas = 0
    errores = []

    def correr(nombre, fn, *args):
        nonlocal total_pruebas, superadas
        total_pruebas += 1
        sys.stdout.write(f"  • {nombre:<55} ")
        sys.stdout.flush()
        try:
            fn(*args)
            print("\033[92m[PASÓ]\033[0m")
            superadas += 1
        except Exception as exc:
            print("\033[91m[FALLÓ]\033[0m")
            errores.append((nombre, exc))

    inicio = time.time()

    # 1. Pruebas Unitarias de Catálogo
    print("\n[CAPA DE SERVICIOS - CATÁLOGO (PRUEBAS UNITARIAS)]")
    autor = c.autor_demo()

    def _test_act_precio():
        l = c.libro(autor)
        tc.test_actualizar_precio_correcto(l, c.uow_falsa(l, autor))
    correr("Actualizar precio correcto", _test_act_precio)

    def _test_rechaza_neg():
        l = c.libro(autor)
        tc.test_rechaza_precio_negativo(l, c.uow_falsa(l, autor))
    correr("Rechazar precio negativo o cero", _test_rechaza_neg)

    correr("No crear libro si autor no existe", lambda: tc.test_no_crear_libro_si_autor_no_existe(c.uow_falsa(None, autor)))
    correr("Crear libro correctamente", lambda: tc.test_crear_libro_correcto(autor, c.uow_falsa(None, autor)))
    correr("Control de libro inexistente", lambda: tc.test_libro_inexistente(c.uow_falsa(None, autor)))

    def _test_desactivar():
        l = c.libro(autor)
        tc.test_desactivar_libro_borrado_logico(l, c.uow_falsa(l, autor))
    correr("Desactivación lógica de libro", _test_desactivar)

    def _test_filtro():
        l = c.libro(autor)
        tc.test_filtrar_libros_por_precio_y_texto(l, c.uow_falsa(l, autor))
    correr("Filtro dinámico y paginación en memoria", _test_filtro)

    # 2. Pruebas Unitarias de Préstamos
    print("\n[CAPA DE SERVICIOS - PRÉSTAMOS (PRUEBAS UNITARIAS)]")
    libro = c.libro(autor)
    correr("Confirmar préstamo correcto (atómico)", lambda: tp.test_confirmar_prestamo_correcto(c.socio_activo(), c.ejemplar_disponible(libro)))
    correr("Rechazar préstamo a socio inactivo", lambda: tp.test_rechaza_socio_inactivo(c.socio_inactivo(), c.ejemplar_disponible(libro)))
    correr("Rechazar ejemplar no disponible", lambda: tp.test_rechaza_ejemplar_no_disponible(c.socio_activo(), c.ejemplar_prestado(libro)))
    correr("Rechazar préstamo con socio inexistente", lambda: tp.test_rechaza_socio_inexistente(c.ejemplar_disponible(libro)))
    correr("Rechazar préstamo con ejemplar inexistente", lambda: tp.test_rechaza_ejemplar_inexistente(c.socio_activo()))
    correr("Devolver préstamo correctamente", lambda: tp.test_devolver_prestamo_correcto(c.socio_activo(), c.ejemplar_prestado(libro)))
    correr("Devolver préstamo inexistente", lambda: tp.test_devolver_prestamo_inexistente())
    correr("Rechazar devolución de préstamo ya devuelto", lambda: tp.test_rechaza_devolucion_prestamo_ya_devuelto(c.socio_activo(), c.ejemplar_disponible(libro)))

    # 3. Pruebas de Integración con Base de Datos
    print("\n[CAPA DE PERSISTENCIA Y REPOSITORIOS (PRUEBAS DE INTEGRACIÓN)]")
    engine = c.engine_test()

    def probar_con_sesion(fn):
        gen = c.session(engine)
        ses = next(gen)
        try:
            fn(ses)
        finally:
            try:
                next(gen)
            except StopIteration:
                pass

    correr("Insertar y recuperar libro en BD real", lambda: probar_con_sesion(tr.test_insertar_y_recuperar_libro))
    correr("Restricción de ISBN duplicado (IntegrityError)", lambda: probar_con_sesion(tr.test_comprobar_isbn_duplicado))
    correr("Registrar préstamo y verificar estado en BD", lambda: probar_con_sesion(tr.test_registrar_prestamo_y_comprobar_estado_ejemplar))
    correr("Devolución de préstamo en BD real", lambda: probar_con_sesion(tr.test_devolucion_prestamo_integracion))
    correr("Consulta con filtros y paginación SQL", lambda: probar_con_sesion(tr.test_consulta_filtro_y_paginacion_libros))

    duracion = time.time() - inicio
    print("\n" + "=" * 70)
    print(f"RESULTADO: {superadas}/{total_pruebas} pruebas superadas en {duracion:.2f} segundos.")
    if errores:
        print("\nDetalle de errores:")
        for nombre, exc in errores:
            print(f"- {nombre}: {exc}")
        return 1

    print("\033[92mTODAS LAS PRUEBAS QUEDARON SUPERADAS SATISFACTORIAMENTE.\033[0m")
    print("=" * 70)
    return 0


def main():
    if TIENE_PYTEST and len(sys.argv) > 1 and sys.argv[1] in ("-q", "-v", "tests"):
        return pytest.main(sys.argv[1:])
    return ejecutar_con_runner_nativo()


if __name__ == "__main__":
    sys.exit(main())
