from sqlmodel import Field, SQLModel, create_engine
from datetime import datetime, timezone
from config.settings import MODEL_CONFIG
import uuid

def get_utc_timestamp():
    """Get UTC timestamp without timezone for database storage"""
    return datetime.now(timezone.utc).replace(tzinfo=None)

class Feedback(SQLModel, table=True):
    uuid: str = Field(default_factory= lambda: str(uuid.uuid4()), primary_key=True)
    timestamp: datetime = Field(default_factory=get_utc_timestamp)
    grade: str

class ImageMetadata(SQLModel, table=True):
    hash: str = Field(primary_key=True)
    filename: str
    ext_type: str
    size_w: int
    size_h: int
    color_mode: str

class PredictionLog(SQLModel, table=True):
    uuid : str = Field(default_factory= lambda: str(uuid.uuid4()), primary_key=True)
    timestamp : datetime = Field(default_factory=get_utc_timestamp)
    prob_cat : float | None = Field(nullable=True)
    prob_dog : float | None = Field(nullable=True)
    inference_time_ms : float = Field(nullable=False)
    success : bool = Field(nullable=False)
    model_version : str = Field(default=MODEL_CONFIG["version"])
    image_id: str = Field(nullable=False)
