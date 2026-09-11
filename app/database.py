# from sqlalchemy import create_engine
# from sqlalchemy.orm import sessionmaker, declarative_base

# # This is the connection string: it tells SQLAlchemy how to reach
# # the exact same Postgres container you already tested.
# DATABASE_URL = "postgresql://eval_admin:#your_password#@localhost:5544/eval_platform"

# engine = create_engine(DATABASE_URL)

# # SessionLocal is a "conversation" with the database we open and close
# # each time we need to read or write something.
# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# # Base is what our table classes (in models.py) will inherit from.
# Base = declarative_base()

# # A small helper FastAPI will use to get a database session per request,
# # and guarantee it always gets closed afterward.
# def get_db():
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()


import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

load_dotenv()

DB_BACKEND = os.getenv("DB_BACKEND", "azure").lower()

if DB_BACKEND == "local":
    DATABASE_URL = "postgresql://eval_admin:#your_password#@localhost:5544/eval_platform"
else:
    DATABASE_URL = os.getenv("AZURE_DATABASE_URL")
    if not DATABASE_URL:
        raise RuntimeError(
            "AZURE_DATABASE_URL is not set. Either set DB_BACKEND=local to use "
            "your local Docker Postgres, or set AZURE_DATABASE_URL in .env."
        )

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
