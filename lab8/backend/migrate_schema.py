#!/usr/bin/env python3
"""
Database Schema Migration Script

Adds missing columns to Supabase tables to match the SQLAlchemy models.

This script:
1. Adds user_id column to users table (if missing)
2. Adds created_at column to users table (if missing)
3. Adds mlflow_run_id column to training_jobs table (if missing)
4. Fixes user_id column type in training_jobs (UUID → VARCHAR)

Usage:
    python3 migrate_schema.py
"""

import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect, text

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("❌ DATABASE_URL not set in .env")
    sys.exit(1)

print("\n" + "="*70)
print("DATABASE SCHEMA MIGRATION")
print("="*70)

# Create engine
engine = create_engine(DATABASE_URL, echo=False)

# Get inspector to check existing columns
inspector = inspect(engine)

print(f"\n📍 Database: {DATABASE_URL[:50]}...")

# ── Migration 1: Add user_id to users table ──────────────────────────────

print("\n[MIGRATION 1] Checking users table...")
users_columns = [col["name"] for col in inspector.get_columns("users")]
print(f"Existing columns: {users_columns}")

if "user_id" not in users_columns:
    print("⚠️  user_id column missing, adding...")
    try:
        with engine.connect() as conn:
            # Add user_id column as VARCHAR(50) UNIQUE NOT NULL
            conn.execute(text("""
                ALTER TABLE users 
                ADD COLUMN user_id VARCHAR(50) UNIQUE NOT NULL DEFAULT gen_random_uuid()::text
            """))
            conn.commit()
        print("✅ user_id column added to users table")
    except Exception as e:
        print(f"❌ Error adding user_id: {str(e)}")
        if "already exists" in str(e).lower():
            print("   (Column may already exist)")
else:
    print("✅ user_id column already exists")

# ── Migration 2: Add created_at to users table ────────────────────────────

print("\n[MIGRATION 2] Checking users table for created_at...")
users_columns = [col["name"] for col in inspector.get_columns("users")]

if "created_at" not in users_columns:
    print("⚠️  created_at column missing, adding...")
    try:
        with engine.connect() as conn:
            # Add created_at column as TIMESTAMP
            conn.execute(text("""
                ALTER TABLE users 
                ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            """))
            conn.commit()
        print("✅ created_at column added to users table")
    except Exception as e:
        print(f"❌ Error adding created_at: {str(e)}")
        if "already exists" in str(e).lower():
            print("   (Column may already exist)")
else:
    print("✅ created_at column already exists")

# ── Migration 3: Add mlflow_run_id to training_jobs table ────────────────

print("\n[MIGRATION 3] Checking training_jobs table...")
training_jobs_columns = [col["name"] for col in inspector.get_columns("training_jobs")]
print(f"Existing columns: {training_jobs_columns}")

if "mlflow_run_id" not in training_jobs_columns:
    print("⚠️  mlflow_run_id column missing, adding...")
    try:
        with engine.connect() as conn:
            # Add mlflow_run_id column as VARCHAR(100) NULL
            conn.execute(text("""
                ALTER TABLE training_jobs 
                ADD COLUMN mlflow_run_id VARCHAR(100) NULL
            """))
            conn.commit()
        print("✅ mlflow_run_id column added to training_jobs table")
    except Exception as e:
        print(f"❌ Error adding mlflow_run_id: {str(e)}")
        if "already exists" in str(e).lower():
            print("   (Column may already exist)")
else:
    print("✅ mlflow_run_id column already exists")

# ── Migration 4: Fix user_id type in training_jobs (UUID → VARCHAR) ──────

print("\n[MIGRATION 4] Checking training_jobs.user_id type...")
try:
    with engine.connect() as conn:
        # Check the column type
        result = conn.execute(text("""
            SELECT data_type FROM information_schema.columns 
            WHERE table_name = 'training_jobs' AND column_name = 'user_id'
        """))
        col_type = result.scalar()
        print(f"Current user_id type: {col_type}")
        
        if col_type and "uuid" in col_type.lower():
            print("⚠️  user_id is UUID type, converting to VARCHAR...")
            try:
                # Drop the foreign key constraint first
                conn.execute(text("""
                    ALTER TABLE training_jobs 
                    DROP CONSTRAINT IF EXISTS training_jobs_user_id_fkey
                """))
                
                # Convert the column type
                conn.execute(text("""
                    ALTER TABLE training_jobs 
                    ALTER COLUMN user_id TYPE VARCHAR(50) USING user_id::text
                """))
                
                # Re-add the foreign key constraint
                conn.execute(text("""
                    ALTER TABLE training_jobs 
                    ADD CONSTRAINT training_jobs_user_id_fkey 
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                """))
                
                conn.commit()
                print("✅ user_id column converted to VARCHAR(50)")
            except Exception as convert_err:
                print(f"⚠️  Could not convert user_id type: {str(convert_err)}")
                print("   This may be OK if the column is already VARCHAR")
        else:
            print("✅ user_id is already VARCHAR type")
except Exception as e:
    print(f"⚠️  Could not check user_id type: {str(e)}")

# ── Verification ──────────────────────────────────────────────────────────

print("\n[VERIFICATION] Checking final schema...")

# Refresh inspector
inspector = inspect(engine)

users_columns = [col["name"] for col in inspector.get_columns("users")]
training_jobs_columns = [col["name"] for col in inspector.get_columns("training_jobs")]

print(f"\nusers table columns: {users_columns}")
print(f"training_jobs table columns: {training_jobs_columns}")

required_user_cols = ["user_id", "created_at"]
required_job_cols = ["mlflow_run_id"]

missing_user = [c for c in required_user_cols if c not in users_columns]
missing_job = [c for c in required_job_cols if c not in training_jobs_columns]

if not missing_user and not missing_job:
    print("\n✅ MIGRATION COMPLETE - All required columns present")
    sys.exit(0)
else:
    if missing_user:
        print(f"\n❌ Missing user columns: {missing_user}")
    if missing_job:
        print(f"\n❌ Missing training_jobs columns: {missing_job}")
    sys.exit(1)
