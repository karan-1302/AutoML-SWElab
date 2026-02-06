# Use Case Specification: Real Estate AutoML Prediction System

## 1. System Overview
Automated machine learning platform for real estate professionals to predict property prices through data upload, model training, and explainable predictions.

---

## 2. Actors
| Actor | Role |
|-------|------|
| **Real Estate Professional** | Primary user - uploads data, initiates training, requests predictions |
| **AutoML Engine** | System component - trains models, generates predictions |
| **Database/Model Storage** | System component - persists data and models |

---

## 3. Use Cases Overview

### Authentication & Data Management
- **UC-01: Login** - User authenticates to system
- **UC-02: Upload Dataset** - User uploads CSV file with property data
- **UC-03: View Dataset** - User previews uploaded data

### Model Training Pipeline
- **UC-04: Select Target Variable** - User chooses prediction target (e.g., Price)
- **UC-05: Configure Training** - User sets training parameters
- **UC-06: Train Model** - System trains multiple ML algorithms
- **UC-07: Evaluate Models** - System calculates performance metrics
- **UC-08: Select Best Model** - System chooses best performing model

### Prediction & Insights
- **UC-09: Generate Prediction** - User inputs property features, gets price prediction
- **UC-10: View Explanation** - User sees which features influenced prediction (SHAP)
- **UC-11: Get Recommendations** - System provides actionable business insights

---

## 4. Detailed Use Cases

### UC-01: Login
**Actors:** Real Estate Professional  
**Description:** User authenticates with email and password

**Main Flow:**
1. User enters email and password
2. System validates credentials
3. System creates session token
4. User redirected to dashboard

**Acceptance Criteria:**
- ✅ Valid credentials accepted
- ✅ Invalid credentials rejected
- ✅ Session token created

---

### UC-02: Upload Dataset
**Actors:** Real Estate Professional, Database/Model Storage  
**Description:** User uploads CSV file containing property data

**Preconditions:**
- User is logged in
- CSV file is valid (≤100 MB)

**Main Flow:**
1. User selects CSV file
2. System validates file format and size
3. System parses CSV and checks structure
4. System stores dataset in Database
5. System displays success message

**Acceptance Criteria:**
- ✅ CSV file uploaded successfully
- ✅ File size validated (≤100 MB)
- ✅ Dataset stored with unique ID
- ✅ Error handling for invalid files

---

### UC-03: View Dataset
**Actors:** Real Estate Professional, Database/Model Storage  
**Description:** User previews uploaded dataset

**Main Flow:**
1. User selects dataset from list
2. System retrieves dataset from Database
3. System displays first 10 rows
4. System shows column names, data types, basic statistics
5. System displays data quality score

**Acceptance Criteria:**
- ✅ First 10 rows displayed
- ✅ Column info shown
- ✅ Data quality metrics calculated
- ✅ Missing values highlighted

---

### UC-04: Select Target Variable
**Actors:** Real Estate Professional, AutoML Engine  
**Description:** User chooses which column to predict

**Preconditions:**
- Dataset uploaded (UC-02 completed)

**Main Flow:**
1. System displays available columns
2. User selects target column (e.g., "Price")
3. System validates target (numeric for regression, categorical for classification)
4. System identifies feature columns (all others)
5. System confirms selection

**Acceptance Criteria:**
- ✅ Target column selected
- ✅ Target validated
- ✅ Feature columns identified
- ✅ Selection stored

---

### UC-05: Configure Training
**Actors:** Real Estate Professional, AutoML Engine  
**Description:** User sets training parameters

**Main Flow:**
1. System displays training options
2. User selects algorithms (Linear Regression, Random Forest, XGBoost)
3. User sets train/test split ratio (default 80/20)
4. User sets cross-validation folds (default 5)
5. System confirms configuration

**Acceptance Criteria:**
- ✅ Algorithms selected
- ✅ Parameters validated
- ✅ Configuration stored

---

### UC-06: Train Model
**Actors:** AutoML Engine, Database/Model Storage  
**Description:** System trains multiple ML models on preprocessed data

**Preconditions:**
- Target variable selected (UC-04 completed)
- Training configured (UC-05 completed)

**Main Flow:**
1. System preprocesses data (imputation, encoding, scaling)
2. System splits data (80% train, 20% test)
3. System trains each selected algorithm
4. System performs cross-validation
5. System calculates metrics for each model
6. System stores trained models

**Acceptance Criteria:**
- ✅ Minimum 2 models trained
- ✅ Data preprocessed correctly
- ✅ Cross-validation performed
- ✅ Metrics calculated

---

### UC-07: Evaluate Models
**Actors:** AutoML Engine, Database/Model Storage  
**Description:** System calculates performance metrics for trained models

**Main Flow:**
1. System generates predictions on test set
2. System calculates metrics:
   - **Regression:** MAE, RMSE, R²
   - **Classification:** Accuracy, Precision, Recall, F1
3. System ranks models by primary metric (R² for regression)
4. System generates evaluation report
5. System stores results

**Acceptance Criteria:**
- ✅ All metrics calculated
- ✅ Models ranked by performance
- ✅ Report generated
- ✅ Results stored

---

### UC-08: Select Best Model
**Actors:** AutoML Engine, Database/Model Storage  
**Description:** System identifies and saves best performing model

**Main Flow:**
1. System identifies best model (highest R² or F1)
2. System generates model metadata
3. System assigns unique model ID
4. System serializes and saves model
5. System marks model as "active"

**Acceptance Criteria:**
- ✅ Best model identified
- ✅ Model saved to storage
- ✅ Metadata recorded
- ✅ Model ready for predictions

---

### UC-09: Generate Prediction
**Actors:** Real Estate Professional, AutoML Engine, Database/Model Storage  
**Description:** User inputs property features and gets price prediction

**Preconditions:**
- Trained model exists (UC-08 completed)

**Main Flow:**
1. User navigates to Predict page
2. System displays input form with required features
3. User enters property data (location, area, bedrooms, etc.)
4. System validates input
5. System preprocesses input (same pipeline as training)
6. System loads active model
7. System generates prediction
8. System calculates confidence score
9. System displays prediction with confidence level

**Acceptance Criteria:**
- ✅ Input validated
- ✅ Prediction generated within 5 seconds
- ✅ Confidence score displayed
- ✅ Prediction stored in history

---

### UC-10: View Explanation
**Actors:** Real Estate Professional, AutoML Engine  
**Description:** User sees which features influenced the prediction

**Preconditions:**
- Prediction generated (UC-09 completed)

**Main Flow:**
1. User clicks "View Explanation"
2. System calculates SHAP values
3. System identifies top 5 influencing features
4. System displays feature contributions
5. System shows direction of influence (positive/negative)
6. System generates visualization

**Acceptance Criteria:**
- ✅ SHAP values calculated
- ✅ Top 5 features displayed
- ✅ Contribution values shown
- ✅ Visualization generated

---

### UC-11: Get Recommendations
**Actors:** Real Estate Professional, AutoML Engine  
**Description:** System provides actionable business insights based on prediction

**Main Flow:**
1. System analyzes prediction and feature importance
2. System assesses confidence level
3. System generates recommendations:
   - Price adjustment suggestions
   - Market positioning
   - Risk assessment
   - Investment recommendations
4. System displays recommendations with reasoning
5. System stores recommendations with prediction

**Acceptance Criteria:**
- ✅ Confidence assessment provided
- ✅ Actionable recommendations given
- ✅ Market positioning shown
- ✅ Recommendations stored

---

## 5. Use Case Dependencies

```
UC-01 (Login)
  ↓
UC-02 (Upload Dataset)
  ↓
UC-03 (View Dataset)
  ↓vV
UC-04 (Select Target)
  ↓
UC-05 (Configure Training)
  ↓
UC-06 (Train Model)
  ↓V
UC-07 (Evaluate Models)
  ↓
UC-08 (Select Best Model)
  ↓
UC-09 (Generate Prediction)
  ↓
UC-10 (View Explanation)
  ↓
UC-11 (Get Recommendations)
```

---

## 6. Actor-Use Case Matrix

| Actor | UC-01 | UC-02 | UC-03 | UC-04 | UC-05 | UC-06 | UC-07 | UC-08 | UC-09 | UC-10 | UC-11 |
|-------|-------|-------|-------|-------|-------|-------|-------|-------|-------|-------|-------|
| **Real Estate Professional** | P | P | P | P | P | - | - | - | P | P | P |
| **AutoML Engine** | - | - | - | S | S | P | P | P | S | P | P |
| **Database/Model Storage** | - | S | S | - | - | S | S | S | S | - | - |

*P = Primary Actor, S = Secondary Actor*

---

## 7. Non-Functional Requirements

| Requirement | Target |
|-------------|--------|
| **Performance** | Predictions within 5 seconds |
| **Availability** | 99% uptime |
| **Security** | JWT authentication, encrypted passwords |
| **Usability** | Intuitive UI, clear error messages |
| **Scalability** | Support 1000+ concurrent users |
| **Reliability** | 100% test pass rate |

---

## 8. Business Rules

- BR-01: Only CSV files accepted (max 100 MB)
- BR-02: Target variable must be numeric (regression) or categorical (classification)
- BR-03: Minimum 20 rows required for training
- BR-04: Train/test split: 80/20
- BR-05: Cross-validation: 5-fold
- BR-06: Model selection: Highest R² (regression) or F1 (classification)
- BR-07: Confidence score = 50 + (R² × 49)
- BR-08: SHAP values calculated for explainability
- BR-09: Only one active model per user
- BR-10: Predictions stored with timestamp and model version

---

**Document Version:** 1.0  
**Status:** Complete  
**Last Updated:** April 26, 2026
