# Defect Report
**Assignment 9 – Q1b | CS 331 Software Engineering Lab**

---

## BUGS

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
| **Status** | Open |

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
| **Status** | Open |

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

| **Status** | Fixed |

---

## Summary

| Bug ID | Description | Severity | Status |
|--------|-------------|----------|--------|
| BUG-001 | Email regex allows consecutive dots | Low | Open |
| BUG-002 | Explain endpoint returns 404 without token | Medium | Open |
| BUG-003 | passlib/bcrypt crash on Python 3.13 | High | Fixed |

---

## Bug Statistics

- **Total Bugs Identified:** 3
- **Bugs Fixed:** 1 (33%)
- **Bugs Open:** 2 (67%)
- **High Severity Bugs:** 1 (Fixed)
- **Medium Severity Bugs:** 1 (Open)
- **Low Severity Bugs:** 1 (Open)

---

## Recommendations

### Immediate Actions
1. **Fix BUG-002** (Medium severity) - Update explain endpoint routing
2. **Fix BUG-001** (Low severity) - Improve email regex validation

### Preventive Actions
1. Add more comprehensive input validation tests
2. Implement automated security scanning
3. Add regression tests for fixed bugs

### Quality Improvements
1. Expand test coverage to other modules
2. Add performance testing
3. Implement continuous integration testing

---

## Root Cause Analysis

### Common Issues:
1. **Input Validation Gaps** - Regex patterns not comprehensive enough
2. **Endpoint Design Issues** - Inconsistent endpoint naming and routing
3. **Dependency Compatibility** - Library version conflicts

### Prevention Strategies:
1. Use established validation libraries (e.g., `email-validator`)
2. Follow consistent endpoint naming conventions
3. Pin dependency versions and test compatibility
4. Implement comprehensive test suites

---

## Verification

All bugs have been:
- ✅ Documented with clear steps to reproduce
- ✅ Assigned severity levels
- ✅ Provided with fix recommendations
- ✅ Tracked in this defect report

Fixed bugs have been:
- ✅ Verified with test execution
- ✅ Documented with fix implementation
- ✅ Confirmed working

---

**Defect Report Date:** April 26, 2026  
**Test Engineer:** Kiro AI  
**Status:** Complete with 2 open bugs
