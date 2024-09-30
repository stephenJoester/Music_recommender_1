import os 
from dotenv import load_dotenv
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
import logging
from database import SessionLocal
from typing import Annotated, List
from sqlalchemy import func
from sqlalchemy.orm import Session
from sqlalchemy.sql.expression import select, or_
from fastapi import Depends, HTTPException, status
from models import User, Track, LikedTracks
from datetime import timedelta, datetime 
from jose import jwt, JWTError
import recommend

load_dotenv()

logging.getLogger('passlib').setLevel(logging.ERROR)

SECRET_KEY = os.getenv("SECRET_KEY") 
ALGORITHM = 'HS256'

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_bearer = OAuth2PasswordBearer(tokenUrl='auth/token')

def get_db() : 
    db = SessionLocal() 
    try : 
        yield db 
    finally : 
        db.close()
        
db_dependency = Annotated[Session, Depends(get_db)]

def authenticate_user(username: str, password: str, db : db_dependency) : 
    user = db.query(User).filter(User.username == username).first()
    if not user : 
        return False
    if not bcrypt_context.verify(password, user.hashed_password) : 
        return False
    return user

def create_access_token(username: str, user_id: int, expires_delta: timedelta) : 
    encode = {'sub': username, 'id': user_id} 
    expires = datetime.now() + expires_delta
    encode.update({'exp' : expires}) 
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token: Annotated[str, Depends(oauth2_bearer)]) : 
    try : 
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM]) 
        username: str = payload.get('sub') 
        user_id : int = payload.get('id') 
        if username is None or username is None : 
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Could not validate user') 
        return {'username': username, 'id' : user_id} 
    except JWTError : 
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Could not validate user')

async def create_liked_track(track_id: str, user_id : int, db: db_dependency) : 
    try : 
        liked_track = LikedTracks(user_id=user_id, track_id=track_id)
        db.add(liked_track) 
        db.commit()
        db.refresh(liked_track)
        return liked_track
    except Exception as e : 
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error creating liked track: " + str(e))
  
async def check_liked_tracks(track_id: str, user_id: int, db: db_dependency) : 
    try : 
        exists = bool(db.query(LikedTracks).filter_by(user_id=user_id, track_id=track_id).first())
        return exists
    except Exception as e : 
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error checking liked tracks: " + str(e))
    
async def delete_liked_track(track_id: str, user_id: int, db: db_dependency) : 
    try : 
        db.query(LikedTracks).filter_by(user_id=user_id, track_id=track_id).delete()
        db.commit()
        return {"message" : "Track unliked successfully"}
    except Exception as e : 
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error deleting liked track: " + str(e))
    
async def get_liked_tracks(user_id: int, db: db_dependency, limit : int = 0) : 
    try : 
        query = (
            select(Track)
            .join(LikedTracks, LikedTracks.track_id == Track.id)
            .filter(LikedTracks.user_id == user_id)
        )

        if limit > 0 : 
            query = query.limit(limit)

        # Execute the query and get the result
        result = db.execute(query)
        liked_tracks = result.scalars().all()
        
        liked_tracks_dict = []
        for track in liked_tracks:
            track_dict = {
                "id": track.id,
                "title": track.title,
                "artist": track.artist,
                "genre": track.genre,
                "album": track.album,
                "release_date": track.release_date,
                "cover_art": track.cover_art,
                "mp3_url": track.mp3_url,
                "tags" : track.tags
            }
            liked_tracks_dict.append(track_dict)

        return liked_tracks_dict

    except Exception as e : 
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error getting liked tracks: " + str(e))
    
def get_tags_keywords(tags : str) -> List[str] : 
    tags_list = tags.split(", ") 
    tags_keywords = [tag.split(":")[0].strip() for tag in tags_list]
    return tags_keywords
    
async def get_recommendation(track_id : str, db: db_dependency) : 
    try : 
        # get the tags of the original track 
        original_track = db.query(Track).filter(Track.id == track_id).first()
        original_tags = get_tags_keywords(original_track.tags)
        
        # get the recommended tracks
        title_count = {} 
        duplicated_ids = []
        detect_duplicated = True
        
        while detect_duplicated: 
            detect_duplicated = False
            track_ids = recommend.get_recommendation(track_id, existed_ids=duplicated_ids)
            tracks = db.query(Track).filter(Track.id.in_(track_ids)).all()
            for track in tracks : 
                title = track.title
                # detect duplicates
                if title in title_count : 
                    duplicated_ids.append(track.id)
                    detect_duplicated = True
                else : 
                    title_count[title] = 1
            
            if detect_duplicated : 
                # reset title count
                title_count = {}
                continue
        
        # only select mutual tags
        for track in tracks : 
            track.tags = get_tags_keywords(track.tags)
            track.tags = list(set(track.tags) & set(original_tags))
            track.tags = ", ".join(track.tags)
        return tracks
    except Exception as e : 
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error getting recommendation: " + str(e))
    
async def get_recommendation_by_likes(user_id: int, db: db_dependency) : 
    try : 
        liked_tracks = await get_liked_tracks(user_id=user_id, db=db, limit=0) 
        if liked_tracks is None : 
            return []
        track_ids = [track['id'] for track in liked_tracks]
        
        results = []
        track_ids_set = set()  # Set to store unique track IDs
        track_titles_set = set()

        for track_id in track_ids:
            track_ids = recommend.get_recommendation(track_id)
            tracks = db.query(Track).filter(Track.id.in_(track_ids)).all()
            for track in tracks:
                if track.id not in track_ids_set and track.title not in track_titles_set:  # Check if track ID is already in the set
                    results.append(track)
                    track_ids_set.add(track.id)  # Add track ID to the set
                    track_titles_set.add(track.title) # Add track title to the set
        
        return results

    except Exception as e : 
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error getting recommendation by likes: " + str(e))

async def get_title_by_track_id(track_id : str, db: db_dependency) : 
    try : 
        track = db.query(Track).filter(Track.id == track_id).first()
        return track.title
    except Exception as e : 
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error getting title by track ID: " + str(e))
    
async def get_tracks_by_preferences(user_id: int, db: db_dependency) : 
    try : 
        user = db.query(User).filter(User.id == user_id).first()
        preferences = user.preferences
        print(preferences)
        tracks = db.query(Track).filter(Track.genre.in_(preferences)).order_by(func.random()).limit(10).all()
        # print(tracks)
        return tracks
    except Exception as e : 
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error getting tracks by preferences: " + str(e))
    
async def get_tracks_for_user(user_id: int, db: db_dependency) : 
    try : 
        # check if liked tracks by user exist 
        recommended_tracks_by_likes = await get_recommendation_by_likes(user_id=user_id, db=db)
        
        if recommended_tracks_by_likes : 
            return recommended_tracks_by_likes
        
        # get tracks by preferences
        tracks = await get_tracks_by_preferences(user_id=user_id, db=db)
        return tracks
    
    except Exception as e : 
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error getting tracks for user: " + str(e))
    
async def check_users_preferences(user_id : int, db : db_dependency) : 
    user = db.query(User).filter(User.id == user_id).first()
    if user.preferences : 
        return True
    return False

# search tracks
async def search_tracks(search_query : str, genres : str, db : db_dependency) : 
    try : 
        if genres != "All" : 
            genres = genres.split(",") 
            genres_map = {
                "Pop" : "pop",
                "Rock" : "rock",
                "Hip-Hop" : "hiphop",
                "Electronic" : "electronic", 
                "Jazz" : "jazz",
                "Country" : "country",
                "Classical" : "classical",
                "Instrumental" : "instrumental"
            }
            genres = [genres_map[genre] for genre in genres]
        # print(genres)
        # tracks = db.query(models.Track).filter(or_(
        #     models.Track.title.ilike(f"%{search_query}%"),
        #     models.Track.artist.ilike(f"%{search_query}%")
        #     )).limit(10).all() 
        query = db.query(Track).filter(or_(
            Track.title.ilike(f"%{search_query}%"),
            Track.artist.ilike(f"%{search_query}%")
        ))
        
        if genres != "All" : 
            query = query.filter(Track.genre.in_(genres))
        tracks = query.limit(10).all() 
    except Exception as e : 
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error searching tracks: " + str(e))
    
    return tracks