# Use Case Specification: Real Estate AutoML Prediction System

## 1. Project Overview
This project focuses on an automated machine learning (AutoML) pipeline designed for real estate professionals. The system handles the end-to-back lifecycle of data cleaning, model selection, and explainable price prediction.

---

## 2. Actors
| Actor | Type | Description |
| :--- | :--- | :--- |
| **Real Estate Professional** | Primary (Human) | Interacts with the interface to upload data, trigger training, and retrieve property predictions. |
| **AutoML / AI Engine** | Secondary (System) | Orchestrates data preprocessing, feature engineering, model training, and performance evaluation. |
| **Database / Model Storage** | Secondary (System) | Persists the trained models and historical datasets for future retrieval. |

---

## 3. Use Case Catalog

### Data Management & Preparation
* **UC-01: Upload Dataset**
    * The user uploads a real estate dataset (CSV/JSON) containing historical property data.
* **UC-02: Preview Dataset**
    * *Optional:* User views a summary or sample (head/tail) of the data to verify integrity.
* **UC-03: Preprocess Data**
    * System automatically cleans missing values, encodes categorical variables, and scales numerical features.

### Model Development (AutoML Pipeline)
* **UC-04: Initiate AutoML Process**
    * The user triggers the automated machine learning pipeline.
* **UC-05: Select Target Variable**
    * User or system identifies the prediction target (e.g., `Price`).
* **UC-06: Train ML Model**
    * The AI Engine trains multiple algorithms (Linear Regression, Random Forest, XGBoost, etc.).
* **UC-07: Evaluate Model**
    * System validates models using metrics like **RMSE** or **R²**.
* **UC-08: Select Best Performing Model**
    * The system identifies the optimal model and saves it to the Model Storage.

### Prediction & Insights
* **UC-09: Generate Prediction**
    * The user requests a price prediction for a specific property input.
* **UC-10: Reuse Trained Model**
    * The system retrieves the "Best Model" from storage to provide instant predictions without retraining.
* **UC-11: View Explainable Predictions**
    * The user views the logic (SHAP/LIME values) behind the estimation (e.g., "Proximity to transit increased value by 10%").
* **UC-12: View Decision-Support Recommendations**
    * The system provides actionable investment arguments based on model outputs.