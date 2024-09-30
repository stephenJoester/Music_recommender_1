from datetime import timedelta, datetime 
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from starlette import status 
from database import SessionLocal
from models import User
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordRequestForm
from schemas import CreateUserRequest, Token
from services import authenticate_user, create_access_token, get_current_user
import json

router = APIRouter(
    prefix='/auth',
    tags=['auth']
) 

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_db() : 
    db = SessionLocal() 
    try : 
        yield db 
    finally : 
        db.close()
        
db_dependency = Annotated[Session, Depends(get_db)]

# sign up
@router.post("/users", status_code=status.HTTP_201_CREATED) 
async def create_user(db: db_dependency, create_user_request: CreateUserRequest) :
    try : 
        # check existing users 
        existing_user = db.query(User).filter(User.username==create_user_request.username).first()
        
        if existing_user : 
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already exists")

        # create user if not exists
        create_user_model = User(
            username=create_user_request.username,
            email=create_user_request.email, hashed_password=bcrypt_context.hash(create_user_request.password))
        
        db.add(create_user_model) 
        db.commit()
    except Exception as e : 
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error creating user: " + str(e))
    
# login 
@router.post("/token", response_model=Token) 
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: db_dependency) : 
    user = authenticate_user(form_data.username, form_data.password, db) 
    if not user : 
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate user") 
    token = create_access_token(user.username, user.id, timedelta(minutes=20)) 
    user = await get_current_user(token)
    print(user)
    is_preferences_set = await check_users_preferences(user['id'], db)
    
    return {'access_token' : token, 'token_type' : 'bearer', 'user' : user, 'preferences' : is_preferences_set}

async def check_users_preferences(user_id : int, db : db_dependency) : 
    user = db.query(User).filter(User.id == user_id).first()
    if user.preferences : 
        return True
    return False

# add user preferences 
@router.put("/users/preferences", status_code=status.HTTP_200_OK) 
async def add_user_preferences(preferences: list[str], db : db_dependency, current_user : dict = Depends(get_current_user)) :
    try : 
        print(current_user)
        # find user 
        user = db.query(User).filter(User.id == current_user['id']).first()
        
        preferences_map = {
            "Pop" : "pop",
            "Rock" : "rock",
            "Hip-Hop" : "hiphop",
            "Electronic" : "electronic", 
            "Jazz" : "jazz",
            "Country" : "country",
            "Classical" : "classical",
            "Instrumental" : "instrumental"
        }
        
        preferences = [preferences_map[preference] for preference in preferences]
        
        # if preferences : 
        user.preferences = preferences 
        db.commit()
        db.refresh(user)
        return {"preferences" : True}
        
    except Exception as e : 
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error updating user preferences: " + str(e))

# verify user
@router.get("/users/me", status_code=status.HTTP_200_OK) 
async def get_user(db : db_dependency ,current_user : dict = Depends(get_current_user)) : 
    user = current_user
    preferences = await check_users_preferences(user['id'], db)
    user['preferences'] = preferences
    return user
    
# TODO : add logout endpoint
