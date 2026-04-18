# Assignment 9 – Guide

This document walks through every file in the lab9 folder, what it is, and how it all fits together.

---

## Folder structure

```
lab9/
├── guide.md                  ← this file
├── README.md                 ← quick start
├── test_plan.md              ← Q1a
├── test_cases.md             ← Q1b
├── test_execution_log.txt    ← Q2a evidence
├── defect_report.md          ← Q2b
└── backend/
    ├── main.py               ← FastAPI app (copied from lab8)
    ├── requirements.txt
    ├── bll/                  ← business logic (auth, ingest, train, predict, explain)
    ├── dal/                  ← database layer (SQLAlchemy models + repositories)
    ├── routers/              ← HTTP endpoints (thin, just call BLL)
    ├── services/             ← ML training logic
    ├── utils/                ← security helpers (JWT, password hashing)
    └── tests/
        ├── conftest.py       ← shared test setup (fixtures)
        └── test_assignment9.py ← the 8 test cases
```

The `backend/` folder is the lab8 backend copied over. The only file that was changed is `utils/security.py` — more on that in the bugs section.

---

## The assignment questions

The assignment had 4 parts:

| Question | What it asked for | File |
|----------|-------------------|------|
| Q1a | Write a test plan | `test_plan.md` |
| Q1b | Design 8 test cases for one module | `test_cases.md` |
| Q2a | Run the tests and show evidence | `test_execution_log.txt` |
| Q2b | Find and document 3 bugs | `defect_report.md` |

---

## test_plan.md

This is the Q1a answer. A test plan is basically a document that says what you're going to test, how, and when you'll consider it done.

**Objective** – what we're trying to verify (login works, bad inputs are rejected, protected routes block unauthenticated requests, etc.)

**Scope** – lists the modules we're testing (auth, ingest, train, predict, explain, DAL, security utils) and what we're explicitly not testing (the React frontend, deployment, third-party ML libraries).

**Types of testing** – we used a mix:
- *Unit tests* – call a single function directly and check the output
- *Integration tests* – test how the router, BLL, and DAL work together
- *Black box tests* – send an HTTP request and check the response without caring about internals
- *White box tests* – call internal functions like `_validate_credentials()` directly
- *Security tests* – check that endpoints return 401 when no token is sent

**Entry/exit criteria** – entry criteria are the conditions that need to be true before testing starts (app runs, dependencies installed, etc.). Exit criteria are what "done" looks like (all 8 cases run, bugs documented, log saved).

---

## test_cases.md

This is the Q1b answer. We picked the **authentication module** (`bll/auth_bll.py` + `routers/auth.py`) because it has clear inputs, clear expected outputs, and covers both happy path and error cases.

The 8 test cases are:

| ID | What it tests |
|----|---------------|
| TC-AUTH-01 | Normal login – should return 200 and a token |
| TC-AUTH-02 | Wrong password – should return 401 |
| TC-AUTH-03 | Email not in DB – should also return 401 (same message, no hint) |
| TC-AUTH-04 | Empty email – should return 422 before touching the DB |
| TC-AUTH-05 | Bad email format (no @, etc.) – should return 422 |
| TC-AUTH-06 | Password under 6 chars – should return 422 |
| TC-AUTH-07 | JWT contents – decode the token and check sub, email, name, exp |
| TC-AUTH-08 | No token on protected endpoints – should return 401 |

Each case has: ID, description, input, expected output, actual output, and pass/fail status.

---

## test_execution_log.txt

This is the Q2a evidence. It's the raw output from running pytest, saved to a file. It shows all 27 sub-tests passing with their names and timing.

To regenerate it yourself:
```bash
cd backend
python -m pytest tests/test_assignment9.py -v
```

---

## defect_report.md

This is the Q2b answer. Three bugs were found during testing:

**BUG-001 (Low)** – The email regex in `bll/auth_bll.py` accepts `user..name@domain.com` (consecutive dots). It passes validation when it shouldn't. The fix is to tighten the regex or use a proper email validation library.

**BUG-002 (Medium)** – The explain endpoint is at `/api/explain/latest`, not `/api/explain`. Calling the wrong path without a token gives 404 instead of 401, which is confusing. Found this while writing TC-AUTH-08. The fix is to either add a root route or rename the decorator.

**BUG-003 (High)** – `passlib` (the password hashing library used in lab8) crashes on Python 3.13 with newer versions of `bcrypt`. It throws a `ValueError` during its own startup check, which breaks every test that needs a database with a user in it. This was fixed in the lab9 backend by calling `bcrypt` directly instead of going through `passlib`.

---

## backend/tests/conftest.py

`conftest.py` is a special pytest file. Anything defined here is automatically available to all test files in the same folder — you don't need to import it.

It defines **fixtures**, which are reusable setup functions. pytest injects them into test functions by matching the parameter name.

### `test_db`
Creates a brand new SQLite database in memory for each test. Uses `StaticPool` so the same connection object is reused within a single test (SQLite in-memory databases disappear when the connection closes). All tables are created at the start and dropped at the end.

```
test starts → create engine → create tables → yield db session → drop tables → test ends
```

### `seeded_db`
Depends on `test_db`. Takes the empty database and inserts one user (`demo@realestate.com` / `password123`). This is the user most tests log in as.

```
test_db (empty DB) → add demo user → commit → return db
```

### `client`
Depends on `seeded_db`. Creates a FastAPI `TestClient` — this lets us make HTTP requests to the app without actually starting a server. The key part is `dependency_overrides`: FastAPI normally injects the real database session into routes via `get_db`. We replace that with a function that returns our in-memory test database instead. After the test, the override is cleared.

```
seeded_db → override get_db → create TestClient → yield client → clear override
```

### `auth_token` and `auth_headers`
`auth_token` generates a real signed JWT for the demo user. `auth_headers` wraps it in `{"Authorization": "Bearer <token>"}` — the format FastAPI's `OAuth2PasswordBearer` expects. These are used in tests that need to be authenticated.

---

## backend/tests/test_assignment9.py

The actual test code. Each class maps to one test case from `test_cases.md`.

### How the tests are structured

Each class has 2–5 methods. They all receive `client` (or sometimes `seeded_db`) as a parameter — pytest sees that name and automatically runs the matching fixture from `conftest.py`.

Most tests follow this pattern:
1. Use `client.post(...)` or `client.get(...)` to make an HTTP request
2. Check `response.status_code`
3. Sometimes also check `response.json()` for the error message content

### White box vs black box

Some tests go through the HTTP layer (black box):
```python
response = client.post("/api/auth/login", json={"email": "", "password": "abc"})
assert response.status_code == 422
```

Others call the BLL function directly (white box), skipping the router entirely:
```python
errors = _validate_credentials("", "password123")
assert "Email address is required." in errors
```

Both approaches test the same logic, just from different angles.

### The parametrize decorator (TC-AUTH-05)

```python
@pytest.mark.parametrize("bad_email", [
    "missing_at_sign",
    "missing@",
    "@nodomain.com",
    "spaces in@email.com",
])
def test_various_bad_formats(self, bad_email):
    errors = _validate_credentials(bad_email, "password123")
    assert len(errors) > 0
```

`@pytest.mark.parametrize` runs the same test function multiple times, once for each value in the list. Instead of writing four separate test functions that do the same thing, you write one and let pytest loop through the inputs. In the output you'll see it listed as `test_various_bad_formats[missing_at_sign]`, `test_various_bad_formats[missing@]`, etc.

### TC-AUTH-06 boundary test

```python
def test_exactly_6_chars_passes_validation(self, client):
    response = client.post(
        "/api/auth/login",
        json={"email": "demo@realestate.com", "password": "abc123"},
    )
    assert response.status_code == 401
```

This checks the boundary between "too short" (422) and "valid length" (401). `abc123` is exactly 6 characters so it should pass the length check. The login still fails because it's the wrong password, but the important thing is we get 401 (auth failure) not 422 (validation failure). This confirms the minimum length is 6, not 7.

### TC-AUTH-07 JWT decoding

```python
token = response.json()["access_token"]
secret = os.getenv("JWT_SECRET_KEY", "cs331-super-secret-key-change-in-production")
payload = jwt.decode(token, secret, algorithms=["HS256"])
assert payload.get("sub") == "user-001"
```

We log in, grab the token from the response, then decode it using the same secret key the app uses to sign it. This lets us inspect the payload directly and check that the right user data was embedded. We also check `exp` (expiry) is roughly 8 hours from now.

---

## How the test cases connect to the modules

The two files being tested are:

- **`bll/auth_bll.py`** — contains all the actual logic. Two things live here: `_validate_credentials()` which checks the inputs before touching the database, and `authenticate_user()` which runs the full login flow (validate → DB lookup → password check → generate token).
- **`routers/auth.py`** — a thin HTTP wrapper. It receives the POST request, calls `authenticate_user()`, and either returns the result or raises an `HTTPException`. It has no logic of its own.

Here's how each test case maps to specific code in those files:

---

### TC-AUTH-01 – valid login

**Endpoint hit:** `POST /api/auth/login`

**Path through the code:**
```
routers/auth.py  →  login()
    calls authenticate_user(email, password, db)  [auth_bll.py]
        _validate_credentials() → no errors
        get_user_by_email(db, email) → finds the demo user
        verify_password("password123", hashed) → True
        create_access_token({sub, email, name}) → JWT string
    returns (True, {access_token, user})
router returns LoginResponse with 200
```

The test checks the status code, that `access_token` is in the response, and that `user.email` matches. All three things come from the final `return` in `authenticate_user()`.

---

### TC-AUTH-02 – wrong password

**Endpoint hit:** `POST /api/auth/login`

**Path through the code:**
```
authenticate_user()  [auth_bll.py]
    _validate_credentials() → no errors (email is valid, password is long enough)
    get_user_by_email() → finds the user
    verify_password("wrongpassword", hashed) → False
    returns (False, {"errors": ["Incorrect email or password."], "code": 401})
router raises HTTPException(401)
```

The test checks that the status is 401 and that the error message is the generic one. The generic message is intentional — `auth_bll.py` uses the same string for both "wrong password" and "user not found" so you can't tell which one it was.

---

### TC-AUTH-03 – email not in database

**Endpoint hit:** `POST /api/auth/login`

**Path through the code:**
```
authenticate_user()  [auth_bll.py]
    _validate_credentials() → no errors
    get_user_by_email(db, "ghost@nowhere.com") → returns None
    returns (False, {"errors": ["Incorrect email or password."], "code": 401})
router raises HTTPException(401)
```

Same 401 and same error message as TC-AUTH-02. The test confirms this — both wrong password and missing email produce identical responses. This is the correct behaviour because if the error said "email not found" an attacker could use the login form to check whether any email is registered.

---

### TC-AUTH-04 – empty email

**Endpoint hit:** `POST /api/auth/login` (black box tests), and `_validate_credentials()` directly (white box test)

**Path through the code:**
```
authenticate_user()  [auth_bll.py]
    _validate_credentials("", "password123")
        email is empty → appends "Email address is required."
        returns early (short-circuit, doesn't check format or password length)
    returns (False, {"errors": [...], "code": 422})
router raises HTTPException(422)
```

The short-circuit in `_validate_credentials()` is important — if email is missing it returns immediately without running the regex check. The white box test (`test_bll_directly`) calls `_validate_credentials()` directly to confirm this without going through HTTP at all.

---

### TC-AUTH-05 – bad email format

**Endpoint hit:** `POST /api/auth/login` (black box), `_validate_credentials()` directly (white box + parametrize)

**Path through the code:**
```
_validate_credentials("not-an-email", "password123")  [auth_bll.py]
    email is not empty → passes the required check
    EMAIL_REGEX.match("not-an-email") → None (no @ sign)
    appends "Email address is not in a valid format (e.g. user@domain.com)."
    password is long enough → no error there
    returns ["Email address is not in a valid format..."]
```

`EMAIL_REGEX` is defined at the top of `auth_bll.py`:
```python
EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
```

The parametrized test runs `_validate_credentials()` four times with different broken email strings to make sure the regex catches all of them.

---

### TC-AUTH-06 – password too short

**Endpoint hit:** `POST /api/auth/login`

**Path through the code:**
```
_validate_credentials("demo@realestate.com", "abc")  [auth_bll.py]
    email is valid → passes
    len("abc") = 3, MIN_PASSWORD_LENGTH = 6
    appends "Password must be at least 6 characters."
    returns ["Password must be at least 6 characters."]
```

`MIN_PASSWORD_LENGTH = 6` is a constant at the top of `auth_bll.py`. The boundary test (`test_exactly_6_chars_passes_validation`) sends a 6-character password and confirms it gets past `_validate_credentials()` — the 401 it gets back means the validation passed and the failure was at the password comparison step instead.

---

### TC-AUTH-07 – JWT has correct data

**Endpoint hit:** `POST /api/auth/login`

**Path through the code:**
```
authenticate_user()  [auth_bll.py]
    validation passes, user found, password matches
    create_access_token({"sub": user.user_id, "email": user.email, "name": user.name})
        [utils/security.py]
        payload["exp"] = now + 8 hours
        jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    returns token in response
```

The test logs in, takes the token from the response, and decodes it using `jose.jwt.decode()` with the same secret key. This is the only test that looks inside the token rather than just checking the HTTP status. It verifies that `authenticate_user()` is putting the right data into the token and that the expiry is set correctly.

---

### TC-AUTH-08 – no token = blocked

**Endpoints hit:** `/api/ingest/upload`, `/api/predict`, `/api/explain/latest`, `/api/train/start`

This test case is different — it's not testing `auth_bll.py` at all. It's testing that the other routers correctly require authentication. Each of those routes has this in its signature:

```python
current_user: dict = Depends(get_current_user)
```

`get_current_user` is in `utils/security.py`. It reads the `Authorization` header, decodes the token, and returns the user dict. If there's no header, FastAPI's `OAuth2PasswordBearer` raises a 401 before the route function even runs.

```
request arrives with no Authorization header
    OAuth2PasswordBearer sees no token
    raises HTTPException(401, "Not authenticated")
route function never executes
```

The `test_fake_token_blocked` sub-test goes one step further — it sends a token that looks like a JWT but has a bad signature. `get_current_user` calls `decode_token()` which calls `jwt.decode()`, the signature check fails, and it raises 401.

---

## How it all connects

```
pytest runs test_assignment9.py
    │
    ├── needs `client` fixture
    │       └── needs `seeded_db` fixture
    │               └── needs `test_db` fixture
    │                       └── creates in-memory SQLite DB
    │               └── inserts demo user into DB
    │       └── overrides FastAPI's get_db to use test DB
    │       └── creates TestClient
    │
    ├── test sends HTTP request via TestClient
    │       └── FastAPI router receives it
    │               └── calls BLL function
    │                       └── BLL calls DAL (which hits the test DB)
    │                       └── BLL returns result
    │               └── router returns HTTP response
    │
    └── test checks status code and/or response body
```

The whole point of the fixture chain is that each test gets a clean, isolated environment. No test can affect another because the database is created fresh and destroyed after every single test function.
