# Lab 4: Software Architecture Style
## Real Estate AutoML Prediction System

---

## I. Why Layered Architecture?

We chose a **Layered Architecture** for this system. It's the best fit because it breaks the system into horizontal layers, where each layer has its own job. This makes the code easier to understand, test, and change.

The system naturally splits into 5 layers based on what we designed in Lab 3 (DFD and UML):

**Layer 1: Presentation Layer** (The UI)
- React.js frontend that users see
- Shows forms, buttons, charts
- Talks to the backend using REST APIs

**Layer 2: API/Router Layer** (The Gateway)
- FastAPI endpoints that handle requests
- Receives login, file uploads, training requests, predictions
- Passes work to the business logic layer

**Layer 3: Business Logic Layer (BLL)** (The Brain)
- `AuthManager`: Checks passwords, creates login tokens
- `Dataset`: Loads CSV files, cleans data, scores quality
- `AutoMLTrainer`: Trains multiple models, picks the best one
- `Explainer`: Explains why the model made a prediction

**Layer 4: Data Access Layer (DAL)** (The Translator)
- `ModelRegistry`: Saves and loads trained models
- Handles all database operations
- Converts between Python objects and database format

**Layer 5: Data Storage Layer** (The Vault)
- **D1: User Database** - Stores login info
- **D2: Dataset Storage** - Stores uploaded CSV files
- **D3: Model Registry** - Stores trained models

### Why This Works

- **Each layer does one thing**: UI layer shows stuff, API layer routes requests, BLL does calculations, DAL talks to databases
- **Easy to test**: You can test each layer separately
- **Easy to change**: If you need to change the database, only the DAL layer changes
- **Easy to scale**: You can run multiple copies of the API layer if needed
- **Reusable code**: The BLL can be used by different frontends (web, mobile, etc.)
- **Matches our design**: The DFD processes map to BLL, the data stores map to storage layer

---

## II. How It All Works Together

### The Big Picture

```
┌─────────────────────────────────────────────────────────────┐
│                  PRESENTATION LAYER                         │
│  React Frontend (Login, Upload, Train, Predict, Explain)   │
└────────────────────┬────────────────────────────────────────┘
                     │ HTTP/REST
┌────────────────────▼────────────────────────────────────────┐
│                  API/ROUTER LAYER                           │
│  FastAPI Endpoints (auth, ingest, train, predict, explain) │
└────────────────────┬────────────────────────────────────────┘
                     │ Function Calls
┌────────────────────▼────────────────────────────────────────┐
│              BUSINESS LOGIC LAYER (BLL)                     │
│  AuthManager | Dataset | AutoMLTrainer | Explainer         │
└────────────────────┬────────────────────────────────────────┘
                     │ Method Calls
┌────────────────────▼────────────────────────────────────────┐
│              DATA ACCESS LAYER (DAL)                        │
│  ModelRegistry | Database Operations | Serialization       │
└────────────────────┬────────────────────────────────────────┘
                     │ SQL/File I/O
┌────────────────────▼────────────────────────────────────────┐
│              DATA STORAGE LAYER                             │
│  D1: User DB | D2: Dataset Storage | D3: Model Registry    │
└─────────────────────────────────────────────────────────────┘
```

### Real Examples: How Data Flows

**When a user logs in:**
```
1. User types email and password in React
2. React sends POST /api/auth/login
3. API layer receives it
4. BLL calls AuthManager.verifyCredentials()
5. DAL queries the user database (D1)
6. BLL compares the password hash
7. BLL creates a JWT token
8. API returns the token to React
9. React stores it and shows the dashboard
```

**When a user uploads a CSV:**
```
1. User picks a CSV file in React
2. React sends POST /api/ingest/upload
3. API layer receives the file
4. BLL calls Dataset.loadFromCSV()
5. BLL calls Dataset.preprocess() to clean it
6. BLL calculates data quality score
7. DAL saves the dataset info to D2
8. API returns success message
9. React shows the data preview
```

**When a user asks for a prediction:**
```
1. User enters property details in React
2. React sends POST /api/predict
3. API layer receives it
4. BLL preprocesses the input data
5. DAL loads the trained model from D3
6. BLL runs the model to get a prediction
7. BLL calculates SHAP values to explain it
8. API returns prediction + explanation
9. React displays the results
```

---

## III. What Each Layer Does

### Layer 1: Presentation Layer (The UI)
**Tools:** React.js 18, React Router v6

**What's in it:**
- `LoginPage`: Login form
- `UploadPage`: File upload and preview
- `TrainPage`: Training settings and progress
- `PredictPage`: Prediction form
- `ExplainPage`: Shows why the model predicted something

**Jobs:**
- Show buttons and forms
- Collect user input
- Display results
- Check that inputs look right
- Keep the user logged in

---

### Layer 2: API/Router Layer (The Gateway)
**Tools:** FastAPI, Pydantic

**Endpoints:**
- `POST /api/auth/login` - Login
- `POST /api/ingest/upload` - Upload CSV
- `GET /api/ingest/preview` - Show CSV preview
- `POST /api/train/start` - Start training
- `GET /api/train/status` - Check training progress
- `POST /api/predict` - Get a prediction
- `GET /api/explain/latest` - Get explanation

**Jobs:**
- Receive HTTP requests
- Check that data looks right (using Pydantic)
- Call the right BLL function
- Send back responses
- Check that the user is logged in
- Log errors

---

### Layer 3: Business Logic Layer (BLL) (The Brain)
**Tools:** Python, scikit-learn, XGBoost, SHAP

**Classes:**

**AuthManager** (handles login)
- `verifyCredentials(email, password)`: Check if password is right
- `generateToken(userId)`: Create login token
- `logout(userId)`: End session

**Dataset** (handles data)
- `loadFromCSV(filePath)`: Read CSV file
- `preprocess()`: Clean data, fix missing values, scale numbers
- `getTrainingSplit()`: Split into 80% training, 20% testing
- `getQualityScore()`: Rate how good the data is

**AutoMLTrainer** (trains models)
- `trainAll(dataset)`: Train multiple models
- `evaluateModels(metric)`: Score each model
- `selectBestModel()`: Pick the winner

**MLModel** (base model class)
- `train(features, labels)`: Train (abstract)
- `predict(features)`: Predict (abstract)
- `getMetrics()`: Return scores

**RegressionModel & ClassificationModel** (actual models)
- Concrete versions of MLModel
- Support Linear Regression, Random Forest, XGBoost

**Explainer** (explains predictions)
- `computeSHAP(model, data)`: Calculate SHAP values
- `generateReport(prediction, model)`: Create explanation
- `getRecommendations()`: Give business advice

**Jobs:**
- Do the actual work (training, predicting)
- Check that data is valid
- Run calculations
- Keep track of state

---

### Layer 4: Data Access Layer (DAL) (The Translator)
**Tools:** SQLAlchemy, joblib, pickle

**Classes:**

**ModelRegistry**
- `saveModel(modelObject)`: Save model to disk
- `loadModel(modelID)`: Load model from disk
- `getMetadata(modelID)`: Get model info
- `listModels()`: List all models

**Database Operations**
- Add/update/delete users
- Store dataset info
- Track training jobs
- Store prediction history

**Jobs:**
- Talk to databases
- Convert Python objects to database format and back
- Manage connections
- Cache frequently used data
- Keep data consistent

---

### Layer 5: Data Storage Layer (The Vault)
**Tools:** SQLite (for testing), PostgreSQL (for production), joblib

**What's stored:**

**D1: User Database**
- Users table: userId, email, passwordHash, role
- Sessions table: sessionId, userId, token, expiryTime
- Purpose: Login info

**D2: Dataset Storage**
- Datasets table: datasetId, userId, filename, rowCount, columnCount, qualityScore
- Files: Raw CSV and cleaned data
- Purpose: Store uploaded files

**D3: Model Registry**
- Models directory: Saved model files (.pkl)
- Metadata: algorithm, scores, training date, features
- Purpose: Store trained models

**Cache:**
- Active datasets (in memory)
- Trained models (in memory)
- User sessions (in memory)

**Jobs:**
- Store data safely
- Provide fast access
- Keep data correct
- Support transactions

---

## IV. How Classes Connect

**Inheritance** (is-a relationship)
- `RegressionModel` is a type of `MLModel`
- `ClassificationModel` is a type of `MLModel`

**Composition** (owns relationship)
- `AutoMLTrainer` owns a `Dataset`
- If the trainer is deleted, the dataset goes away too

**Aggregation** (has relationship)
- `ModelRegistry` has many `MLModel` objects
- Models can exist without the registry

**Association** (uses relationship)
- `User` uses `AutoMLTrainer`
- `User` uses `Explainer`

**Dependency** (depends on relationship)
- `User` needs `AuthManager` to log in
- `Explainer` needs `MLModel` to explain predictions

---

## V. How It Maps to Our Design

**From Lab 3 (DFD):**

**Process 1.0: Login & Authenticate**
- Input: Email and password
- Uses: D1 (User Database)
- Output: Login token

**Process 2.0: Upload & Clean Data**
- Input: CSV file
- Uses: D2 (Dataset Storage)
- Output: Cleaned data

**Process 3.0: AutoML Training & Registry**
- Input: Cleaned data
- Uses: D2 and D3 (Dataset Storage and Model Registry)
- Output: Best trained model

**Process 4.0: Prediction**
- Input: Property details
- Uses: D3 (Model Registry)
- Output: Price prediction

**Process 5.0: Explainer (Insights)**
- Input: Prediction and model
- Uses: D3 (Model Registry)
- Output: Explanation report

**From Lab 2 (Use Cases):**

| Use Case | Layer | Component | Process | Data |
|----------|-------|-----------|---------|------|
| UC-01: Login | API + BLL | AuthManager | 1.0 | D1 |
| UC-02: Upload | API + BLL | Dataset | 2.0 | D2 |
| UC-03: View Dataset | API + BLL | Dataset | 2.0 | D2 |
| UC-04: Select Target | API + BLL | Dataset | 2.0 | D2 |
| UC-05: Configure Training | API + BLL | AutoMLTrainer | 3.0 | D2 |
| UC-06: Train Model | BLL + DAL | AutoMLTrainer | 3.0 | D2, D3 |
| UC-07: Evaluate Models | BLL + DAL | AutoMLTrainer | 3.0 | D3 |
| UC-08: Select Best Model | BLL + DAL | AutoMLTrainer + ModelRegistry | 3.0 | D3 |
| UC-09: Generate Prediction | API + BLL + DAL | ModelRegistry + MLModel | 4.0 | D3 |
| UC-10: View Explanation | API + BLL | Explainer | 5.0 | D3 |
| UC-11: Get Recommendations | API + BLL | Explainer | 5.0 | D3 |

---

## VI. Tech Stack

| Layer | Tools | What It Does |
|-------|-------|-------------|
| **Presentation** | React 18, React Router v6, Recharts | Shows UI and charts |
| **API** | FastAPI, Uvicorn, Pydantic | Handles web requests |
| **BLL** | Python, scikit-learn, XGBoost, SHAP | Does ML work |
| **DAL** | SQLAlchemy, joblib, pickle | Talks to databases |
| **Storage** | SQLite (testing), PostgreSQL (production) | Stores data |

---

## VII. Database Schema

**D1: User Database**
```sql
CREATE TABLE users (
    userId STRING PRIMARY KEY,
    email STRING UNIQUE NOT NULL,
    passwordHash STRING NOT NULL,
    role STRING,
    createdAt TIMESTAMP
);

CREATE TABLE sessions (
    sessionId STRING PRIMARY KEY,
    userId STRING FOREIGN KEY,
    token STRING,
    expiryTime TIMESTAMP
);
```

**D2: Dataset Storage**
```sql
CREATE TABLE datasets (
    datasetId STRING PRIMARY KEY,
    userId STRING FOREIGN KEY,
    filename STRING,
    rowCount INTEGER,
    columnCount INTEGER,
    qualityScore FLOAT,
    uploadedAt TIMESTAMP
);

-- Files stored in: /data/datasets/{datasetId}/
-- - raw.csv (original file)
-- - preprocessed.pkl (cleaned data)
-- - metadata.json (column info)
```

**D3: Model Registry**
```sql
CREATE TABLE models (
    modelId STRING PRIMARY KEY,
    userId STRING FOREIGN KEY,
    algorithm STRING,
    metrics JSON,
    hyperparameters JSON,
    trainingDate TIMESTAMP,
    isActive BOOLEAN
);

-- Files stored in: /models/{modelId}/
-- - model.pkl (saved model)
-- - metadata.json (model info)
```

---

## VIII. Where It Runs

```
┌─────────────────────────────────────────────────────────────┐
│                    DEPLOYMENT LAYERS                        │
└─────────────────────────────────────────────────────────────┘

Presentation Layer
├─ Vercel (React frontend CDN)
└─ URL: https://automl-frontend.vercel.app

API/Router Layer
├─ Render (FastAPI backend)
└─ URL: https://automl-backend.onrender.com

BLL + DAL
├─ Render (same container as API)
└─ Runs with FastAPI

Storage Layer
├─ D1: Supabase PostgreSQL (User Database)
├─ D2: Supabase PostgreSQL + S3 (Dataset Storage)
├─ D3: DagsHub MLflow (Model Registry)
└─ Cache: Redis (optional)
```

---

## IX. Why This Architecture Works

1. **Clear jobs**: Each layer does one thing
2. **Easy to test**: Test each layer separately
3. **Easy to change**: Change one layer without breaking others
4. **Easy to scale**: Run multiple copies of layers
5. **Reusable code**: BLL can be used by different frontends
6. **Matches our design**: Aligns with DFD and UML
7. **Standard pattern**: Developers know how it works
8. **Flexible deployment**: Deploy layers separately
9. **Good data management**: Three separate data stores
10. **Easy to extend**: Add new features without breaking old ones

---

## X. Complete Example: Training a Model

```
User uploads CSV
    ↓
React shows file upload form
    ↓
React sends POST /api/ingest/upload
    ↓
API receives file
    ↓
BLL calls Dataset.loadFromCSV()
    ↓
BLL calls Dataset.preprocess()
    ↓
BLL calculates quality score
    ↓
DAL saves to D2
    ↓
React shows data preview
    ↓
User selects target variable
    ↓
React sends POST /api/train/start
    ↓
BLL calls AutoMLTrainer.trainAll()
    ├─ Load dataset from D2
    ├─ Train multiple models
    ├─ Evaluate each model
    └─ Pick the best one
    ↓
DAL saves model to D3
    ↓
User requests prediction
    ↓
React sends POST /api/predict
    ↓
BLL loads model from D3
    ↓
BLL runs prediction
    ↓
BLL calculates SHAP values
    ↓
API returns prediction + explanation
    ↓
React displays results
```

---

## XI. Potential Problems & Solutions

| Problem | Solution |
|---------|----------|
| Slow requests between layers | Use caching, optimize queries |
| Layers too tightly connected | Use dependency injection |
| Data copied between layers | Use proper data mapping |
| System gets too complex | Split into microservices |
| Too much data to store | Archive old data, clean up |
| Model versions get messy | Use MLflow for versioning |

---

**Architecture Version:** 2.0  
**Last Updated:** April 26, 2026  
**Status:** Complete
