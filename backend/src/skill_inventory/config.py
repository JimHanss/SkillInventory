import os

from sqlalchemy import URL


def database_url() -> URL | str:
    if value := os.getenv("DATABASE_URL"):
        return value
    return URL.create(
        "postgresql+psycopg",
        username=os.getenv("POSTGRES_USER", "skill_inventory"),
        password=os.getenv("POSTGRES_PASSWORD", ""),
        host=os.getenv("POSTGRES_HOST", "db"),
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        database=os.getenv("POSTGRES_DB", "skill_inventory"),
    )
