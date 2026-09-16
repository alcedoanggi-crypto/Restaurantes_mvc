"""Configuración de la aplicación."""
import os
from pathlib import Path

from dotenv import load_dotenv

basedir = Path(__file__).resolve().parent
load_dotenv(basedir / ".env")


def _normalize_db_url(url: str) -> str:
    """Normaliza la URL de conexión.

    - `postgres://` (Heroku y otros) -> `postgresql://`
    - Fuerza el driver `psycopg` (v3) porque psycopg2 no compila en Python 3.13.
    """
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-cambia-esto")

    SQLALCHEMY_DATABASE_URI = _normalize_db_url(
        os.environ.get("DATABASE_URL", f"sqlite:///{basedir / 'restaurante.db'}")
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}

    # Facturación
    IVA = float(os.environ.get("IVA", "0.16"))

    # Paginación de listados
    ITEMS_PER_PAGE = 12

    # Umbrales (minutos) para el semáforo del KDS
    KDS_WARN_MIN = int(os.environ.get("KDS_WARN_MIN", "8"))
    KDS_LATE_MIN = int(os.environ.get("KDS_LATE_MIN", "15"))
