import logging
from sqlalchemy import text
from sqlmodel import SQLModel, Session, create_engine
from app.config import get_settings
from contextlib import contextmanager

logger = logging.getLogger(__name__)

engine = create_engine(
    get_settings().database_uri, 
    echo=get_settings().env.lower() in ["dev", "development", "test", "testing", "staging"],
    pool_size=get_settings().db_pool_size,
    max_overflow=get_settings().db_additional_overflow,
    pool_timeout=get_settings().db_pool_timeout,
    pool_recycle=get_settings().db_pool_recycle,
)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
    _ensure_workout_image_column()
    _ensure_routine_workout_columns()


def _ensure_workout_image_column():
    with engine.begin() as conn:
        dialect = conn.dialect.name
        if dialect == "sqlite":
            columns = conn.exec_driver_sql("PRAGMA table_info(workout)").fetchall()
            column_names = {row[1] for row in columns}
            if "image_url" not in column_names:
                conn.exec_driver_sql("ALTER TABLE workout ADD COLUMN image_url VARCHAR")
            return

        conn.execute(text("ALTER TABLE workout ADD COLUMN IF NOT EXISTS image_url VARCHAR"))


def _ensure_routine_workout_columns():
    with engine.begin() as conn:
        dialect = conn.dialect.name
        if dialect == "sqlite":
            columns = conn.exec_driver_sql("PRAGMA table_info(routineworkout)").fetchall()
            column_names = {row[1] for row in columns}
            if "order" not in column_names:
                conn.exec_driver_sql("ALTER TABLE routineworkout ADD COLUMN " + '"order" INTEGER DEFAULT 0')
            if "notes" not in column_names:
                conn.exec_driver_sql("ALTER TABLE routineworkout ADD COLUMN notes VARCHAR DEFAULT ''")
            return

        conn.execute(text('ALTER TABLE routineworkout ADD COLUMN IF NOT EXISTS "order" INTEGER DEFAULT 0'))
        conn.execute(text("ALTER TABLE routineworkout ADD COLUMN IF NOT EXISTS notes VARCHAR DEFAULT ''"))

def drop_all():
    SQLModel.metadata.drop_all(bind=engine)
    
def _session_generator():
    with Session(engine) as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()

def get_session():
    yield from _session_generator()

@contextmanager
def get_cli_session():
    yield from _session_generator()
