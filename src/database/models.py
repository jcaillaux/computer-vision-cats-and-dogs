from sqlmodel import Field, SQLModel, create_engine


class Feedback(SQLModel, table=True):
    uiid: int | None = Field(default=None, primary_key=True)
    timestamp: str
    grade: str

class Prediction(SQLModel, table=True):
    uuid : int | None = Field(default=None, primary_key=True)
    timestamp : str
    probability_cat : float
    probability_dog : float
    inference_time : float
