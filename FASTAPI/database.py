# database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


SQLALCHEMY_DATABASE_URL = "mysql+pymysql://root:Master12$@localhost:3306/comicstore"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"charset": "utf8mb4"})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
