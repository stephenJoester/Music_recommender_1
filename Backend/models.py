from sqlalchemy import Column, Integer, String, DateTime, ARRAY, ForeignKey
from sqlalchemy.orm import relationship, backref
from sqlalchemy.schema import ForeignKeyConstraint
from database import Base
import datetime

class User(Base) : 
    __tablename__ = "users" 
    id = Column(Integer, primary_key=True)
    username = Column(String, nullable=False) 
    email = Column(String, unique=True, nullable=False) 
    hashed_password = Column(String, nullable=False)
    preferences = Column(ARRAY(String), default=[])
    liked_tracks = relationship("Track", secondary="liked_tracks")
    
class Track(Base) : 
    __tablename__ = "tracks"
    id = Column(String, primary_key=True, index=True) 
    title = Column(String, nullable=False) 
    artist = Column(String, nullable=False) 
    genre = Column(String, nullable=False)
    album = Column(String , default="") 
    release_date = Column(DateTime, default=datetime.datetime.now) 
    cover_art = Column(String, default="") 
    mp3_url = Column(String, default="") 
    tags = Column(String, default="")
    liked_tracks = relationship("LikedTracks", back_populates="track" ,cascade="all, delete-orphan", overlaps="liked_tracks")

class LikedTracks(Base) : 
    __tablename__ = "liked_tracks"
    id = Column(Integer, primary_key=True) 
    user_id = Column(Integer, ForeignKey("users.id"))
    track_id = Column(String, ForeignKey("tracks.id", ondelete="CASCADE"))
    track = relationship("Track", back_populates="liked_tracks", overlaps="liked_tracks")
    
