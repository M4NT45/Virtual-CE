import os

class Config:
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://Mantas:Mantas123@localhost/VCE'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = 'your-secret-key'