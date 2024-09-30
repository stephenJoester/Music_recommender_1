# Music Recommendation System 
## Introduction 
This project is a Music Recommendation System utilizing content-based recommendation techniques. The CRNN model is trained on audio data in the form of mel spectrograms to extract audio features, while the NN model is trained on metadata of the tracks to extract metadata features. Both models are combined using an ensemble method. The backend is built with FastAPI and PostgreSQL, while the frontend is developed using React JS. The system recommends music to users based on their music preferences or previously liked tracks. 
Link to app : https://music-recommender-phi.vercel.app/
## How to run the web app locally
## Backend 
### Go to the backend directory 
```
cd ./Backend
```
### Set up virtual environment
```
pip install virtualenv (in case you haven't installed this)
python -m venv env
```
### Install dependecies
```
pip install -r requirements.txt
```
### Run server 
```
uvicorn main:app --reload 
```
## Frontend 
### Go to the frontend directory 
```
cd ./Frontend/music_app 
```
### Install packages
```
npm install 
```
### Run app 
```
npm start
```
App runs on http://localhost:3000.
#### Note 
You should change the file Frontend\music_app\src\api.js to be able to call the local server API.