from sqlmodel import Session, SQLModel, create_engine

from src.config import DATABASE_URL


connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite:") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)


def create_db_and_tables() -> None:
    # Importar las tablas antes de invocar metadata.create_all.
    from src.models.agenda import Contacto  # noqa: F401
    from src.models.user import Usuario  # noqa: F401

    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
