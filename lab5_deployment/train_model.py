import os
import sys
import joblib 
import dagshub
import mlflow
import mlflow.sklearn
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, OneHotEncoder
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

# --- CONFIGURATION ---
os.environ["DAGSHUB_USER_TOKEN"] = "efaf13a2f97f587e89899421f621f416c88019fd"
dagshub.init(repo_owner="karan.gupta23b", repo_name="my-first-repo", mlflow=True)

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
            "LogisticRegression": LogisticRegression(max_iter=1000),
            "SVM": SVC(probability=True)
        }

    # --- Automated Preprocessing Engine ---
    numeric_features = X.select_dtypes(include=['int64', 'float64']).columns
    numeric_transformer = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='median')), # Median is robust to outliers
        ('scaler', StandardScaler())
    ])

    categorical_features = X.select_dtypes(include=['object', 'category']).columns
    categorical_transformer = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='constant', fill_value='Uncategorized')),
        ('onehot', OneHotEncoder(handle_unknown='ignore')) 
    ])

    preprocessor = ColumnTransformer(
        transformers=[
            ('num', numeric_transformer, numeric_features),
            ('cat', categorical_transformer, categorical_features)
        ])

    # --- MLflow Setup ---
    experiment_name = f"{user_id}/{dataset_id}"
    mlflow.set_experiment(experiment_name)
    print(f"Evaluating models under experiment: {experiment_name}...")
    
    trained_pipelines = {}
    scores = {}
    best_score = -float('inf')
    best_name = ""

    # --- Training Loop ---
    for name, model in models.items():
        pipe = Pipeline([
            ('preprocessor', preprocessor),
            ('model', model)
        ])
        
        pipe.fit(X_train, y_train)
        score = pipe.score(X_test, y_test)
        print(f" - {name} Score: {score:.4f}")
        
        trained_pipelines[name] = pipe
        scores[name] = score

        if score > best_score:
            best_score = score
            best_name = name

    print(f"\nWinning Model: {best_name} with score {best_score:.4f}")
    
    # --- LOGIC: Save best model locally and push to DagsHub ---
    local_model_filename = "best_model.pkl"
    winner_pipeline = trained_pipelines[best_name]
    
    # Save a naked .pkl locally for the Streamlit app to pick up immediately
    joblib.dump(winner_pipeline, local_model_filename)
    print(f"Model saved locally as {local_model_filename}")

    print("Logging data and uploading raw model file to DagsHub MLflow...")

    for name in models.keys():
        with mlflow.start_run(run_name=f"{name}_{target_variable}"):
            # Log metrics
            mlflow.log_metric("accuracy_or_r2", scores[name])
            mlflow.log_param("model_type", name)
            
            # Log the actual file ONLY for the BEST model
            if name == best_name:
                mlflow.set_tag("best_model", "true")
                # Upload JUST the single .pkl file to MLflow
                mlflow.log_artifact(local_model_filename, artifact_path="model")
                print(f" -> Artifact file '{local_model_filename}' successfully uploaded for {name}!")

    print("Training complete. Model logged to DagsHub and saved locally.")

if __name__ == "__main__":
    if len(sys.argv) > 3:
        run_automl(sys.argv[1], sys.argv[2], sys.argv[3])
    else:
        print("Please provide user_id, dataset_id, and target_variable.")