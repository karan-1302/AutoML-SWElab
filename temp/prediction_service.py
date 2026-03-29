# prediction_service.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Internal Prediction Service")

# 1. Define the Expected Input Data Structure
class PropertyFeatures(BaseModel):
    bedrooms: int
    square_feet: float
    location_score: int

# 2. Define the Internal Endpoint
@app.post("/internal/predict")
def predict_price(features: PropertyFeatures):
    """
    Simulates loading the serialized ML Pipeline from DagsHub 
    and running the prediction algorithm.
    """
    try:
        # Mocking the Machine Learning Preprocessing & Inference logic
        base_price = 50000
        size_value = features.square_feet * 150
        room_value = features.bedrooms * 25000
        loc_value = features.location_score * 10000
        
        estimated_price = base_price + size_value + room_value + loc_value
        
        # Return the calculated prediction
        return {
            "status": "success",
            "model_version": "RandomForest_v1.2",
            "predicted_price_usd": estimated_price
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error processing prediction pipeline")

# To run this service, open your terminal and type:
# uvicorn prediction_service:app --port 8001s