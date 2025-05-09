from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class YamlPath(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subsystem = db.Column(db.String(100), nullable=False)
    path = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.now())

class Query(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.now())