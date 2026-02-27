import os
import sys
import dagshub

# 1. Native DagsHub Initialization
os.environ["DAGSHUB_USER_TOKEN"] = "efaf13a2f97f587e89899421f621f416c88019fd"
dagshub.init(repo_owner="karan.gupta23b", repo_name="my-first-repo", mlflow=True)

import mlflow
import mlflow.sklearn
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.compose import ColumnTransformer

# Regression Models
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.tree import DecisionTreeRegressor

# Classification Models
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC

def run_automl(user_id, dataset_id, target_variable):
    print(f"--- Starting AutoML Factory for User: {user_id}, Dataset: {dataset_id}, Target: {target_variable} ---")
    
    # Load dataset
    try:
        df = pd.read_csv("data.csv")
    except FileNotFoundError:
        print("Error: data.csv not found.")
        return

    # Ensure target exists
    if target_variable not in df.columns:
        print(f"Error: Target {target_variable} not found in CSV.")
        return

    # Automatically Determine Task Type (Regression/Classification)
    if df[target_variable].dtype == 'object' or df[target_variable].nunique() < 10:
        task_type = 'classification'
    else:
        task_type = 'regression'
        
    print(f"Task type detected: {task_type}")

    X = df.drop(columns=[target_variable])
    y = df[target_variable]
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Define Models
    if task_type == 'regression':
        models = {
            "RandomForest": RandomForestRegressor(),
            "LinearRegression": LinearRegression(),
            "DecisionTree": DecisionTreeRegressor()
        }
    else:
        models = {
            "RandomForest": RandomForestClassifier(),
            "LogisticRegression": LogisticRegression(),
            "SVM": SVC(probability=True)
        }

    # Automated Preprocessing
    numeric_features = X.select_dtypes(include=['int64', 'float64']).columns
    numeric_transformer = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='mean')),
        ('scaler', StandardScaler())
    ])

    preprocessor = ColumnTransformer(
        transformers=[
            ('num', numeric_transformer, numeric_features)
        ])

    # --- MLFLOW / DAGSHUB IMPLEMENTATION ---
    # ... (Keep all imports and preprocessing exactly the same) ...
    
    experiment_name = f"{user_id}/{dataset_id}"
    mlflow.set_experiment(experiment_name)

    print(f"Evaluating models under experiment: {experiment_name}...")

    # --- PASS 1: Train and find the best model in memory ---
    trained_pipelines = {}
    scores = {}
    best_score = -float('inf')
    best_name = ""

    for name, model in models.items():
        pipe = Pipeline([
            ('preprocessor', preprocessor),
            ('model', model)
        ])
        
        # Train and evaluate
        pipe.fit(X_train, y_train)
        score = pipe.score(X_test, y_test)
        print(f" - {name} Score: {score:.4f}")
        
        # Store in dictionaries
        trained_pipelines[name] = pipe
        scores[name] = score

        # Track the absolute winner
        if score > best_score:
            best_score = score
            best_name = name

    print(f"\nWinning Model: {best_name} with score {best_score:.4f}")
    print("Logging data to DagsHub MLflow...")

    # --- PASS 2: Safely log to MLflow in active runs ---
    for name in models.keys():
        with mlflow.start_run(run_name=f"{name}_{target_variable}"):
            # 1. Log the score for EVERY model
            mlflow.log_metric("accuracy", scores[name])
            
            # 2. Log the actual file ONLY for the BEST model
            if name == best_name:
                mlflow.set_tag("best_model", "true")
                
                # The run is currently ACTIVE, so this will 100% upload
                mlflow.sklearn.log_model(
                    sk_model=trained_pipelines[name], 
                    artifact_path="model", 
                    pip_requirements=["scikit-learn", "pandas"]
                )
                print(f" -> Artifact folder 'model' successfully uploaded for {name}!")

    print("Training complete. Best model saved securely.")

if __name__ == "__main__":
    if len(sys.argv) > 3:
        run_automl(sys.argv[1], sys.argv[2], sys.argv[3])
    else:
        print("Please provide user_id, dataset_id, and target_variable.")