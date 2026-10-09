from collections.abc import Iterator
from functools import lru_cache

from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, Session

from skill_inventory.config import database_url


class Base(DeclarativeBase):
    pass


@lru_cache
def get_engine():
    return create_engine(database_url(), pool_pre_ping=True, connect_args={"connect_timeout": 5})


def get_session() -> Iterator[Session]:
    with Session(get_engine()) as session:
        yield session


def check_database() -> None:
    with get_engine().connect() as connection:
        connection.execute(text("SELECT 1"))
