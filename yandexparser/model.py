from sqlalchemy import create_engine, Column, Integer, String, Text, ForeignKey, Boolean, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import os

db_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'stat.db')
engine = create_engine('sqlite:///{}'.format(db_path))

Base = declarative_base()

Session = sessionmaker(bind=engine)
session = Session()

class Info(Base):

    """Main BD"""
    __tablename__ = 'info'
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=True)
    type = Column(String(255), nullable=True)
    kitchen = Column(String(255), nullable=True)
    menu = Column(Text, nullable=True)
    raiting = Column(String(255), nullable=True)
    description = Column(String(255), nullable=True)
    address = Column(String(255), nullable=True)
    phone = Column(String(255), nullable=True)
    site = Column(String(255), nullable=True)
    working_hours = Column(String(255), nullable=True)
    photo_links = Column(Text, nullable=True)
    prices = Column(String(255), nullable=True)
    average_check = Column(String(255), nullable=True)
    relevance_information = Column(Boolean)
    longitude = Column(String(50), nullable=True)
    latitude = Column(String(50), nullable=True)
    link = Column(String(255), nullable=True, unique=True)
    daterenew = Column(Date)