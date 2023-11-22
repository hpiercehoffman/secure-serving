from fastapi import FastAPI
from typing import List
import tensorflow as tf
import pickle
from tensorflow.keras.preprocessing.sequence import pad_sequences

app = FastAPI()
model = tf.keras.models.load_model('sentiment_analysis_model.h5')
max_length = 200

@app.post("/predict")
def predict_sentiment(reviews: List[str]):
    print("Now computing text sentiment...")
    
    # Tokenize and pad input sequences
    with open('tokenizer.pickle', 'rb') as handle:
        tokenizer = pickle.load(handle)
    reviews_sequences = [[tokenizer.get(word, 0) for word in review.split()] for review in reviews]
    reviews_sequences = pad_sequences(reviews_sequences, maxlen=max_length)
    
    # Make predictions
    predictions = model.predict(reviews_sequences)
    sentiment_predictions = [{'sentiment': 'positive' if pred >= 0.5 else 'negative', 'confidence': float(pred)} for pred in predictions]
    return sentiment_predictions
