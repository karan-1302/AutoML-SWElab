import streamlit as st
import pandas as pd
import numpy as np
import os
import joblib
import dagshub
import mlflow
from mlflow.tracking import MlflowClient
from mlflow.artifacts import download_artifacts

# --- CONFIGURATION ---
os.environ["DAGSHUB_USER_TOKEN"] = "efaf13a2f97f587e89899421f621f416c88019fd"
dagshub.init(repo_owner="karan.gupta23b", repo_name="my-first-repo", mlflow=True)
USER_ID = "karan_1302"

st.set_page_config(page_title="Real Estate Predictor", layout="centered")
st.title("🔮 Real Estate AI Predictor")

# --- 1. MODEL LOADING SECTION ---
st.subheader("1. Connect to AI Model")
dataset_id = st.text_input("Enter Dataset ID (from your training run):")

if st.button("Load Latest Model"):
    with st.spinner("Connecting to DagsHub and downloading model..."):
        try:
            client = MlflowClient()
            experiment_name = f"{USER_ID}/{dataset_id}"
            experiment = client.get_experiment_by_name(experiment_name)

            if not experiment:
                st.error("Experiment not found. Check your Dataset ID.")
            else:
                runs = client.search_runs(
                    experiment_ids=[experiment.experiment_id],
                    filter_string="tags.best_model = 'true'",
                    order_by=["attributes.start_time DESC"],
                    max_results=1
                )
                
                if runs:
                    run_id = runs[0].info.run_id
                    target_var = runs[0].data.tags.get("mlflow.runName", "Unknown").split("_")[-1]
                    
                    artifact_uri = f"runs:/{run_id}/model/best_model.pkl"
                    local_file_path = download_artifacts(artifact_uri=artifact_uri)
                    
                    st.session_state['loaded_model'] = joblib.load(local_file_path)
                    st.session_state['target_var'] = target_var
                    
                    st.success(f"Model loaded! Ready to predict: **{target_var}**")
                else:
                    st.error("No valid model found for this dataset.")
        except Exception as e:
            st.error(f"Failed to load: {e}")

# --- 2. PREDICTION UI & EXPLANATION ---
st.divider()

if 'loaded_model' in st.session_state:
    target = st.session_state['target_var']
    st.subheader(f"2. Input Property Details for: {target}")
    
    # We need to extract the expected feature names from the preprocessor
    pipeline = st.session_state['loaded_model']
    preprocessor = pipeline.named_steps['preprocessor']
    model_core = pipeline.named_steps['model']
    
    # Extract original numeric and categorical feature names from the transformer
    try:
        numeric_features = preprocessor.transformers_[0][2]
        categorical_features = preprocessor.transformers_[1][2]
        all_features = list(numeric_features) + list(categorical_features)
    except Exception:
        st.error("Could not parse feature names from the model. Please retrain using the latest script.")
        st.stop()

    # Build dynamic form
    with st.form("prediction_form"):
        input_data = {}
        cols = st.columns(2)
        
        for i, col in enumerate(all_features):
            with cols[i % 2]:
                if col in numeric_features:
                    input_data[col] = st.number_input(f"{col} (Number)", value=0.0)
                else:
                    input_data[col] = st.text_input(f"{col} (Text/Category)", value="Unknown")
                    
        submit_button = st.form_submit_button("Generate Prediction & Analysis")

    # --- THE PREDICTION & EXPLANATION ENGINE ---
    if submit_button:
        input_df = pd.DataFrame([input_data])
        
        try:
            # 1. Get the Raw Prediction
            prediction = pipeline.predict(input_df)[0]
            
            # 2. Format the Output strictly based on Regression vs Classification
            st.divider()
            st.subheader("📊 AI Verdict")
            
            is_regression = isinstance(prediction, (int, float, np.integer, np.floating))
            
            if is_regression:
                st.metric(label=f"Predicted {target}", value=f"{prediction:,.2f}")
            else:
                # Force Classification into Low/Med/High if possible, otherwise show raw class
                pred_str = str(prediction).title()
                if target in ["Investment Risk Level", "risk_level"] and pred_str not in ["Low", "Medium", "High"]:
                    st.info(f"Raw Output: {pred_str} (Ensure your training CSV contains Low/Medium/High labels for strict mapping).")
                st.metric(label=f"Predicted {target}", value=pred_str)

            # 3. Arguments to Support It (Feature Extracting)
            st.subheader("🧠 Why did the AI choose this?")
            
            importances = None
            if hasattr(model_core, 'feature_importances_'):
                importances = model_core.feature_importances_
                model_type = "Tree-based (Random Forest / Decision Tree)"
            elif hasattr(model_core, 'coef_'):
                # Handle single-row coefs (regression/binary) or multi-row (multi-class)
                importances = np.abs(model_core.coef_[0]) if len(model_core.coef_.shape) > 1 else np.abs(model_core.coef_)
                model_type = "Linear-based (Linear / Logistic Regression)"
            
            if importances is not None:
                # Get the post-processed feature names
                feature_names_out = preprocessor.get_feature_names_out()
                
                # Match importance to feature names, sort them, and get top 3
                importance_df = pd.DataFrame({
                    "Feature": feature_names_out,
                    "Impact Weight": importances
                }).sort_values(by="Impact Weight", ascending=False).head(3)
                
                # Clean up the feature names (remove pipeline prefixes like 'num__' or 'cat__')
                importance_df["Feature"] = importance_df["Feature"].str.replace(r'^(num__|cat__)', '', regex=True)
                
                st.write(f"*Based on a {model_type} architecture, here are the strongest arguments supporting this prediction:*")
                
                for index, row in importance_df.iterrows():
                    feat = row['Feature']
                    # Try to find the original input value the user provided
                    original_input = "Derived from text"
                    for orig_col in all_features:
                        if orig_col in feat:
                            original_input = f"{input_data[orig_col]}"
                            
                    st.markdown(f"- **{feat}** heavily influenced the model (Your input: `{original_input}`).")
            else:
                st.write("This specific model architecture (like SVM) operates as a 'black box', meaning direct supporting arguments cannot be extracted easily.")

        except Exception as e:
            st.error(f"Prediction failed: {e}")