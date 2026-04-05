# Real Estate AutoML - Assignment 8

## Overview
This directory contains the completed Assignment 8 for CS 331 (Software Engineering Lab).

The assignment covers two main parts:
1. **Part A:** Implementation of a Data Access Layer (DAL) using SQLAlchemy and SQLite to replace the previous in-memory system. (20 marks)
2. **Part B:** Implementation of White Box and Black Box Testing suites to ensure system correctness. (20 marks)

## Architecture Details

- **Presentation Layer**: Thin HTTP routers (`routers/`)
- **Business Logic Layer (BLL)**: Validates input and orchestrates operations (`bll/`)
- **Data Access Layer (DAL)**: Database engines, ORM models, and repositories (`dal/`)
  - **Models**: `users`, `datasets`, `training_jobs`, `predictions` (using SQLite `automl.db`)
  - **Repositories**: Standardized CRUD operations to decouple BLL from ORM implementation.
- **Runtime Cache**: `utils/store.py` manages ML specific non-serializable objects (Pandas DataFrames, Scikit-Learn Pipelines).

## Setup & Execution

### 1. Installation
Activate your virtual environment and install the required dependencies:
```bash
cd backend
pip install -r requirements.txt
```

### 2. Run the Application
Start the FastAPI server. The database (and seed data) will be automatically initialized on startup.
```bash
python main.py
```
> **Demo Credentials:** 
> Email: `demo@realestate.com`
> Password: `password123`

### 3. Run the Test Suites (Part B)
Navigate to the `backend/` directory and execute `pytest`:

**Run All Tests:**
```bash
python -m pytest tests/ -v
```

**Run White Box Tests Only:**
```bash
python -m pytest tests/test_whitebox.py -v
```

**Run Black Box Tests Only:**
```bash
python -m pytest tests/test_blackbox.py -v
```
