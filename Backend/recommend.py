import numpy as np
from sqlalchemy.orm import Session
from database import SessionLocal
from typing import Annotated, List
from fastapi import Depends, HTTPException, status
import json

embeded_images = np.load("data/embeded_images.npy")
labels = np.load("data/labels.npy")
with open("data/embedd_metadata.json", "r") as f:
    embedd_metadata = json.load(f)

matrix_size = 64
top_k = 5

def get_recommendation(track_id : str, existed_ids : List[str] = []) -> List[str]: 
    prediction_anchor = np.zeros((1, matrix_size)) 
    prediction_songs = [] 
    predictions_metadata = []
    predictions_label = [] 
    distance_array = [] 
    
    # Calculate the latent feature vectors for all the songs.
    for i in range(len(labels)):
        if(labels[i] == track_id):
            prediction_anchor_1 = embeded_images[i]
            prediction_anchor_2 = embedd_metadata[labels[i]]
        else : 
            predictions_label.append(labels[i])
            prediction_songs.append(embeded_images[i])
            predictions_metadata.append(embedd_metadata[labels[i]])
    prediction_anchor_2 = np.array(prediction_anchor_2)
    predictions_metadata = np.array(predictions_metadata)
    
    # Count is used for averaging the latent feature vectors.
    for i in range(len(prediction_songs)):
        # Cosine Similarity - Computes a similarity score of all songs with respect
        # to the anchor song.
        distance_1 = np.sum(prediction_anchor_1 * prediction_songs[i]) / (np.sqrt(np.sum(prediction_anchor_1**2)) * np.sqrt(np.sum(prediction_songs[i]**2)))
        distance_2 = np.sum(prediction_anchor_2 * predictions_metadata[i]) / (np.sqrt(np.sum(prediction_anchor_2**2)) * np.sqrt(np.sum(predictions_metadata[i]**2)))
        distance_array.append(distance_1*0.6 + distance_2*0.4)

    distance_array = np.array(distance_array)
    recommendations = 0
    
    list_recommend_ids = []
    list_recommend_songs = []

    while recommendations < top_k:
        index = np.argmax(distance_array)
        value = distance_array[index]
        if predictions_label[index] != track_id and predictions_label[index] not in list_recommend_ids and predictions_label[index] not in existed_ids:
            list_recommend_ids.append(predictions_label[index])
            recommendations = recommendations + 1
        
        distance_array[index] = -np.inf

    return list_recommend_ids


