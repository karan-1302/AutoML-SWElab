# Assignment 9 – CS 331 Software Engineering Lab

This folder has everything for Assignment 9.

- `test_plan.md` – Q1a: test plan
- `test_cases.md` – Q1b: 8 test cases for the auth module
- `test_execution_log.txt` – Q2a: output from running the tests
- `defect_report.md` – Q2b: 3 bugs found during testing
- `backend/` – the actual test code (copied from lab8 with fixes)

## Running the tests

```bash
cd backend
pip install -r requirements.txt
python -m pytest tests/test_assignment9.py -v
```
