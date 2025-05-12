import models.DB_class as db
from sqlalchemy import Column, Integer, String, Date, Text, DateTime
from datetime import datetime

class Query(db.Base):
    __tablename__ = 'queries'
    id = Column(Integer, primary_key=True)
    text = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.now)