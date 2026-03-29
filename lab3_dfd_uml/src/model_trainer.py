from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import mean_squared_error, r2_score
import numpy as np

class ModelTrainer:
    """
    Module 2: Model Trainer
    Responsible for training multiple machine learning models and selecting the best one
    based on performance metrics (R^2 Score).
    """
    
    def __init__(self):
        self.models = {
            "Linear Regression": LinearRegression(),
            "Random Forest": RandomForestRegressor(n_estimators=100, random_state=42)
        }
        self.best_model = None
        self.best_score = -np.inf
        self.best_model_name = ""

    def train_and_evaluate(self, X, y):
        """
        Trains all defined models and selects the best one.
        """
        print("\\nStarting Model Training...")
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        results = {}
        
        for name, model in self.models.items():
            print(f"Training {name}...")
            model.fit(X_train, y_train)
            
            y_pred = model.predict(X_test)
            
            mse = mean_squared_error(y_test, y_pred)
            r2 = r2_score(y_test, y_pred)
            
            results[name] = {"MSE": mse, "R2": r2}
            print(f"  -> {name} Performance: MSE={mse:.4f}, R2={r2:.4f}")
            
            # Select best model based on R2 Score
            if r2 > self.best_score:
                self.best_score = r2
                self.best_model = model
                self.best_model_name = name
                
        print(f"\\nBest Model Selected: {self.best_model_name} with R2 Score: {self.best_score:.4f}")
        return self.best_model, results

    def get_best_model(self):
        return self.best_model
