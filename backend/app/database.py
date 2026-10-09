from datetime import timezone
from sqlalchemy import DateTime, create_engine
from sqlalchemy.types import TypeDecorator
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from . import config

_args = {"check_same_thread": False} if config.DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(config.DATABASE_URL, connect_args=_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class UTCDateTime(TypeDecorator):
    """Always stores UTC and always returns timezone-aware UTC datetimes.

    SQLite silently drops time zones, which made the API send "2026-10-08T12:20:33" (no zone), and browsers then
    read it as local time. With this type the API sends "...+00:00" and the frontend shows Indian time (IST)."""
    impl = DateTime
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc).replace(tzinfo=None)

    def process_result_value(self, value, dialect):
        return None if value is None else value.replace(tzinfo=timezone.utc)


def ensure_columns():
    """Tiny migration: add columns that a newer version of the code expects but an older database file lacks.
    (create_all only creates missing TABLES, never missing columns.) Only nullable columns are added."""
    from sqlalchemy import inspect, text
    insp = inspect(engine)
    with engine.begin() as conn:
        for table in Base.metadata.sorted_tables:
            if not insp.has_table(table.name):
                continue
            have = {c["name"] for c in insp.get_columns(table.name)}
            for col in table.columns:
                if col.name not in have and col.nullable:
                    ddl = col.type.compile(dialect=engine.dialect)
                    conn.execute(text(f'ALTER TABLE {table.name} ADD COLUMN {col.name} {ddl}'))
