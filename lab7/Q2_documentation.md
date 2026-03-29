# CS 331 — Software Engineering Lab
# Assignment 7: Business Logic Layer (BLL)
# Q2 Documentation :-

---

## Q2 (A): Business Rules Implementation

Business rules are the conditions, constraints, and domain-specific logic that govern how the application processes data and makes decisions. In our Real Estate AutoML Prediction System, business rules are implemented inside dedicated BLL modules (`lab7/backend/bll/`) that sit between the presentation layer (FastAPI routers + React frontend) and the data access layer (in-memory store + ML services).

### Module 1: Authentication (`bll/auth_bll.py`)

| Rule ID    | Business Rule                                            | Implementation                        |
|------------|----------------------------------------------------------|---------------------------------------|
| BR-AUTH-01 | Email must be in valid format (user@domain.com)          | Regex validation in `_validate_credentials()` |
| BR-AUTH-02 | Both email and password are mandatory fields             | Empty/null checks in `_validate_credentials()` |
| BR-AUTH-03 | Password must be at least 6 characters long              | Length check in `_validate_credentials()` |
| BR-AUTH-04 | User must exist in the user database                     | Lookup via `get_user(email)` in `authenticate_user()` |
| BR-AUTH-05 | Password hash must match stored bcrypt hash              | `verify_password()` call in `authenticate_user()` |
| BR-AUTH-06 | JWT token contains user claims (sub, email, name)        | `create_access_token()` with payload dict |
| BR-AUTH-07 | Token expires after 8 hours                              | `ACCESS_TOKEN_EXPIRE_MINUTES = 480` in security.py |

**Code Example — Credential Validation:**
```python
def _validate_credentials(email: str, password: str) -> list[str]:
    errors = []
    if not email or not email.strip():
        errors.append("Email address is required.")         # BR-AUTH-02
    if not EMAIL_REGEX.match(email.strip()):
        errors.append("Email address is not in a valid format.")  # BR-AUTH-01
    if len(password) < MIN_PASSWORD_LENGTH:
        errors.append(f"Password must be at least {MIN_PASSWORD_LENGTH} characters.")  # BR-AUTH-03
    return errors
```

**Interaction with Presentation Layer:**
- The React `LoginPage.js` mirrors these rules with real-time client-side validation (email format, password length) before sending the request.
- If server-side BLL validation fails, error messages are returned as an array and displayed to the user.

---

### Module 2: Data Ingestion (`bll/ingest_bll.py`)

| Rule ID    | Business Rule                                            | Implementation                        |
|------------|----------------------------------------------------------|---------------------------------------|
| BR-ING-01 | Only `.csv` files are accepted                           | Extension check in `_validate_file()` |
| BR-ING-02 | File size must not exceed 50 MB                          | Byte-length check in `_validate_file()` |
| BR-ING-03 | CSV must be parseable by pandas                          | `pd.read_csv()` with try/except |
| BR-ING-04 | Dataset must not be empty (0 rows)                       | `df.empty` check in `_validate_dataframe()` |
| BR-ING-05 | Dataset must have at least 2 columns                     | Column count check in `_validate_dataframe()` |
| BR-ING-06 | Dataset must have at least 10 rows for ML                | Row count check in `_validate_dataframe()` |
| BR-ING-07 | Data quality report is computed                          | `_compute_quality_report()` function |
| BR-ING-08 | Preview is limited to 10 rows                            | `PREVIEW_ROWS = 10` constant |
| BR-ING-09 | NaN replaced with None for JSON serialization            | `pd.notnull()` filtering |

**Code Example — Quality Scoring:**
```python
def _compute_quality_report(df):
    score = 100
    score -= min(missing_pct, 40)        # Deduct for missing data
    score -= min(dup_pct / 2, 20)        # Deduct for duplicates
    if len(df) < 100:
        score -= 10                      # Penalty for small datasets
    return {"quality_score": max(0, round(score, 1)), ...}
```

**Interaction with Presentation Layer:**
- The React `UploadPage.js` displays the quality report with a visual score badge, per-column missing data table, and column type breakdown (numeric vs categorical).

---

### Module 3: AutoML Training (`bll/train_bll.py`)

| Rule ID    | Business Rule                                            | Implementation                        |
|------------|----------------------------------------------------------|---------------------------------------|
| BR-TRN-01 | Dataset must exist in the store                          | `DATASETS.get(dataset_id)` check |
| BR-TRN-02 | Target column must exist in the dataset                  | Column membership check |
| BR-TRN-03 | Target column must be numeric (regression only)          | `pd.api.types.is_numeric_dtype()` check |
| BR-TRN-04 | Only one training job per user at a time                 | Status == "running" check |
| BR-TRN-05 | Dataset needs at least 20 valid rows                     | Row count after dropping NaN targets |
| BR-TRN-06 | Best model selected by highest R² score                  | Score comparison in automl_trainer.py |
| BR-TRN-07 | Model scores rounded for readability                     | `round()` in `get_formatted_training_status()` |

**Interaction with Presentation Layer:**
- The React `TrainPage.js` shows algorithm progress bars updated via polling, and the best model banner displays the selected model with R², RMSE, and MAE.

---

### Module 4: Prediction (`bll/predict_bll.py`)

| Rule ID    | Business Rule                                            | Implementation                        |
|------------|----------------------------------------------------------|---------------------------------------|
| BR-PRD-01 | Trained model must exist before prediction               | `get_training_job()` status check |
| BR-PRD-02 | All property features are required                       | Presence checks in `_validate_features()` |
| BR-PRD-03 | Numeric fields must be within valid ranges               | Min/max range checks per FIELD_RULES |
| BR-PRD-04 | Confidence = 50 + R² × 49 (50%-99% range)               | `_compute_confidence()` function |
| BR-PRD-05 | Predicted price rounded to 2 decimal places              | `round(prediction, 2)` |
| BR-PRD-06 | Result saved for explainability downstream               | `set_last_prediction()` call |
| BR-PRD-07 | Waterfront: 0/1; View: 0-4; Condition: 1-5; Grade: 1-13 | Defined in `FIELD_RULES` dict |
| BR-PRD-08 | Year built between 1800 and current year                 | Range in `FIELD_RULES` |
| BR-PRD-09 | ZIP code must be a non-empty string                      | String non-empty check |

**Interaction with Presentation Layer:**
- The React `PredictPage.js` performs real-time per-field validation on blur, showing inline error messages that mirror the BLL rules. Range indicators ([min–max]) are shown next to each label.

---

### Module 5: Explainability (`bll/explain_bll.py`)

| Rule ID    | Business Rule                                            | Implementation                        |
|------------|----------------------------------------------------------|---------------------------------------|
| BR-EXP-01 | A prediction must exist before explanation               | `get_last_prediction()` check |
| BR-EXP-02 | TreeExplainer for tree-based models (RF, XGB, GB)        | Model type check + SHAP explainer selection |
| BR-EXP-03 | LinearExplainer for linear models                        | Fallback explainer selection |
| BR-EXP-04 | Finite-difference fallback if SHAP fails                 | Perturb-and-predict sensitivity analysis |
| BR-EXP-05 | One-hot features aggregated to original column names     | `split("__")` + sum aggregation |
| BR-EXP-06 | Maximum 6 recommendation cards                          | `recs[:6]` cap |
| BR-EXP-07 | Price tiers: Premium (>$700K), Mid ($400K-$700K), Entry  | Conditional recommendation strings |
| BR-EXP-08 | SHAP values sorted by absolute value                     | `sort(key=abs(value), reverse=True)` |

**Interaction with Presentation Layer:**
- The React `ExplainPage.js` renders a horizontal bar chart (Recharts) colour-coded by direction, a ranked feature table, and recommendation cards. The BLL pipeline steps are visually displayed to the user.

---

## Q2 (B): Validation Logic

Validation logic ensures that data entering our system is correct, consistent, and in the proper format before being processed further. Our application implements **three tiers** of validation:

### Tier 1: Client-Side Validation (Presentation Layer)

Implemented in the React frontend, providing **immediate feedback** without a network round-trip. These rules **mirror** the backend BLL rules for consistency.

| Page         | Validation                                | Reference       |
|--------------|-------------------------------------------|-----------------|
| LoginPage    | Email format regex, password ≥ 6 chars    | auth_bll rules  |
| UploadPage   | .csv extension check, 50 MB size limit    | ingest_bll rules|
| PredictPage  | Per-field range checks on blur            | predict_bll rules|
| TrainPage    | Target column selection required          | train_bll rules |

**Example — Real-time field validation in PredictPage.js:**
```javascript
function validateField(field, value) {
  if (!value && value !== 0) return `${field.label} is required (BR-PRD-02)`;
  if (field.type === 'number') {
    const num = Number(value);
    if (num < field.min || num > field.max) {
      return `${field.label} must be between ${field.min} and ${field.max} (BR-PRD-03)`;
    }
  }
  return null;
}
```

### Tier 2: Pydantic Schema Validation (API Layer)

FastAPI uses Pydantic models (`models/schemas.py`) for automatic request validation. Invalid requests are rejected with HTTP 422 **before** reaching the BLL.

**Example — PredictRequest schema with field constraints:**
```python
class PredictRequest(BaseModel):
    bedrooms:    float = Field(..., ge=0, le=20)
    bathrooms:   float = Field(..., ge=0, le=10)
    sqft_living: float = Field(..., ge=1)
    sqft_lot:    float = Field(..., ge=1)
    floors:      float = Field(..., ge=1, le=5)
    waterfront:  int   = Field(0, ge=0, le=1)
    view:        int   = Field(0, ge=0, le=4)
    condition:   int   = Field(..., ge=1, le=5)
    grade:       int   = Field(..., ge=1, le=13)
    yr_built:    int   = Field(..., ge=1800, le=2025)
    zipcode:     str
```

### Tier 3: Business Logic Validation (BLL)

The deepest validation layer, enforcing **domain-specific rules** that cannot be expressed in schemas alone:

| BLL Module     | Validation                                                      |
|----------------|-----------------------------------------------------------------|
| `auth_bll`     | User existence check, password hash verification                |
| `ingest_bll`   | CSV parseability, minimum row/column count, data quality scoring|
| `train_bll`    | Target column must be numeric, min 20 rows, no concurrent jobs  |
| `predict_bll`  | Trained model must exist, feature range enforcement             |
| `explain_bll`  | Prediction must exist before explanation                        |

**Example — Training validation in train_bll.py:**
```python
def validate_training_request(dataset_id, target_column, user_id):
    # BR-TRN-03: Target column must be numeric
    if not pd.api.types.is_numeric_dtype(df[target_column]):
        return False, {
            "errors": [f"Target column '{target_column}' must be numeric for regression."],
            "code": 422,
        }
    # BR-TRN-04: No concurrent training
    existing = get_training_job(user_id)
    if existing and existing.get("status") == "running":
        return False, {
            "errors": ["A training job is already running."],
            "code": 409,
        }
```

### Validation Flow Diagram

```
User Input → [Tier 1: Client JS] → [HTTP Request] → [Tier 2: Pydantic] → [Tier 3: BLL] → Processing
    ↑              ↓                                       ↓                    ↓
    └── Instant ←── Error                           422 Response          Domain Error
        Feedback    Message                                                 (400/401/409/422)
```

---

## Q2 (C): Data Transformation

Data transformation refers to converting data from one format or structure to another as it flows between the data layer, business logic layer, and presentation layer. Our application implements the following transformations:

### 1. Data Ingestion Transformations (`ingest_bll.py`)

| ID       | Transformation                           | From             | To                        |
|----------|------------------------------------------|------------------|---------------------------|
| DT-ING-01| CSV parsing                              | Raw bytes        | pandas DataFrame          |
| DT-ING-02| Preview generation                       | DataFrame        | `list[dict]` (JSON-safe)  |
| DT-ING-03| Column type detection                    | DataFrame dtypes | `numeric_columns` / `categorical_columns` lists |

**Example — CSV bytes to structured preview:**
```python
# DT-ING-01: Raw CSV bytes → DataFrame
df = pd.read_csv(io.BytesIO(file_bytes))

# DT-ING-02: DataFrame → JSON-safe preview (NaN → None)
preview_df = df.head(PREVIEW_ROWS).where(pd.notnull(df.head(PREVIEW_ROWS)), None)
preview = preview_df.to_dict(orient="records")

# DT-ING-03: Type classification
numeric_cols = df.select_dtypes(include=["int64", "float64"]).columns.tolist()
categorical_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
```

**How it serves the UI:** The React `UploadPage.js` receives the preview as an array of objects and renders it in a `DataGrid` component. Column types are displayed as colour-coded tags (green for numeric, orange for categorical).

### 2. Training Transformations (`train_bll.py` + `automl_trainer.py`)

| ID       | Transformation                           | From             | To                        |
|----------|------------------------------------------|------------------|---------------------------|
| DT-TRN-01| Training status formatting               | Raw job dict     | `TrainStatusResponse` with rounded scores |
| DT-TRN-02| Progress normalisation                   | Internal progress dict | 0-100 percentages |

**Example — Raw job → formatted response:**
```python
# DT-TRN-01: Transform raw scores
best_model_out = ModelScore(
    name=name,
    r2=round(scores["r2"], 6),
    rmse=round(scores["rmse"], 4),
    mae=round(scores["mae"], 4),
)
```

**ML Pipeline Data Transformation (automl_trainer.py):**
```python
# Numeric features: impute missing (median) → standardise (z-score)
numeric_pipe = Pipeline([
    ("imputer", SimpleImputer(strategy="median")),
    ("scaler",  StandardScaler()),
])
# Categorical features: impute missing ("Unknown") → one-hot encode
categorical_pipe = Pipeline([
    ("imputer", SimpleImputer(strategy="constant", fill_value="Unknown")),
    ("onehot",  OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
])
```

### 3. Prediction Transformations (`predict_bll.py`)

| ID       | Transformation                           | From             | To                        |
|----------|------------------------------------------|------------------|---------------------------|
| DT-PRD-01| Feature assembly                         | Form input dict  | Single-row DataFrame (training schema) |
| DT-PRD-02| Price extraction                         | numpy array      | Rounded float             |
| DT-PRD-03| Confidence derivation                    | R² score (0-1)   | Percentage (50-99%)       |

**Example — Form input → DataFrame → Prediction:**
```python
# DT-PRD-01: Build input DataFrame matching training schema
input_row = {col: features.get(col) for col in feature_columns}
input_df = pd.DataFrame([input_row])

# DT-PRD-02: Pipeline prediction → scalar price
prediction = float(pipeline.predict(input_df)[0])
prediction = round(prediction, 2)

# DT-PRD-03: R² → human-readable confidence
confidence = round(50 + max(0.0, min(r2, 1.0)) * 49, 1)
```

**How it serves the UI:** The React `PredictPage.js` displays the predicted price formatted as US currency (`Intl.NumberFormat`), the confidence as a percentage, and derived metrics (price per sq ft).

### 4. Explainability Transformations (`explain_bll.py`)

| ID       | Transformation                           | From             | To                        |
|----------|------------------------------------------|------------------|---------------------------|
| DT-EXP-01| SHAP value aggregation                   | Raw SHAP array + transformed feature names | Feature-name-to-value dict |
| DT-EXP-02| Entry formatting                         | Dict of values   | Sorted `ShapEntry` list   |
| DT-EXP-03| Recommendation generation                | SHAP values + price | Plain-English recommendation strings |

**Example — One-hot feature aggregation:**
```python
# DT-EXP-01: Map one-hot features back to original columns
for fname, sv in zip(feature_names_out, shap_vals):
    original = fname.split("__")[-1]          # "num__sqft_living" → "sqft_living"
    base = original.split("_")[0]              # "zipcode_98103" → "zipcode"
    shap_dict[matched] = shap_dict.get(matched, 0.0) + float(sv)  # Aggregate
```

**How it serves the UI:** The React `ExplainPage.js` renders SHAP values as a colour-coded horizontal bar chart (blue = positive, red = negative) and investment recommendation cards with emoji icons.

### Overall Data Flow Diagram

```
┌──────────────────┐     ┌──────────────────────┐     ┌──────────────────┐
│  PRESENTATION    │     │  BUSINESS LOGIC      │     │  DATA ACCESS     │
│  LAYER (UI)      │     │  LAYER (BLL)         │     │  LAYER           │
├──────────────────┤     ├──────────────────────┤     ├──────────────────┤
│                  │     │                      │     │                  │
│  React Pages     │◄───►│  auth_bll.py         │◄───►│  store.py        │
│  ├─ LoginPage    │     │  ingest_bll.py       │     │  (USERS dict)    │
│  ├─ UploadPage   │     │  train_bll.py        │     │  (DATASETS dict) │
│  ├─ TrainPage    │     │  predict_bll.py      │     │  (TRAINING_JOBS) │
│  ├─ PredictPage  │     │  explain_bll.py      │     │  (PREDICTIONS)   │
│  └─ ExplainPage  │     │                      │     │                  │
│                  │     │  ↕ Validation         │     │  automl_trainer  │
│  FastAPI Routers │     │  ↕ Business Rules     │     │  (sklearn + XGB) │
│  (thin HTTP      │     │  ↕ Data Transform     │     │                  │
│   handlers)      │     │                      │     │  security.py     │
│                  │     │                      │     │  (JWT + bcrypt)  │
└──────────────────┘     └──────────────────────┘     └──────────────────┘
```
