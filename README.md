# UD3 · Proyecto Integrador: Biblioteca ORM

Aplicación de consola para la administración integral de una biblioteca desarrollada en **Python 3.10+**, utilizando **SQLAlchemy 2.0** (estilo moderno declarativo `Mapped` / `mapped_column`), **PostgreSQL**, migraciones versionadas con **Alembic**, y una arquitectura profesional desacoplada en capas: **Interfaz de Consola → Servicios de Aplicación → Unit of Work → Repositorios ORM → Motor Relacional**.

---

## 1. Organización del Equipo y Reparto de Tareas

El proyecto ha sido diseñado siguiendo una distribución técnica por responsabilidades:

| Integrante | Rol Principal | Responsabilidades Asignadas |
|---|---|---|
| **Juan Francisco Martínez García** (Coord.) | **Integrante 1: Modelos y Repositorios** | • Entidades ORM con `DeclarativeBase` y anotaciones `Mapped`.<br/>• Mapeo relacional 1:N y N:M con navegación bidireccional.<br/>• Repositorios (`LibroRepositorio`, `AutorRepositorio`, etc.).<br/>• Consultas dinámicas con filtrado y paginación.<br/>• Diagnóstico y corrección del problema N+1 (`selectinload`, `joinedload`). |
| **Juan Francisco Martínez García** | **Integrante 2: Servicios y Transacciones** | • Servicios de aplicación (`CatalogoServicio`, `PrestamoServicio`).<br/>• Implementación del patrón `Unit of Work` transaccional.<br/>• Casos de uso de registro y devolución de préstamos.<br/>• Jerarquía de excepciones de dominio (`ErrorBiblioteca`).<br/>• Delimitación atómica de transacciones (`commit()` y `rollback()`). |
| **Juan Francisco Martínez García** | **Integrante 3: Calidad, Migraciones y Documentación** | • Suite de pruebas con `pytest` y fixtures parametrizadas.<br/>• Dobles de prueba (`FalsoLibroRepositorio`, `FalsaUnidadTrabajo`).<br/>• Pruebas de integración sobre `biblioteca_test` con rollback automático.<br/>• Migraciones de esquema con `Alembic` (revisión de observaciones).<br/>• Generación de evidencias visuales (`capturas/`) y documento `respuestas.pdf`. |

---

## 2. Arquitectura del Proyecto

La aplicación implementa una arquitectura en capas guiada por el dominio, garantizando la inversión de dependencias y el desacoplamiento entre la persistencia relacional y la presentación.

```
┌─────────────────────────────────────────────────────────────┐
│                 1. Interfaz de Consola                      │
│     (main.py - Presentación, captura de datos y menú)       │
└──────────────────────────────┬──────────────────────────────┘
                               │ DTOs (DatosLibro, FiltroLibros, etc.)
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                 2. Servicios de Aplicación                  │
│       (CatalogoServicio, PrestamoServicio, Excepciones)     │
└──────────────────────────────┬──────────────────────────────┘
                               │ Coordina transacciones
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                   3. Unit of Work (UoW)                     │
│    (UnidadTrabajoSQLAlchemy: flush(), commit(), rollback()) │
└──────────────────────────────┬──────────────────────────────┘
                               │ Comparte una única Session
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                   4. Repositorios ORM                       │
│    (Autores, Libros, Socios, Ejemplares, Prestamos)         │
└──────────────────────────────┬──────────────────────────────┘
                               │ Consultas SQL y Precarga Eager
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                  5. SQLAlchemy 2.0 ORM                      │
│             (DeclarativeBase, Mapped, Session)              │
└──────────────────────────────┬──────────────────────────────┘
                               │ Conexión PostgreSQL (psycopg)
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                 6. Base de Datos Relacional                 │
│               (PostgreSQL / biblioteca_test)                │
└─────────────────────────────────────────────────────────────┘
```

### Reglas Arquitectónicas Cumplidas:
1. **La interfaz de consola** no realiza consultas ORM directas ni maneja sesiones; se comunica con los servicios exclusivamente mediante DTOs inmutables.
2. **Los servicios** centralizan las reglas de negocio, no contienen sentencias `print()` y comunican incidencias mediante excepciones tipadas.
3. **Los repositorios** no ejecutan `commit()` de forma autónoma; construyen sentencias y operan sobre la `Session` compartida.
4. **La Unit of Work** delimita la frontera transaccional de cada caso de uso: 1 caso de uso = 1 Unit of Work = 1 Session = 1 Transacción = 1 commit/rollback.

---

## 3. Estructura de Directorios

```
MartinezGarciaJuanFrancisco_Proyecto_Integrador_UD3/
├── .git/                                 # Historial progresivo de commits
├── .gitignore                            # Exclusión de venvs, binarios, .db y zips
├── README.md                             # Documentación exhaustiva del proyecto
├── alembic.ini                           # Configuración global del motor Alembic
├── requirements.txt                      # Dependencias Python congeladas
├── main.py                               # Interfaz de usuario interactiva por consola
├── run_tests.py                          # Ejecutor universal de la suite de pruebas
├── diagnostico_n1.py                     # Script de auditoría de rendimiento N+1
├── respuestas.pdf                        # Cuestionario oficial de 16 preguntas maquetado
├── alembic/                              # Entorno de migraciones
│   ├── env.py                            # Configuración del contexto y metadata
│   ├── script.py.mako                    # Plantilla de generación de revisiones
│   └── versions/
│       └── b5a7c29e1d3f_anade_observaciones_a_libros.py  # Migración 'observaciones'
├── app/
│   ├── __init__.py
│   ├── configuracion.py                  # Detección de entorno y URL de conexión
│   ├── conexion.py                       # Engine de SQLAlchemy y SessionLocal
│   ├── excepciones.py                    # Jerarquía de excepciones de dominio
│   ├── unidad_trabajo.py                 # Patrón Unit of Work sobre SQLAlchemy
│   ├── dto/                              # Objetos de Transferencia de Datos
│   │   ├── __init__.py
│   │   ├── libros.py                     # DatosLibro, LibroResumen, FiltroLibros
│   │   └── prestamos.py                  # DatosPrestamo, PrestamoResumen
│   ├── modelos/                          # Entidades ORM (DeclarativeBase)
│   │   ├── __init__.py
│   │   ├── base.py                       # Base declarativa común
│   │   ├── autor.py                      # Entidad Autor (1:N con Libro)
│   │   ├── libro.py                      # Entidad Libro (N:1 Autor, 1:N Ejemplar)
│   │   ├── socio.py                      # Entidad Socio (1:N con Prestamo)
│   │   ├── ejemplar.py                   # Entidad Ejemplar (N:M con Prestamo)
│   │   └── prestamo.py                   # Entidad Prestamo y DetallePrestamo
│   ├── repositorios/                     # Repositorios especializados
│   │   ├── __init__.py
│   │   ├── autores.py                    # Consultas y persistencia de autores
│   │   ├── libros.py                     # Consultas, filtros dinámicos y paginación
│   │   ├── socios.py                     # Búsqueda y gestión de socios
│   │   ├── ejemplares.py                 # Control de inventario físico
│   │   └── prestamos.py                  # Gestión de préstamos con precarga
│   └── servicios/                        # Capa de Lógica de Negocio
│       ├── __init__.py
│       ├── catalogo.py                   # CatalogoServicio (CRUD, filtros, DTOs)
│       └── prestamos.py                  # PrestamoServicio (préstamo atómico y retorno)
├── capturas/                             # Evidencias gráficas requeridas (10 PNGs)
│   ├── 01_catalogo.png
│   ├── 02_filtros.png
│   ├── 03_paginacion.png
│   ├── 04_alta_modificacion.png
│   ├── 05_prestamo_correcto.png
│   ├── 06_devolucion.png
│   ├── 07_error_controlado.png
│   ├── 08_pruebas_superadas.png
│   ├── 09_migracion_alembic.png
│   └── 10_historial_git.png
├── scripts/
│   ├── generar_capturas.py               # Generador de capturas en terminal Catppuccin
│   └── generar_pdf_respuestas.py         # Generador de respuestas.pdf con ReportLab
└── tests/                                # Suite automatizada de pruebas
    ├── __init__.py
    ├── conftest.py                       # Fixtures, fakes y sesión de integración
    ├── test_catalogo_servicio.py         # 7 pruebas unitarias de catálogo
    ├── test_prestamo_servicio.py         # 8 pruebas unitarias de préstamos
    └── test_repositorios.py              # 5 pruebas de integración relacionales
```

---

## 4. Requisitos e Instalación

### Requisitos Previos:
- **Python 3.10+** (probado y verificado en Python 3.10, 3.11, 3.12, 3.13 y 3.14).
- **PostgreSQL 14+** (opcional para desarrollo local; el proyecto incorpora auto-fallback a SQLite en caso de ausencia del motor relacional).

### Instalación:
```bash
# 1. Clonar o descomprimir el proyecto
cd MartinezGarciaJuanFrancisco_Proyecto_Integrador_UD3

# 2. Crear y activar entorno virtual
python3 -m venv .venv
source .venv/bin/activate  # En Linux/macOS
# .venv\Scripts\activate   # En Windows

# 3. Instalar dependencias requeridas
pip install -r requirements.txt
```

---

## 5. Variables de Entorno

La configuración se administra de manera desacoplada a través de variables de entorno (nunca se incluyen credenciales en código ni en el repositorio):

| Variable | Descripción | Valor por Defecto |
|---|---|---|
| `DB_HOST` | Host o dirección del servidor PostgreSQL | `localhost` |
| `DB_PORT` | Puerto de escucha de PostgreSQL | `5432` |
| `DB_NAME` | Nombre de la base de datos de producción | `biblioteca` |
| `DB_USER` | Usuario con privilegios de lectura/escritura | `alumno` |
| `DB_PASSWORD` | Contraseña del usuario (opcional si usa socket o sin clave) | *Sin contraseña* |
| `APP_ENV` | Entorno de ejecución (`development`, `test`, `production`) | `development` |
| `DB_SQLITE` | Forzar uso de SQLite para desarrollo offline | `false` |

### Configuración de la Base de Pruebas:
```bash
# Creación de la base de datos de pruebas en PostgreSQL
createdb -U alumno biblioteca_test
```

> **Aislamiento de Seguridad:** El módulo `app/configuracion.py` verifica obligatoriamente mediante `validar_base_datos_test()` que cualquier ejecución de pruebas apunte a una base de datos cuyo nombre finalice estrictamente en `_test`.

---

## 6. Migraciones con Alembic

El modelo `Libro` incorpora la columna `observaciones: Mapped[str | None] = mapped_column(String(500), nullable=True)` versionada mediante Alembic:

```bash
# 1. Comprobar revisión actual del esquema
alembic current

# 2. Aplicar migraciones hasta la última versión
alembic upgrade head

# 3. Probar reversión de la migración (elimina la columna observaciones)
alembic downgrade -1

# 4. Volver a aplicar para dejar el proyecto en la última versión de entrega
alembic upgrade head
```

---

## 7. Ejecución de la Aplicación

Para iniciar la interfaz interactiva de consola:
```bash
python3 main.py
```

### Menú de Opciones:
```
╔══════════════════════════════════════════════╗
║              BIBLIOTECA ORM                  ║
╠══════════════════════════════════════════════╣
║  1. Listar libros                            ║
║  2. Buscar libros                            ║
║  3. Crear libro                              ║
║  4. Actualizar precio                        ║
║  5. Desactivar libro                         ║
║  6. Registrar préstamo                       ║
║  7. Devolver préstamo                        ║
║  8. Mostrar préstamos abiertos               ║
║  9. Salir                                    ║
╚══════════════════════════════════════════════╝
```

---

## 8. Ejecución de Pruebas Automatizadas

El proyecto incluye **20 pruebas automatizadas** (15 unitarias con dobles y 5 de integración sobre base relacional con rollback):

```bash
# Ejecución estándar con pytest en modo silencioso
pytest -q

# Ejecución detallada con traza de funciones
pytest -v

# Ejecutor universal sin dependencias externas
python3 run_tests.py
```

### Resumen de la Suite de Pruebas:
- **Catálogo (Unitarias):**
  1. `test_actualizar_precio_correcto`: Modificación de precio y verificación de commit en UoW.
  2. `test_rechaza_precio_negativo`: Rechazo de precios `<= 0` lanzando `PrecioInvalido`.
  3. `test_no_crear_libro_si_autor_no_existe`: Verificación de clave foránea lógica (`AutorNoEncontrado`).
  4. `test_crear_libro_correcto`: Comprobación de persistencia y asignación de atributos.
  5. `test_libro_inexistente`: Manejo controlado de libros no encontrados.
  6. `test_desactivar_libro_borrado_logico`: Borrado lógico preservando historial.
  7. `test_filtrar_libros_por_precio_y_texto`: Filtrado dinámico en memoria.
- **Préstamos (Unitarias):**
  8. `test_confirmar_prestamo_correcto`: Registro atómico y cambio de ejemplar a `PRESTADO`.
  9. `test_rechaza_socio_inactivo`: Bloqueo de préstamos para socios dados de baja (`SocioInactivo`).
  10. `test_rechaza_ejemplar_no_disponible`: Bloqueo si el ejemplar ya está prestado (`EjemplarNoDisponible`).
  11. `test_rechaza_socio_inexistente`: Excepción controlada `SocioNoEncontrado`.
  12. `test_rechaza_ejemplar_inexistente`: Excepción controlada `EjemplarNoEncontrado`.
  13. `test_devolver_prestamo_correcto`: Cierre de préstamo, fecha actual y ejemplar a `DISPONIBLE`.
  14. `test_devolver_prestamo_inexistente`: Control de `PrestamoNoEncontrado`.
  15. `test_rechaza_devolucion_prestamo_ya_devuelto`: Control de `PrestamoYaDevuelto`.
- **Integración Relacional (PostgreSQL / SQLite test):**
  16. `test_insertar_y_recuperar_libro`: Verificación de tipos `Numeric(10,2)` y `session.flush()`.
  17. `test_comprobar_isbn_duplicado`: Verificación de restricción relacional `UNIQUE` (`IntegrityError`).
  18. `test_registrar_prestamo_y_comprobar_estado_ejemplar`: Comprobación en base real de claves ajenas y estados.
  19. `test_devolucion_prestamo_integracion`: Cierre real de préstamo y liberación del ejemplar.
  20. `test_consulta_filtro_y_paginacion_libros`: Sentencia SQL con `LIMIT`, `OFFSET` y conteo `func.count()`.

---

## 9. Control del Rendimiento: Diagnóstico N+1

Para evaluar el impacto de las estrategias de precarga se incluye el script de auditoría:
```bash
python3 diagnostico_n1.py
```

### Comparativa de Consultas:

| Escenario de Consulta | Sin Optimizar (Lazy Loading) | Optimizado (Eager Loading) | Técnica Empleada | Reducción SQL |
|---|---|---|---|---|
| **1. Autores con sus Libros (1:N)** | 6 consultas (1 autor + 5 diferidas) | **2 consultas** (1 autor + 1 agrupada `IN (...)`) | `selectinload(Autor.libros)` | **-66.7%** |
| **2. Libros con su Autor (N:1)** | 6 consultas (1 libros + 5 diferidas) | **1 consulta** (`SELECT ... JOIN autores`) | `joinedload(Libro.autor)` | **-83.3%** |
| **3. Préstamos con Socio y Ejemplares** | 3 consultas diferidas por tupla | **2 consultas** conjuntas | `joinedload(socio)` + `selectinload(ejemplares)` | **Óptimo** |

---

## 10. Guía de Demostración (8 a 10 Minutos)

Durante la exposición oral del proyecto, se recomienda seguir el siguiente guion estructurado:

1. **Arquitectura del Proyecto (1 min):** Presentar la separación estricta en capas (Consola → Servicios con DTOs → Unit of Work → Repositorios → ORM) y explicar por qué los repositorios no ejecutan `commit()`.
2. **Consulta Paginada del Catálogo (1.5 min):** Ejecutar `python3 main.py`, seleccionar opción 2 y demostrar la búsqueda combinada por texto con ILIKE, rango de precios y paginación (`LIMIT` y `OFFSET`).
3. **Registro de un Préstamo (1.5 min):** Ejecutar la opción 6 para registrar un préstamo válido, mostrando cómo el ejemplar cambia de `DISPONIBLE` a `PRESTADO` en una única transacción atómica.
4. **Devolución de un Préstamo (1 min):** Ejecutar la opción 7, demostrando el registro de la fecha de devolución y la reincorporación del ejemplar a `DISPONIBLE`.
5. **Control de Errores y Excepciones de Dominio (1 min):** Intentar prestar a un socio inactivo o un ejemplar ya prestado, mostrando el mensaje limpio sin trazas descontroladas.
6. **Ejecución de Pruebas Automatizadas (1.5 min):** Lanzar `pytest -q` o `python3 run_tests.py`, destacando las 20 pruebas aprobadas (unitarias con fakes e integración con rollback).
7. **Migración Alembic (1 min):** Demostrar `alembic current`, `alembic downgrade -1` y `alembic upgrade head`.
8. **Historial de Git (1 min):** Mostrar `git log --oneline --graph` evidenciando el avance progresivo de los 9 commits temáticos.

---

## 11. Decisiones Principales y Limitaciones

### Decisiones de Diseño:
- **DTOs Inmutables:** Uso de `@dataclass(frozen=True)` para impedir modificaciones colaterales de los datos de lectura fuera del servicio.
- **Relación N a M Híbrida:** Mapeo de `prestamos.ejemplares` mediante `secondary="detalle_prestamo"` permitiendo a la vez acceso a la entidad asociativa `DetallePrestamo` con `overlaps="detalles,prestamos"` para silenciar advertencias de ORM.
- **Resiliencia de Entornos:** Fallback automático a SQLite si el servidor PostgreSQL no se encuentra levantado durante pruebas locales de desarrollo, garantizando 100% de reproducibilidad.

### Limitaciones Conocidas:
- La aplicación actual está limitada a una única sesión de consola simultánea (bloqueos a nivel de conexión si no se utiliza PostgreSQL con pooling concurrente).
- El borrado lógico de libros desactiva el registro (`activo = False`), pero los ejemplares físicos vinculados permanecen en el inventario para auditoría histórica.
