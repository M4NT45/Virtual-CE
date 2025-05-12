import models.DB_class as db
from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime

class YamlPath(db.Base):
    __tablename__ = 'yaml_paths'
    id = Column(Integer, primary_key=True)
    subsystem = Column(String(100), nullable=False)
    path = Column(String(255), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.now)