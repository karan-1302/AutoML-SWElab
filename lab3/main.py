import pandas as pd
import numpy as np
import sys
import os

# Ensures src is in python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.data_preprocessor import DataPreprocessor
from src.model_trainer import ModelTrainer

def create_synthetic_data(num_samples=1000):
    """
    Generates synthetic real estate data for demonstration.
    """
    np.random.seed(42)
    data = {
        'SquareFeet': np.random.randint(500, 5000, num_samples),
        'Bedrooms': np.random.randint(1, 6, num_samples),
        'Bathrooms': np.random.randint(1, 4, num_samples),
        'Location': np.random.choice(['Urban', 'Suburban', 'Rural'], num_samples),
        'Age': np.random.randint(0, 50, num_samples)
    }
    
    df = pd.DataFrame(data)
    
    # Generate Price with some logic + noise
    # Base price + sqft + bedrooms + bathrooms - age
    price = (
        50000 + 
        (df['SquareFeet'] * 200) + 
        (df['Bedrooms'] * 15000) + 
        (df['Bathrooms'] * 10000) - 
        (df['Age'] * 500) + 
        np.random.normal(0, 25000, num_samples) # Add noise
    )
    
    # Location multiplier
    location_multiplier = df['Location'].map({'Urban': 1.5, 'Suburban': 1.2, 'Rural': 1.0})
    df['Price'] = price * location_multiplier
    
    return df

def main():
    print("==========================================")
    print("   Real Estate AutoML System - Prototype  ")
    print("==========================================\\n")

    # 1. Load Data
    print("Step 1: Loading Dataset...")
    df = create_synthetic_data()
    print(df.head())
    print("-" * 30)

    # 2. Data Preprocessing
    print("\\nStep 2: Preprocessing Data...")
    
    # Instantiate DataPreprocessor
    try:
        preprocessor = DataPreprocessor(target_variable='Price')
        
        # Split target (y) and features (X)
        if 'Price' in df.columns:
            y = df['Price']
            X = df.drop(columns=['Price'])
            
            # Fit and transform
            print("Fitting preprocessor...")
            preprocessor.fit(X)
            X_processed = preprocessor.transform(X)
            print("Preprocessing Complete.")
        else:
            print("Target variable 'Price' not found.")
            return

    except Exception as e:
        print(f"Error in Preprocessing: {e}")
        return

    print("-" * 30)

    # 3. Model Training
    print("\\nStep 3: Training & Selecting Model...")
    try:
        trainer = ModelTrainer()
        trainer.models = {
            "Linear Regression": trainer.models["Linear Regression"],
            "Random Forest": trainer.models["Random Forest"]
        }
        best_model, results = trainer.train_and_evaluate(X_processed, y)
    except Exception as e:
         print(f"Error in Training: {e}") 
         return
         
    print("-" * 30)
    
    print("\\nProcess Complete. The system is ready for real data usage.")

if __name__ == "__main__":
    main()
