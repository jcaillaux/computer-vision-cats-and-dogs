from sqlmodel import SQLModel, create_engine
from sqlalchemy import URL
from .models import Feedback, Prediction
from config.settings import PG_CONFIG


db_url = URL.create(
    drivername="postgresql+psycopg2",
    username=PG_CONFIG["user"],
    password=PG_CONFIG["password"],
    host=PG_CONFIG["host"],
    port=PG_CONFIG["port"],
    database=PG_CONFIG["database"],
)

def create_tables():
    global db_url
    if db_url:
        engine = create_engine(db_url, echo=True)
        SQLModel.metadata.create_all(engine)

def drop_tables():
    global db_url
    if db_url:
        engine = create_engine(db_url, echo=True)
        SQLModel.metadata.drop_all(engine)

if __name__ == "__main__":
    #create_tables()
    drop_tables()