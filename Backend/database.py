from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from dotenv import load_dotenv
import os 

load_dotenv()

URL_DATABASE = os.getenv("URL_DATABASE")  

# create a PostgreSQL engine instance
engine = create_engine(URL_DATABASE) 

# create declarative base meta instance 
Base = declarative_base() 

# create session local class for ession maker
SessionLocal = sessionmaker(autocommit=False, autoflush=False,bind=engine) 
