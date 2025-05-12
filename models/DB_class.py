from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker 

engine = create_engine("mysql+pymysql://Mantas:Mantas123@localhost/VCE")
session_maker = sessionmaker(engine)

class Base(DeclarativeBase):
    pass