# Assignment 9 - CS 331 Software Engineering Lab
# Testing the authentication module (bll/auth_bll.py + routers/auth.py)
#
# TC-AUTH-01  valid login
# TC-AUTH-02  wrong password
# TC-AUTH-03  email not in database
# TC-AUTH-04  empty email
# TC-AUTH-05  bad email format
# TC-AUTH-06  password too short
# TC-AUTH-07  JWT has correct data
# TC-AUTH-08  no token = blocked

import io
import os
import time
import pytest
import jose.jwt as jwt

from bll.auth_bll import _validate_credentials


# ------------------------------------------------------------------
# TC-AUTH-01: valid login
# ------------------------------------------------------------------

class TestTC_AUTH_01:

    def test_status_code(self, client):
        # send a POST to the login endpoint with correct credentials
        # the server should find the user, verify the password, and return 200
        response = client.post(
            "/api/auth/login",
            json={"email": "demo@realestate.com", "password": "password123"},
        )
        assert response.status_code == 200

    def test_token_is_returned(self, client):
        # on a successful login the response body must include access_token
        # we also check it's not an empty string
        response = client.post(
            "/api/auth/login",
            json={"email": "demo@realestate.com", "password": "password123"},
        )
        data = response.json()
        assert "access_token" in data
        assert len(data["access_token"]) > 0

    def test_user_email_in_response(self, client):
        # the response also returns a user object - check the email matches what we sent
        response = client.post(
            "/api/auth/login",
            json={"email": "demo@realestate.com", "password": "password123"},
        )
        assert response.json()["user"]["email"] == "demo@realestate.com"


# ------------------------------------------------------------------
# TC-AUTH-02: wrong password
# ------------------------------------------------------------------

class TestTC_AUTH_02:

    def test_status_code(self, client):
        # the email exists in the DB but the password is wrong
        # bcrypt comparison will fail so we expect 401
        response = client.post(
            "/api/auth/login",
            json={"email": "demo@realestate.com", "password": "wrongpassword"},
        )
        assert response.status_code == 401

    def test_error_message(self, client):
        # the error message should be generic - it shouldn't say "wrong password"
        # because that would let someone know the email is valid (user enumeration)
        response = client.post(
            "/api/auth/login",
            json={"email": "demo@realestate.com", "password": "wrongpassword"},
        )
        detail = response.json().get("detail", [])
        assert any("Incorrect email or password" in str(d) for d in detail)


# ------------------------------------------------------------------
# TC-AUTH-03: email not in database
# ------------------------------------------------------------------

class TestTC_AUTH_03:

    def test_status_code(self, client):
        # this email was never registered so the DB lookup returns nothing
        # the BLL should still return 401, not 404 or anything else
        response = client.post(
            "/api/auth/login",
            json={"email": "ghost@nowhere.com", "password": "password123"},
        )
        assert response.status_code == 401

    def test_same_generic_error(self, client):
        # same message as wrong password - the user shouldn't be able to tell
        # whether the email exists or not just from the error
        response = client.post(
            "/api/auth/login",
            json={"email": "ghost@nowhere.com", "password": "password123"},
        )
        detail = response.json().get("detail", [])
        assert any("Incorrect email or password" in str(d) for d in detail)


# ------------------------------------------------------------------
# TC-AUTH-04: empty email
# ------------------------------------------------------------------

class TestTC_AUTH_04:

    def test_status_code(self, client):
        # empty string for email - the BLL checks for this before doing anything else
        # should come back as 422 (validation error), not 401
        response = client.post(
            "/api/auth/login",
            json={"email": "", "password": "password123"},
        )
        assert response.status_code == 422

    def test_error_message(self, client):
        # check the actual error text says email is required
        response = client.post(
            "/api/auth/login",
            json={"email": "", "password": "password123"},
        )
        detail = response.json().get("detail", [])
        assert any("Email address is required" in str(d) for d in detail)

    def test_bll_directly(self, seeded_db):
        # call the internal validation function directly (white box)
        # bypasses the HTTP layer entirely - just checks the function returns the right error
        errors = _validate_credentials("", "password123")
        assert "Email address is required." in errors


# ------------------------------------------------------------------
# TC-AUTH-05: bad email format
# ------------------------------------------------------------------

class TestTC_AUTH_05:

    def test_status_code(self, client):
        # "not-an-email" has no @ so the regex check in auth_bll.py should reject it
        response = client.post(
            "/api/auth/login",
            json={"email": "not-an-email", "password": "password123"},
        )
        assert response.status_code == 422

    def test_error_message(self, client):
        # the error should mention the format is wrong
        response = client.post(
            "/api/auth/login",
            json={"email": "not-an-email", "password": "password123"},
        )
        detail = response.json().get("detail", [])
        assert any("not in a valid format" in str(d) for d in detail)

    def test_bll_directly(self):
        # same check but calling _validate_credentials directly
        errors = _validate_credentials("not-an-email", "password123")
        assert any("not in a valid format" in e for e in errors)

    @pytest.mark.parametrize("bad_email", [
        "missing_at_sign",
        "missing@",
        "@nodomain.com",
        "spaces in@email.com",
    ])
    def test_various_bad_formats(self, bad_email):
        # run the same check against a few different broken email patterns
        # parametrize runs this test once per value in the list above
        errors = _validate_credentials(bad_email, "password123")
        assert len(errors) > 0


# ------------------------------------------------------------------
# TC-AUTH-06: password too short
# ------------------------------------------------------------------

class TestTC_AUTH_06:

    def test_status_code(self, client):
        # "abc" is only 3 characters, minimum is 6
        # the BLL catches this before even touching the database
        response = client.post(
            "/api/auth/login",
            json={"email": "demo@realestate.com", "password": "abc"},
        )
        assert response.status_code == 422

    def test_error_message(self, client):
        # check the error mentions the 6 character minimum
        response = client.post(
            "/api/auth/login",
            json={"email": "demo@realestate.com", "password": "abc"},
        )
        detail = response.json().get("detail", [])
        assert any("at least 6 characters" in str(d) for d in detail)

    def test_exactly_6_chars_passes_validation(self, client):
        # "abc123" is exactly 6 characters so it should pass the length check
        # it will still fail login (wrong password) but the error should be 401 not 422
        # this is a boundary value test
        response = client.post(
            "/api/auth/login",
            json={"email": "demo@realestate.com", "password": "abc123"},
        )
        assert response.status_code == 401


# ------------------------------------------------------------------
# TC-AUTH-07: JWT has correct data
# ------------------------------------------------------------------

class TestTC_AUTH_07:

    def test_claims_present(self, client):
        # log in, grab the token, then decode it to inspect the payload
        # we use the same secret key the app uses to sign tokens
        # checking that sub (user id), email, name, and exp (expiry) are all there
        response = client.post(
            "/api/auth/login",
            json={"email": "demo@realestate.com", "password": "password123"},
        )
        token = response.json()["access_token"]
        secret = os.getenv("JWT_SECRET_KEY", "cs331-super-secret-key-change-in-production")
        payload = jwt.decode(token, secret, algorithms=["HS256"])

        assert payload.get("sub") == "user-001"
        assert payload.get("email") == "demo@realestate.com"
        assert payload.get("name") == "Demo Agent"
        assert "exp" in payload

    def test_expiry_is_in_future(self, client):
        # decode the token and check that exp is a timestamp in the future
        # the app sets tokens to expire after 8 hours so we check it's roughly that
        response = client.post(
            "/api/auth/login",
            json={"email": "demo@realestate.com", "password": "password123"},
        )
        token = response.json()["access_token"]
        secret = os.getenv("JWT_SECRET_KEY", "cs331-super-secret-key-change-in-production")
        payload = jwt.decode(token, secret, algorithms=["HS256"])

        now = int(time.time())
        assert payload["exp"] > now

        # allow 2 minutes of slack in case the test machine is slow
        expected = now + (8 * 3600)
        assert abs(payload["exp"] - expected) < 120


# ------------------------------------------------------------------
# TC-AUTH-08: no token = blocked
# ------------------------------------------------------------------

class TestTC_AUTH_08:

    def test_upload_blocked(self, client):
        # try to upload a file without sending any Authorization header
        # FastAPI's OAuth2PasswordBearer dependency should reject this with 401
        csv_content = b"price,bedrooms\n500000,3\n" * 15
        response = client.post(
            "/api/ingest/upload",
            files={"file": ("data.csv", io.BytesIO(csv_content), "text/csv")},
        )
        assert response.status_code == 401

    def test_predict_blocked(self, client):
        # same idea - predict endpoint also requires a token
        response = client.post(
            "/api/predict",
            json={
                "bedrooms": 3, "bathrooms": 2, "sqft_living": 1500,
                "sqft_lot": 5000, "floors": 1, "waterfront": 0,
                "view": 0, "condition": 3, "grade": 7,
                "yr_built": 1990, "zipcode": "98000",
            },
        )
        assert response.status_code == 401

    def test_explain_blocked(self, client):
        # explain endpoint - note the path is /api/explain/latest not /api/explain
        response = client.get("/api/explain/latest")
        assert response.status_code == 401

    def test_train_blocked(self, client):
        # training endpoint also protected
        response = client.post(
            "/api/train/start",
            json={"dataset_id": "some-id", "target_column": "price"},
        )
        assert response.status_code == 401

    def test_fake_token_blocked(self, client):
        # send a token that looks like a JWT but is completely made up
        # the server tries to verify the signature and fails, returns 401
        response = client.post(
            "/api/ingest/upload",
            headers={"Authorization": "Bearer this.is.not.a.valid.token"},
            files={"file": ("data.csv", io.BytesIO(b"a,b\n1,2\n"), "text/csv")},
        )
        assert response.status_code == 401
