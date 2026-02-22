from pydantic import BaseModel
from datetime import datetime

class SentimentEvent(BaseModel):
    label: str
    confidence: float
    timestamp: datetime
