#!/usr/bin/env python3
"""
Database Schema Migration Script - Datasets Table

Adds the file_path column to the datasets table in Supabase to support
storing the absolute path to uploaded CSV files.

Usage:
    python3 migrate_datasets_schema.py
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
print("DATABASE SCHEMA MIGRATION - DATASETS TABLE")
print("="*70)

# Create engine
engine = create_engine(DATABASE_URL, echo=False)

# Get inspector to check existing columns
inspector = inspect(engine)

print(f"\n📍 Database: {DATABASE_URL[:50]}...")

# ── Migration: Add file_path to datasets table ────────────────

print("\n[MIGRATION] Checking datasets table...")
datasets_columns = [col["name"] for col in inspector.get_columns("datasets")]
print(f"Existing columns: {datasets_columns}")

if "file_path" not in datasets_columns:
    print("⚠️  file_path column missing, adding...")
    try:
        with engine.connect() as conn:
            # Add file_path column as TEXT NULL
            conn.execute(text("""
                ALTER TABLE datasets 
                ADD COLUMN file_path TEXT NULL
            """))
            conn.commit()
        print("✅ file_path column added to datasets table")
    except Exception as e:
        print(f"❌ Error adding file_path: {str(e)}")
        if "already exists" in str(e).lower():
            print("   (Column may already exist)")
else:
    print("✅ file_path column already exists")

# ── Verification ──────────────────────────────────────────────

print("\n[VERIFICATION] Checking final schema...")

# Refresh inspector
inspector = inspect(engine)

datasets_columns = [col["name"] for col in inspector.get_columns("datasets")]

print(f"\ndatasets table columns: {datasets_columns}")

if "file_path" in datasets_columns:
    print("\n✅ MIGRATION COMPLETE - file_path column present")
    sys.exit(0)
else:
    print("\n❌ MIGRATION INCOMPLETE - file_path column still missing")
    sys.exit(1)
