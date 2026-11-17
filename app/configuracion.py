import os
from urllib.parse import quote_plus


def validar_base_datos_test(nombre_bd: str) -> None:
    """Verifica que el entorno de pruebas apunte obligatoriamente a una BD de prueba."""
    if not nombre_bd.endswith("_test"):
        raise RuntimeError(
            "Las pruebas requieren una base de datos terminada en '_test'."
        )


def obtener_url_bd(solo_test: bool = False) -> str:
    """
    Construye la URL de conexión a la base de datos a partir de variables de entorno.
    Si se activa DB_SQLITE=true o no hay configuración PostgreSQL, permite SQLite.
    """
    usar_sqlite = os.getenv("DB_SQLITE", "false").lower() in ("true", "1", "yes")
    if usar_sqlite:
        if solo_test or os.getenv("APP_ENV") == "test":
            return "sqlite:///biblioteca_test.db"
        return "sqlite:///biblioteca.db"

    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "5432")
    app_env = os.getenv("APP_ENV", "development")

    nombre_bd_defecto = "biblioteca_test" if (solo_test or app_env == "test") else "biblioteca"
    nombre_bd = os.getenv("DB_NAME", nombre_bd_defecto)

    if solo_test or app_env == "test":
        validar_base_datos_test(nombre_bd)

    usuario = os.getenv("DB_USER", "alumno")
    password = os.getenv("DB_PASSWORD")

    if not usuario:
        raise ValueError("Falta la variable de entorno DB_USER.")

    if password:
        auth = f"{quote_plus(usuario)}:{quote_plus(password)}@"
    else:
        auth = f"{quote_plus(usuario)}@"

    return f"postgresql+psycopg://{auth}{host}:{port}/{nombre_bd}"
