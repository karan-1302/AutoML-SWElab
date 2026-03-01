import streamlit as st
import pandas as pd
import numpy as np
import subprocess
import hashlib
import os
import dagshub
import joblib
import threading # --- NEW: For background tasks ---

# --- CONFIGURATION ---
os.environ["DAGSHUB_USER_TOKEN"] = "efaf13a2f97f587e89899421f621f416c88019fd"
dagshub.init(repo_owner="karan.gupta23b", repo_name="my-first-repo", mlflow=True)

import mlflow
import mlflow.sklearn
from mlflow.artifacts import download_artifacts
from mlflow.tracking import MlflowClient

USER_ID = "karan_1302"

st.set_page_config(page_title="Real Estate AutoML", layout="wide")

# --- INITIALIZE SESSION STATE ---
if 'dataset_id' not in st.session_state:
    st.session_state['dataset_id'] = None
if 'loaded_model' not in st.session_state:
    st.session_state['loaded_model'] = None
if 'target_col' not in st.session_state:
    st.session_state['target_col'] = None
if 'df_schema' not in st.session_state:
    st.session_state['df_schema'] = None
if 'training_status' not in st.session_state:
    st.session_state['training_status'] = "Idle"

# --- NAVIGATION ---
st.sidebar.title("Navigation")
app_mode = st.sidebar.radio("Go to:", ["1. Train & Load Model", "2. Prediction Engine"])

# ==========================================
# PAGE 1: TRAIN & LOAD MODEL
# ==========================================
if app_mode == "1. Train & Load Model":
    st.title("Real Estate AutoML - Training")
    
    st.header("1. Data Upload")
    uploaded_file = st.file_uploader("Upload CSV", type=["csv"])

    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        
        # Drop the first column (ID)
        # if not df.empty:
        #     df = df.drop(df.columns[0], axis=1)                
        
        # Save cleaned schema
        st.session_state['df_schema'] = df
        
        st.subheader("Data Preview (First 10 Lines)")
        st.dataframe(df.head(10))
        
        file_content = uploaded_file.getvalue()
        dataset_id = hashlib.md5(file_content).hexdigest()[:10]
        st.session_state['dataset_id'] = dataset_id
        st.write(f"**Dataset ID:** `{dataset_id}`")
        
        st.divider()
        st.header("2. Training Configuration")
        
        # SMART FILTERING
        SUPPORTED_TARGETS = {
            "Property Sale Price (Regression)": ["price", "sale_price", "property_price"],
            "Rental Value (Regression)": ["rental_value", "rent", "monthly_rent"],
            "Property Category (Classification)": ["category", "property_category", "type", "property_type"],
            "Investment Risk Level (Classification)": ["risk_level", "investment_risk", "risk", "risk_score"]
        }

        available_options = {}
        for friendly_name, possible_col_names in SUPPORTED_TARGETS.items():
            for col in df.columns:
                if col.lower().strip() in possible_col_names:
                    available_options[friendly_name] = col
                    break
        
        if not available_options:
            st.error("No supported target variables found in this CSV.")
        else:
            selected_ui_target = st.selectbox("Select Target to Predict", list(available_options.keys()))
            actual_target_col = available_options[selected_ui_target]
            
            # --- NEW: Background Threading Logic ---
            if st.button("Train Best Model"):
                st.session_state['training_status'] = "Training"
                df.to_csv("data.csv", index=False)
                
                # Function to run in background
                def background_train():
                    current_env = os.environ.copy()
                    subprocess.run(
                        ["python", "train_model.py", USER_ID, dataset_id, actual_target_col], 
                        env=current_env,
                        check=True
                    )
                    # Load model locally immediately after training
                    if os.path.exists("best_model.pkl"):
                        st.session_state['loaded_model'] = joblib.load("best_model.pkl")
                        st.session_state['target_col'] = actual_target_col
                        st.session_state['training_status'] = "Finished"
                    else:
                        st.session_state['training_status'] = "Error"

                # Start the thread
                thread = threading.Thread(target=background_train)
                thread.start()
                st.info("Training started in the background. You can navigate to other pages, but do not close the app.")

            # Status Indicator
            if st.session_state['training_status'] == "Training":
                st.warning("Training in progress...")
            elif st.session_state['training_status'] == "Finished":
                st.success("Training complete! Model loaded. Switch to Prediction Engine.")
            elif st.session_state['training_status'] == "Error":
                st.error("Training failed.")

    # Model Retrieval
    st.divider()
    st.header("3. Retrieve & Reuse Model from Cloud")
    
    if st.session_state['dataset_id'] is not None:
        if st.button("Load Model from Cloud"):
            with st.spinner("Downloading raw model file from DagsHub..."):
                try:
                    dagshub.init(repo_owner="karan.gupta23b", repo_name="my-first-repo", mlflow=True)
                    client = MlflowClient()
                    experiment_name = f"{USER_ID}/{st.session_state['dataset_id']}"
                    experiment = client.get_experiment_by_name(experiment_name)

                    if experiment:
                        runs = client.search_runs(
                            experiment_ids=[experiment.experiment_id],
                            filter_string="tags.best_model = 'true'",
                            order_by=["attributes.start_time DESC"],
                            max_results=1
                        )
                        
                        if runs:
                            run_id = runs[0].info.run_id
                            st.session_state['target_col'] = runs[0].data.tags.get("mlflow.runName", "Unknown").split("_")[-1]
                            
                            artifact_uri = f"runs:/{run_id}/model/best_model.pkl"
                            local_file_path = download_artifacts(artifact_uri=artifact_uri)
                            
                            st.session_state['loaded_model'] = joblib.load(local_file_path)
                            st.success(f"Model downloaded and loaded successfully! Switch to the **Prediction Engine** tab.")
                        else:
                            st.warning("No best model found for this experiment.")
                    else:
                        st.warning("Experiment not found. Train a model first.")
                except Exception as e:
                    st.error(f"Failed to load model from cloud: {e}")
    else:
        st.info("Upload a dataset above to enable model retrieval.")


# ==========================================
# PAGE 2: PREDICTION ENGINE
# ==========================================
elif app_mode == "2. Prediction Engine":
    st.title("AI Prediction Engine")
    
    # Check if model is loaded from session state
    if st.session_state['loaded_model'] is None or st.session_state['df_schema'] is None:
        st.warning("No model is currently loaded in memory. Please go to **Train & Load Model** to upload data and load a model.")
    else:
        target = st.session_state['target_col']
        df = st.session_state['df_schema']
        pipeline = st.session_state['loaded_model']
        
        st.subheader(f"Predicting: **{target}**")
        st.write("Select at least 3 attributes you know, and the AI will automatically use typical (default) values for the rest.")
        
        # 1. Identify features and calculate background defaults
        features = [col for col in df.columns if col != target]
        defaults = {}
        
        for col in features:
            if pd.api.types.is_numeric_dtype(df[col]):
                median_val = df[col].median()
                defaults[col] = float(median_val) if not pd.isna(median_val) else 0.0
            else:
                defaults[col] = "Uncategorized"

        # 2. Let the user choose which features to input
        default_selections = features[:min(3, len(features))]
        selected_features = st.multiselect(
            "Select the attributes you want to provide:", 
            options=features, 
            default=default_selections
        )
        
        # Enforce the minimum of 3 rule
        if len(selected_features) < 3:
            st.error("⚠️ Please select at least 3 attributes to ensure a reliable prediction.")
        
        with st.form("prediction_form"):
            input_data = {}
            cols = st.columns(3)
            
            # 3. Only build input UI for the selected features
            for i, col in enumerate(selected_features):
                with cols[i % 3]:
                    if pd.api.types.is_numeric_dtype(df[col]):
                        input_data[col] = st.number_input(f"{col}", value=float(defaults[col]))
                    else:
                        unique_vals = df[col].dropna().unique().tolist()
                        input_data[col] = st.selectbox(f"{col}", options=unique_vals)
                        
            submit_button = st.form_submit_button("Generate Prediction & Analysis")

        if submit_button:
            if len(selected_features) < 3:
                st.error("Prediction blocked. You must provide at least 3 attributes.")
            else:
                try:
                    # 4. Merge user inputs with the background defaults
                    final_input_dict = defaults.copy()
                    final_input_dict.update(input_data)
                    
                    input_df = pd.DataFrame([final_input_dict])
                    
                    # Make prediction
                    prediction = pipeline.predict(input_df)[0]
                    
                    st.divider()
                    st.subheader("AI Verdict")
                    
                    is_regression = isinstance(prediction, (int, float, np.integer, np.floating))
                    
                    if is_regression:
                        st.metric(label=f"Predicted {target}", value=f"{prediction:,.2f}")
                    else:
                        pred_str = str(prediction).title()
                        st.metric(label=f"Predicted {target}", value=pred_str)

                    # --- ARGUMENTS ENGINE ---
                    st.subheader("Why did the AI choose this?")
                    model_core = pipeline.named_steps['model']
                    preprocessor = pipeline.named_steps['preprocessor']
                    
                    importances = None
                    if hasattr(model_core, 'feature_importances_'):
                        importances = model_core.feature_importances_
                        model_type = "Tree-based model"
                    elif hasattr(model_core, 'coef_'):
                        importances = np.abs(model_core.coef_[0]) if len(model_core.coef_.shape) > 1 else np.abs(model_core.coef_)
                        model_type = "Linear-based model"
                    
                    if importances is not None:
                        feature_names_out = preprocessor.get_feature_names_out()
                        importance_df = pd.DataFrame({
                            "Feature": feature_names_out,
                            "Impact": importances
                        }).sort_values(by="Impact", ascending=False)
                        
                        importance_df["Feature"] = importance_df["Feature"].str.replace(r'^(num__|cat__)', '', regex=True)
                        
                        st.write(f"*Based on a {model_type}, here are the strongest factors **you provided** that drove this result:*")
                        
                        count = 0
                        for _, row in importance_df.iterrows():
                            if count >= 3: break
                            
                            feat = row['Feature']
                            is_custom = any(user_col in feat for user_col in selected_features)
                            
                            if is_custom:
                                st.markdown(f"- **{feat}** heavily influenced the output.")
                                count += 1
                        
                        if count == 0:
                            st.write("The strongest driving factors were not among the specific fields you highlighted.")
                            
                    else:
                        st.write("This specific AI architecture operates as a 'black box' (e.g., SVM), meaning direct feature weights cannot be extracted.")

                except Exception as e:
                    st.error(f"Prediction failed: {e}")