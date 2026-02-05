from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from typing import Generator
import os
from urllib.parse import quote_plus
from dotenv import load_dotenv

load_dotenv()

DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "genworx")
DB_HOST = os.getenv("DB_HOST", "postgres-service")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "ecommerce")

DB_PASSWORD_ENCODED = quote_plus(DB_PASSWORD)

DATABASE_URL = (
    f"postgresql://{DB_USER}:{DB_PASSWORD_ENCODED}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
