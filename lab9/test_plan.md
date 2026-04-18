# Test Plan – Real Estate AutoML
**Assignment 9 – Q1a | CS 331 Software Engineering Lab**

---

## Objective

The goal of testing is to make sure the backend works correctly – that login, file upload, training, prediction, and explainability all behave as expected. We also want to check that the database layer (added in Lab 8) saves and retrieves data properly, and that protected endpoints can't be accessed without a valid token.

---

## Scope

**What we're testing:**
- Auth – login, JWT token, input validation
- Ingest – CSV upload, file checks, data quality
- Training – starting a job, status updates, model selection
- Prediction – input validation, running the model, saving results
- Explainability – SHAP values, recommendations
- DAL repositories – user, dataset, training job, prediction tables
- Security utils – password hashing, token creation/verification

**What we're NOT testing:**
- The React frontend
- Deployment/infrastructure setup
- Performance or load
- Internal scikit-learn / XGBoost / SHAP library code

---

## Types of Testing

- **Unit tests** – test individual functions in isolation (validators, BLL logic, utilities)
- **Integration tests** – test how layers talk to each other (router → BLL → DAL)
- **Black box tests** – send HTTP requests and check the responses, no knowledge of internals
- **White box tests** – test internal logic branches directly (e.g. calling `_validate_credentials()`)
- **Security tests** – confirm that endpoints return 401 when no token is provided

---

## Tools

- **pytest** – test runner
- **FastAPI TestClient** – makes HTTP requests without needing a running server
- **SQLite in-memory** – isolated database per test, no leftover state
- **bcrypt** – password hashing in fixtures
- **pandas** – building test DataFrames

---

## Entry Criteria

Before testing starts:
1. `python main.py` runs without errors
2. All packages from `requirements.txt` are installed
3. The database seeds correctly on startup
4. The Lab 8 test suite still passes (no regressions)

## Exit Criteria

Testing is done when:
1. All 8 test cases have been run and results are written down
2. At least 7 out of 8 pass
3. Any bugs found are documented with steps to reproduce and a suggested fix
4. The test log is saved as evidence
