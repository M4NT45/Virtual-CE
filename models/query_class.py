import models.DB_class as db
from sqlalchemy import Column, Integer, String, Date, Text, DateTime, Boolean
from datetime import datetime

class Query(db.Base):
    __tablename__ = 'queries'
    
    id = Column(Integer, primary_key=True)
    text = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.now)

    clarification_requested = Column(Boolean, default=False)
    clarification_type = Column(String(50), nullable=True)

    processed_text = Column(Text, nullable=True)
    enhanced_text = Column(Text, nullable=True)

    engine_type = Column(String(20), nullable=True)

    parent_query_id = Column(Integer, nullable=True)
