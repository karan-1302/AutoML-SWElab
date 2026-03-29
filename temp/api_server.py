from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import joblib
import pandas as pd

app = FastAPI()

# Load the artifact (contains the model AND the task type)
artifact = joblib.load("best_model.pkl")
model = artifact["model"]
task_type = artifact["type"]

class PredictionRequest(BaseModel):
    features: dict # Flexible dictionary to handle any dataset columns

@app.post("/predict")
def predict(request: PredictionRequest):
    try:
        # Convert input dict to DataFrame
        input_df = pd.DataFrame([request.features])
        
        prediction = model.predict(input_df)[0]
        
        # Add business logic/recommendation (Section 4)
        recommendation = "Maintain strategy"
        if task_type == "regression" and prediction > 400000:
            recommendation = "High-value asset: Consider premium marketing."
        elif task_type == "classification" and prediction == "High Risk":
            recommendation = "Warning: Exercise caution with this investment."

        return {
            "task": task_type,
            "prediction": str(prediction),
            "recommendation": recommendation
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))