from pydantic import BaseModel, Field
from datetime import datetime
from typing import List

class CreateUserRequest(BaseModel) : 
    username : str
    email : str
    password : str
    preferences : List[str] = []
    
# class User(BaseModel) : 
#     username : str
#     email : str

class TrackBase(BaseModel) : 
    title : str 
    artist : str 
    genre : str 
    album : str 
    release_date : datetime 
    cover_art : str
    mp3_url : str
    tags : str
    
class TrackSchema(TrackBase) : 
    id: str 
    
    class Config : 
        from_attributes = True
    
class TrackUpdateSchema(BaseModel) : 
    title: str = Field(None, title="Title of the track")
    artist: str = Field(None, title="Artist of the track")
    genre: str = Field(None, title="Genre of the track")
    album: str = Field(None, title="Album of the track")
    release_date: datetime = Field(None, title="Release date of the track")
    cover_art: str = Field(None, title="URL of the cover art for the track")
    mp3_url: str = Field(None, title="URL of the MP3 file for the track")
    tags: str = Field(None, title="Tags of the track")
    
class Token(BaseModel) : 
    access_token : str 
    token_type : str
    user : dict
    preferences : bool
    
class LikedTracksSchema(BaseModel) : 
    user_id : int
    track_id : str
    
    class Config : 
        from_attributes = True
