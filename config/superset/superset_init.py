import logging
import os
from pathlib import Path

from sqlalchemy import create_engine, text

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("biolink.superset_init")


def _database_uri() -> str:
    host = os.getenv("BIOLINK_PG_HOST", "postgres")
    port = os.getenv("BIOLINK_PG_PORT", "5432")
    database = os.getenv("BIOLINK_PG_DB", "biolink")
    user = os.getenv("BIOLINK_PG_USER", "biolink")
    password = os.getenv("BIOLINK_PG_PASSWORD", "biolink_secret")
    return f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}"


def main() -> None:
    upload_folder = Path(os.getenv("SUPERSET_UPLOAD_FOLDER", "/tmp/superset_uploads"))
    upload_folder.mkdir(parents=True, exist_ok=True)
    logger.info("Ensured Superset upload folder exists at %s", upload_folder)

    try:
        engine = create_engine(_database_uri(), pool_pre_ping=True)
        with engine.connect() as conn:
            view_count = conn.execute(text('SELECT COUNT(*) FROM public.ehvol')).scalar()
            registry_count = conn.execute(text('SELECT COUNT(*) FROM public.unified_registry')).scalar()
        engine.dispose()
        logger.info(
            "BioLink source database reachable from Superset init: ehvol=%s unified_registry=%s",
            view_count,
            registry_count,
        )
        logger.info(
            "Superset datasets are provisioned lazily by the BioLink backend integration route."
        )
    except Exception as exc:
        logger.warning("Superset init preflight could not verify BioLink source DB: %s", exc)


if __name__ == "__main__":
    main()
