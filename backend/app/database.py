import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

# PostgreSQL is the primary database
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/loan_db")
USE_SQLITE = os.getenv("USE_SQLITE", "false").lower() in ("true", "1", "yes")

if USE_SQLITE:
    DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "loan_agent.db")
    DATABASE_URL = f"sqlite:///{DB_PATH}"
    connect_args = {"check_same_thread": False}
else:
    connect_args = {}

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
