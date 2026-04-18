# Test Cases – Authentication Module
**Assignment 9 – Q1b | CS 331 Software Engineering Lab**

Module tested: `bll/auth_bll.py` and `routers/auth.py`

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

---

## Summary

| ID | Description | Status |
|----|-------------|--------|
| TC-AUTH-01 | Valid login | PASS |
| TC-AUTH-02 | Wrong password | PASS |
| TC-AUTH-03 | Email not found | PASS |
| TC-AUTH-04 | Empty email | PASS |
| TC-AUTH-05 | Bad email format | PASS |
| TC-AUTH-06 | Password too short | PASS |
| TC-AUTH-07 | JWT claims | PASS |
| TC-AUTH-08 | No token | PASS |

**8/8 passed**
