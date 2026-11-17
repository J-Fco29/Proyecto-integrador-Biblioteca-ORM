from app.repositorios.autores import AutorRepositorio
from app.repositorios.libros import LibroRepositorio, SQLAlchemyLibroRepositorio
from app.repositorios.socios import SocioRepositorio
from app.repositorios.ejemplares import EjemplarRepositorio
from app.repositorios.prestamos import PrestamoRepositorio

__all__ = [
    "AutorRepositorio",
    "LibroRepositorio",
    "SQLAlchemyLibroRepositorio",
    "SocioRepositorio",
    "EjemplarRepositorio",
    "PrestamoRepositorio",
]
