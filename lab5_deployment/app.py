import streamlit as st
import pandas as pd
import subprocess
import hashlib
import os
import dagshub

# --- CONFIGURATION ---
os.environ["DAGSHUB_USER_TOKEN"] = "efaf13a2f97f587e89899421f621f416c88019fd"
dagshub.init(repo_owner="karan.gupta23b", repo_name="my-first-repo", mlflow=True)

import mlflow
import mlflow.sklearn

USER_ID = "karan_1302"

st.set_page_config(page_title="Real Estate AutoML", layout="wide")
st.title("🏡 Real Estate AutoML Platform")

# --- INITIALIZE SESSION STATE ---
if 'dataset_id' not in st.session_state:
    st.session_state['dataset_id'] = None

# 1. Dataset Upload
st.sidebar.header("1. Data Upload")
uploaded_file = st.sidebar.file_uploader("Upload CSV", type=["csv"])

# Readme Supported Targets
readme_targets = ["price", "rental_value", "category", "risk_level", "demand_score"]

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    
    # --- 10 LINES PREVIEW ---
    st.subheader("Data Preview (First 10 Lines)")
    st.dataframe(df.head(10))
    
    # Dataset ID based on content
    file_content = uploaded_file.getvalue()
    dataset_id = hashlib.md5(file_content).hexdigest()[:10]
    
    # Store in session state for retrieval later
    st.session_state['dataset_id'] = dataset_id
    st.sidebar.write(f"Dataset ID: `{dataset_id}`")
    
    # 2. Select Target Variable
    st.sidebar.header("2. Training Configuration")
    
    available_targets = [col for col in df.columns if col in readme_targets]
    
    if not available_targets:
        st.error("No supported target variables from readme found in this CSV.")
    else:
        target_col = st.sidebar.selectbox("Select Supported Target", available_targets)
        
        if st.sidebar.button("Train Best Model"):
            # Save local copy for training script
            df.to_csv("data.csv", index=False)
            st.info(f"Training initiated for target: {target_col}")
            
            # Pass environment (which includes the DAGSHUB_USER_TOKEN)
            current_env = os.environ.copy()
            
            # Run training script
            with st.spinner("Training models and saving to DagsHub..."):
                subprocess.run(
                    ["python", "train_model.py", USER_ID, dataset_id, target_col], 
                    env=current_env
                )
            st.success("Training complete! Model logged to DagsHub.")

# 3. Model Retrieval Section
st.divider()
st.subheader("3. Retrieve & Reuse Model")

client = mlflow.tracking.MlflowClient()

# --- USE SESSION STATE FOR RETRIEVAL ---
if st.session_state['dataset_id'] is not None: 
    experiment_name = f"{USER_ID}/{st.session_state['dataset_id']}" 
    
    # Graceful handling just in case the experiment doesn't exist yet
    try:
        experiment = client.get_experiment_by_name(experiment_name)
    except Exception as e:
        experiment = None

    if experiment:
        # Get runs from this experiment
        runs = client.search_runs(
            experiment_ids=[experiment.experiment_id],
            filter_string="tags.best_model = 'true'",
            order_by=["metrics.accuracy DESC"],
            max_results=1
        )
        
        if runs:
            run_id = runs[0].info.run_id
            model_uri = f"runs:/{run_id}/model"
            
            if st.button("Load Model"):
                with st.spinner("Downloading model artifact from DagsHub..."):
                    model = mlflow.sklearn.load_model(model_uri)
                st.success("Model loaded successfully!")
                st.write("The model is ready in memory. You can now use it to make predictions.")
        else:
            st.warning("No best model found for this experiment.")
    else:
        st.warning(f"Experiment '{experiment_name}' not found. Train a model first.")
else:
    st.info("Upload a dataset above to enable model retrieval.")