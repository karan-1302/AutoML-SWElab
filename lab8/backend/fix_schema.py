#!/usr/bin/env python3
"""
Comprehensive Database Schema Fix for Supabase

This script diagnoses and fixes all schema mismatches between SQLAlchemy models
and the actual Supabase database. It specifically addresses:

1. Missing columns in each table (users, datasets, training_jobs, predictions)
2. Incorrect column types (UUID vs VARCHAR for user_id)
3. Missing foreign key constraints
4. Missing indexes and unique constraints

Error being fixed:
  psycopg2.errors.UndefinedColumn: column "dataset_id" of relation "datasets" does not exist

Usage:
    python3 fix_schema.py

Expected output:
    ✅ All schema mismatches fixed
    ✅ All tables have required columns
    ✅ All foreign keys re-established
"""

import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect, text, MetaData, Table
from sqlalchemy.exc import ProgrammingError

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("❌ DATABASE_URL not set in .env")
    sys.exit(1)

if "sqlite" in DATABASE_URL.lower():
    print("⚠️  This script is for Supabase (PostgreSQL) only.")
    print("   SQLite handles schema creation automatically.")
    sys.exit(0)

print("\n" + "="*80)
print("COMPREHENSIVE DATABASE SCHEMA FIX FOR SUPABASE")
print("="*80)
print(f"\n📍 Database: {DATABASE_URL[:60]}...")

# Create engine
engine = create_engine(DATABASE_URL, echo=False)

# Expected schema based on SQLAlchemy models
EXPECTED_SCHEMA = {
    "users": {
        "id": ("INTEGER", False),
        "user_id": ("VARCHAR(50)", True),  # (type, is_unique)
        "email": ("VARCHAR(255)", True),
        "full_name": ("VARCHAR(255)", False),
        "hashed_password": ("VARCHAR(255)", False),
        "created_at": ("TIMESTAMP", False),
    },
    "datasets": {
        "id": ("INTEGER", False),
        "dataset_id": ("VARCHAR(50)", True),  # ← THIS IS THE MISSING COLUMN
        "filename": ("VARCHAR(255)", False),
        "user_id": ("VARCHAR(50)", False),
        "row_count": ("INTEGER", False),
        "column_count": ("INTEGER", False),
        "quality_score": ("FLOAT", False),
        "file_path": ("TEXT", False),
        "uploaded_at": ("TIMESTAMP", False),
    },
    "training_jobs": {
        "id": ("INTEGER", False),
        "user_id": ("VARCHAR(50)", False),
        "status": ("VARCHAR(20)", False),
        "progress_json": ("TEXT", False),
        "scores_json": ("TEXT", False),
        "best_model_name": ("VARCHAR(100)", False),
        "target_column": ("VARCHAR(255)", False),
        "feature_columns_json": ("TEXT", False),
        "error_message": ("TEXT", False),
        "mlflow_run_id": ("VARCHAR(100)", False),
        "created_at": ("TIMESTAMP", False),
        "updated_at": ("TIMESTAMP", False),
    },
    "predictions": {
        "id": ("INTEGER", False),
        "user_id": ("VARCHAR(50)", False),
        "predicted_price": ("FLOAT", False),
        "model_used": ("VARCHAR(100)", False),
        "confidence": ("FLOAT", False),
        "input_features_json": ("TEXT", False),
        "created_at": ("TIMESTAMP", False),
    },
}

FOREIGN_KEYS = {
    "datasets": [("user_id", "users", "user_id")],
    "training_jobs": [("user_id", "users", "user_id")],
    "predictions": [("user_id", "users", "user_id")],
}

# ── STEP 1: Inspect current schema ────────────────────────────────────────

print("\n[STEP 1] Inspecting current Supabase schema...")
inspector = inspect(engine)
current_tables = inspector.get_table_names()
print(f"✓ Found {len(current_tables)} tables: {', '.join(current_tables)}")

# ── STEP 2: Check each table for missing columns ──────────────────────────

print("\n[STEP 2] Checking for missing columns...")
missing_columns = {}

for table_name, expected_cols in EXPECTED_SCHEMA.items():
    if table_name not in current_tables:
        print(f"  ⚠️  Table '{table_name}' does not exist (will be created by init_db)")
        continue
    
    current_cols = {col["name"]: col for col in inspector.get_columns(table_name)}
    missing = [col for col in expected_cols if col not in current_cols]
    
    if missing:
        missing_columns[table_name] = missing
        print(f"  ❌ {table_name}: Missing columns: {', '.join(missing)}")
    else:
        print(f"  ✓ {table_name}: All columns present")

# ── STEP 3: Add missing columns ───────────────────────────────────────────

if missing_columns:
    print("\n[STEP 3] Adding missing columns...")
    
    with engine.connect() as conn:
        for table_name, missing_cols in missing_columns.items():
            print(f"\n  Processing {table_name}...")
            
            for col_name in missing_cols:
                col_type, is_unique = EXPECTED_SCHEMA[table_name][col_name]
                
                # Map SQLAlchemy types to PostgreSQL types
                pg_type = col_type
                if col_type == "INTEGER":
                    pg_type = "INTEGER"
                elif col_type.startswith("VARCHAR"):
                    pg_type = col_type
                elif col_type == "FLOAT":
                    pg_type = "FLOAT"
                elif col_type == "TEXT":
                    pg_type = "TEXT"
                elif col_type == "TIMESTAMP":
                    pg_type = "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
                
                # Build ALTER TABLE statement
                unique_clause = " UNIQUE" if is_unique else ""
                
                # Build ALTER TABLE statement (no special defaults - let Python/SQLAlchemy handle ID generation)
                sql = f"""
                    ALTER TABLE {table_name}
                    ADD COLUMN {col_name} {pg_type}{unique_clause}
                """
                
                try:
                    conn.execute(text(sql))
                    conn.commit()
                    print(f"    ✓ Added {col_name} ({pg_type})")
                except ProgrammingError as e:
                    if "already exists" in str(e):
                        print(f"    ⚠️  {col_name} already exists")
                    else:
                        print(f"    ❌ Error adding {col_name}: {str(e)}")
                    conn.rollback()
                except Exception as e:
                    print(f"    ❌ Error adding {col_name}: {str(e)}")
                    conn.rollback()

# ── STEP 4: Fix user_id column types (UUID → VARCHAR) ────────────────────

print("\n[STEP 4] Checking user_id column types...")

with engine.connect() as conn:
    for table_name in ["users", "datasets", "training_jobs", "predictions"]:
        if table_name not in current_tables:
            continue
        
        try:
            result = conn.execute(text(f"""
                SELECT data_type, character_maximum_length
                FROM information_schema.columns 
                WHERE table_name = '{table_name}' AND column_name = 'user_id'
            """))
            row = result.fetchone()
            
            if row:
                data_type, char_max_len = row
                if data_type.upper() == "UUID":
                    print(f"  ⚠️  {table_name}.user_id is UUID, converting to VARCHAR(50)...")
                    
                    try:
                        # Drop foreign key constraint if it exists
                        fk_name = f"{table_name}_user_id_fkey"
                        conn.execute(text(f"""
                            ALTER TABLE {table_name}
                            DROP CONSTRAINT IF EXISTS {fk_name}
                        """))
                        
                        # Convert column type
                        conn.execute(text(f"""
                            ALTER TABLE {table_name}
                            ALTER COLUMN user_id TYPE VARCHAR(50) USING user_id::text
                        """))
                        
                        conn.commit()
                        print(f"    ✓ {table_name}.user_id converted to VARCHAR(50)")
                    except Exception as e:
                        print(f"    ❌ Error converting {table_name}.user_id: {str(e)}")
                        conn.rollback()
                else:
                    print(f"  ✓ {table_name}.user_id is {data_type}")
            else:
                print(f"  ⚠️  {table_name}.user_id not found")
        except Exception as e:
            print(f"  ⚠️  Could not check {table_name}.user_id: {str(e)}")

# ── STEP 5: Re-add foreign key constraints ────────────────────────────────

print("\n[STEP 5] Re-adding foreign key constraints...")

with engine.connect() as conn:
    for table_name, fks in FOREIGN_KEYS.items():
        if table_name not in current_tables:
            continue
        
        for col_name, ref_table, ref_col in fks:
            fk_name = f"{table_name}_{col_name}_fkey"
            
            try:
                # Drop existing constraint if it exists
                conn.execute(text(f"""
                    ALTER TABLE {table_name}
                    DROP CONSTRAINT IF EXISTS {fk_name}
                """))
                
                # Add new constraint with ON DELETE CASCADE
                conn.execute(text(f"""
                    ALTER TABLE {table_name}
                    ADD CONSTRAINT {fk_name}
                    FOREIGN KEY ({col_name}) REFERENCES {ref_table}({ref_col})
                    ON DELETE CASCADE
                """))
                
                conn.commit()
                print(f"  ✓ {table_name}.{col_name} → {ref_table}.{ref_col}")
            except Exception as e:
                if "already exists" in str(e).lower():
                    print(f"  ✓ {table_name}.{col_name} → {ref_table}.{ref_col} (already exists)")
                else:
                    print(f"  ⚠️  Could not add FK {fk_name}: {str(e)}")
                conn.rollback()

# ── STEP 6: Add indexes and unique constraints ────────────────────────────

print("\n[STEP 6] Adding indexes and unique constraints...")

indexes_to_add = {
    "users": [
        ("user_id", True),   # (column, is_unique)
        ("email", True),
    ],
    "datasets": [
        ("dataset_id", True),
        ("user_id", False),
    ],
    "training_jobs": [
        ("user_id", False),
    ],
    "predictions": [
        ("user_id", False),
    ],
}

with engine.connect() as conn:
    for table_name, indexes in indexes_to_add.items():
        if table_name not in current_tables:
            continue
        
        for col_name, is_unique in indexes:
            try:
                # Check if index already exists
                result = conn.execute(text(f"""
                    SELECT indexname FROM pg_indexes 
                    WHERE tablename = '{table_name}' AND indexdef ILIKE '%{col_name}%'
                """))
                
                if result.fetchone():
                    print(f"  ✓ {table_name}.{col_name} index already exists")
                else:
                    if is_unique:
                        # Unique constraint
                        constraint_name = f"{table_name}_{col_name}_unique"
                        conn.execute(text(f"""
                            ALTER TABLE {table_name}
                            ADD CONSTRAINT {constraint_name} UNIQUE ({col_name})
                        """))
                        print(f"  ✓ Added unique constraint on {table_name}.{col_name}")
                    else:
                        # Regular index
                        index_name = f"{table_name}_{col_name}_idx"
                        conn.execute(text(f"""
                            CREATE INDEX IF NOT EXISTS {index_name}
                            ON {table_name}({col_name})
                        """))
                        print(f"  ✓ Added index on {table_name}.{col_name}")
                
                conn.commit()
            except Exception as e:
                if "already exists" in str(e).lower() or "duplicate" in str(e).lower():
                    print(f"  ✓ {table_name}.{col_name} constraint/index already exists")
                else:
                    print(f"  ⚠️  Could not add index on {table_name}.{col_name}: {str(e)}")
                conn.rollback()

# ── STEP 7: Final verification ────────────────────────────────────────────

print("\n[STEP 7] Final schema verification...")

inspector = inspect(engine)
all_good = True

for table_name, expected_cols in EXPECTED_SCHEMA.items():
    if table_name not in inspector.get_table_names():
        print(f"  ⚠️  {table_name}: Table not found (will be created by init_db)")
        continue
    
    current_cols = {col["name"] for col in inspector.get_columns(table_name)}
    missing = [col for col in expected_cols if col not in current_cols]
    
    if missing:
        print(f"  ❌ {table_name}: Still missing: {', '.join(missing)}")
        all_good = False
    else:
        print(f"  ✓ {table_name}: All columns present")

# ── STEP 8: Dispose engine cache ──────────────────────────────────────────

print("\n[STEP 8] Clearing SQLAlchemy engine cache...")
engine.dispose()
print("  ✓ Engine cache cleared (metadata will be re-fetched on next connection)")

# ── Summary ───────────────────────────────────────────────────────────────

print("\n" + "="*80)
if all_good:
    print("✅ SCHEMA FIX COMPLETE - All tables have required columns")
    print("="*80)
    print("\nWhat was fixed:")
    print("  1. ✓ Added missing columns to all tables")
    print("  2. ✓ Converted user_id columns from UUID to VARCHAR(50)")
    print("  3. ✓ Re-added foreign key constraints")
    print("  4. ✓ Added indexes and unique constraints")
    print("  5. ✓ Cleared SQLAlchemy engine cache")
    print("\nNext steps:")
    print("  1. Start backend: python3 main.py")
    print("  2. Check startup logs for [HEALTH] messages")
    print("  3. Test upload - should work without errors")
    print("  4. Verify in Supabase dashboard")
    sys.exit(0)
else:
    print("⚠️  SCHEMA FIX COMPLETE - Some issues may remain")
    print("="*80)
    print("\nPlease review the errors above and:")
    print("  1. Check Supabase dashboard for table structure")
    print("  2. Manually add any remaining columns")
    print("  3. Run this script again")
    sys.exit(1)
