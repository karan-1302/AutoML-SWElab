# Test Cases – Authentication Module
**Assignment 9 – Q1b | CS 331 Software Engineering Lab**

Module tested: `bll/auth_bll.py` and `routers/auth.py`


The 8 test cases are:

| ID | What it tests | One-line workflow |
|----|---------------|-------------------|
| TC-AUTH-01 | Normal login | POST valid credentials → `_validate_credentials` passes → DB finds user → bcrypt matches → JWT returned → 200 |
| TC-AUTH-02 | Wrong password | POST wrong password → validation passes → DB finds user → bcrypt fails → generic 401 |
| TC-AUTH-03 | Email not in DB | POST unknown email → validation passes → DB returns nothing → generic 401 (same message as TC-AUTH-02) |
| TC-AUTH-04 | Empty email | POST empty email → `_validate_credentials` short-circuits immediately → 422, never touches DB |
| TC-AUTH-05 | Bad email format | POST `not-an-email` → `_validate_credentials` runs regex → no `@` match → 422 |
| TC-AUTH-06 | Password too short | POST 3-char password → `_validate_credentials` checks `len < 6` → 422, never touches DB |
| TC-AUTH-07 | JWT contents | POST valid login → get token → decode with secret key → assert sub, email, name, exp all correct |
| TC-AUTH-08 | No token on protected routes | POST/GET with no Authorization header → `oauth2_scheme` finds nothing → 401 before route runs |

Each case has: ID, description, input, expected output, actual output, and pass/fail status.

---

## TC-AUTH-01 – Valid login

| | |
|---|---|
| **Test Case ID** | TC-AUTH-01 |
| **Description** | Login with correct email and password |
| **Input** | email: `demo@realestate.com`, password: `password123` |
| **Expected Output** | HTTP 200, response has `access_token` and correct `user.email` |
| **Actual Output** | HTTP 200, token returned, email matches |
| **Status** | PASS |

---

## TC-AUTH-02 – Wrong password

| | |
|---|---|
| **Test Case ID** | TC-AUTH-02 |
| **Description** | Correct email but wrong password |
| **Input** | email: `demo@realestate.com`, password: `wrongpassword` |
| **Expected Output** | HTTP 401, error says "Incorrect email or password." |
| **Actual Output** | HTTP 401, same error message |
| **Status** | PASS |

---

## TC-AUTH-03 – Email not in database

| | |
|---|---|
| **Test Case ID** | TC-AUTH-03 |
| **Description** | Email doesn't exist in the system |
| **Input** | email: `ghost@nowhere.com`, password: `password123` |
| **Expected Output** | HTTP 401, same generic error (so you can't tell if the email exists or not) |
| **Actual Output** | HTTP 401, "Incorrect email or password." |
| **Status** | PASS |

---

## TC-AUTH-04 – Empty email

| | |
|---|---|
| **Test Case ID** | TC-AUTH-04 |
| **Description** | Email field is left blank |
| **Input** | email: `""`, password: `password123` |
| **Expected Output** | HTTP 422, error says "Email address is required." |
| **Actual Output** | HTTP 422, correct error |
| **Status** | PASS |

---

## TC-AUTH-05 – Bad email format

| | |
|---|---|
| **Test Case ID** | TC-AUTH-05 |
| **Description** | Email doesn't look like a real email address |
| **Input** | email: `not-an-email`, password: `password123` |
| **Expected Output** | HTTP 422, error mentions invalid format |
| **Actual Output** | HTTP 422, "Email address is not in a valid format (e.g. user@domain.com)." |
| **Status** | PASS |

---

## TC-AUTH-06 – Password too short

| | |
|---|---|
| **Test Case ID** | TC-AUTH-06 |
| **Description** | Password is less than 6 characters |
| **Input** | email: `demo@realestate.com`, password: `abc` |
| **Expected Output** | HTTP 422, error says password must be at least 6 characters |
| **Actual Output** | HTTP 422, correct error |
| **Status** | PASS |

---

## TC-AUTH-07 – JWT has correct data

| | |
|---|---|
| **Test Case ID** | TC-AUTH-07 |
| **Description** | After login, decode the token and check it has the right user info |
| **Input** | email: `demo@realestate.com`, password: `password123` |
| **Expected Output** | Token contains `sub`, `email`, `name`, and `exp` (expiry ~8 hours from now) |
| **Actual Output** | All claims present and correct |
| **Status** | PASS |

---

## TC-AUTH-08 – No token = no access

| | |
|---|---|
| **Test Case ID** | TC-AUTH-08 |
| **Description** | Try to hit a protected endpoint without sending a token |
| **Input** | POST `/api/ingest/upload` with no Authorization header |
| **Expected Output** | HTTP 401 |
| **Actual Output** | HTTP 401, "Not authenticated" |
| **Status** | PASS |


**8/8 passed**

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

---

# Defect Report
**BUGS**

---

## BUG-001 – Email regex allows consecutive dots

| | |
|---|---|
| **Bug ID** | BUG-001 |
| **Description** | The regex in `bll/auth_bll.py` accepts emails like `user..name@domain.com` (two dots in a row). That's not a valid email format but the validator lets it through. |
| **Steps to Reproduce** | 1. POST to `/api/auth/login` with `email: "user..name@domain.com"` and any password. 2. You get HTTP 401 (wrong credentials) instead of HTTP 422 (invalid format). |
| **Expected** | HTTP 422 – "Email address is not in a valid format" |
| **Actual** | HTTP 401 – the email passes validation and a DB lookup is attempted |
| **Severity** | Low |
| **Fix** | Tighten the regex to disallow consecutive dots, or use the `email-validator` library instead. |

---

## BUG-002 – Explain endpoint returns 404 instead of 401 when no token is given

| | |
|---|---|
| **Bug ID** | BUG-002 |
| **Description** | The explain route is registered at `/api/explain/latest`, not `/api/explain`. So if you call `GET /api/explain` without a token you get 404 (not found) instead of 401 (unauthorized). This is confusing – it looks like the endpoint doesn't exist. |
| **Steps to Reproduce** | 1. `GET /api/explain` with no Authorization header. 2. Response is 404. 3. `GET /api/explain/latest` with no header gives 401 as expected. |
| **Expected** | HTTP 401 |
| **Actual** | HTTP 404 |
| **Severity** | Medium |
| **Fix** | Either add a root route at `/api/explain` that redirects to `/latest`, or change the router decorator to `@router.get("")` so the endpoint lives at `/api/explain` directly. |

---

## BUG-003 – passlib crashes on Python 3.13 with newer bcrypt

| | |
|---|---|
| **Bug ID** | BUG-003 |
| **Description** | `passlib` uses `bcrypt` internally and runs a wrap-bug detection check on startup. In `bcrypt >= 4.0` the API changed and that check throws `ValueError: password cannot be longer than 72 bytes`. This crashes the entire test setup on Python 3.13 – every test that needs a seeded database fails before it even runs. |
| **Steps to Reproduce** | 1. Install requirements on Python 3.13. 2. Run `python -m pytest tests/`. 3. All tests error out during fixture setup with the ValueError. |
| **Expected** | Tests run normally |
| **Actual** | `ValueError: password cannot be longer than 72 bytes` from `passlib/handlers/bcrypt.py` |
| **Severity** | High |
| **Fix** | Call `bcrypt` directly instead of going through `passlib`. That's what was done in this lab's `utils/security.py`: |

```python
import bcrypt

def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
```

---

## Summary

| Bug ID | Description | Severity | Status |
|--------|-------------|----------|--------|
| BUG-001 | Email regex allows consecutive dots | Low | Open |
| BUG-002 | Explain endpoint returns 404 without token | Medium | Open |
| BUG-003 | passlib/bcrypt crash on Python 3.13 | High | Fixed |
