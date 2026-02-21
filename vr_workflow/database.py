from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = "sqlite:///tasks.db"

engine = create_engine(DATABASE_URL, echo=False)

session = SessionLocal()

Base = declarative_base()
