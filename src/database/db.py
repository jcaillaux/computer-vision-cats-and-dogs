from sqlmodel import SQLModel, Session, create_engine
from sqlalchemy import URL
from sqlalchemy.exc import IntegrityError
from .models import *
from config.settings import PG_CONFIG, MODEL_CONFIG

db_url = URL.create(
    drivername = "postgresql+psycopg2",
    username   = PG_CONFIG["user"],
    password   = PG_CONFIG["password"],
    host       = PG_CONFIG["host"],
    port       = PG_CONFIG["port"],
    database   = PG_CONFIG["database"],
)

def make_engine():
    global db_url
    if db_url:
        return create_engine(db_url, echo=True)
    return None

def create_tables():
    engine = make_engine()
    SQLModel.metadata.create_all(engine)

def drop_tables():
    engine = make_engine()
    SQLModel.metadata.drop_all(engine)

def insert(row):
    engine = make_engine()
    with Session(engine) as session:
        try : 
            session.add(row)
            session.commit()
        except IntegrityError as e:
            session.rollback()
    return row

def insert_feedback(uuid:str, grade: int):

    feedback = Feedback(uuid=uuid, grade=grade)
    return insert(feedback)

def update_feedback(uuid: str, grade: int):
    engine = make_engine()
    with Session(engine) as session:
        feedback = session.get(Feedback, uuid)
        if feedback:
            feedback.grade = grade
            feedback.timestamp = get_utc_timestamp()
            session.add(feedback)
            session.commit()
        else :
            raise ValueError(f"Feedback with id {uuid} not found")
def insert_image_metadata(hash:str, filename:str, ext_type:str, size_w:int, size_h:int, color_mode:int):
    image_metadata = ImageMetadata(
        hash=hash,
        filename=filename,
        ext_type=ext_type,
        size_w=size_w,
        size_h=size_h,
        color_mode=color_mode
    )
    return insert(image_metadata)

def insert_prediction(uuid:str, image_id:str, inference_time_ms:float, success:bool, prediction):
    monitoring = PredictionLog(
        uuid=uuid,
        prob_cat=prediction["p_cat"],
        prob_dog=prediction["p_dog"],
        inference_time_ms=inference_time_ms,
        success=success,
        image_id=image_id
    )
    return insert(monitoring)

if __name__ == "__main__":
    create_tables()
    #drop_tables()