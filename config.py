import os

class Config:
    SQLALCHEMY_DATABASE_URI = 'sqlite:///virtual_chief.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = 'your-secret-key'