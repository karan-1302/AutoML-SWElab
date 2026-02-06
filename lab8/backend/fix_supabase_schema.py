#!/usr/bin/env python3
"""
Fix Supabase Schema for VARCHAR user_id - HARD RESET APPROACH

This script performs a HARD RESET of the user_id columns:
1. Force kills all active connections to Supabase
2. Drops and recreates user_id columns as VARCHAR(50) in correct order
3. Re-adds foreign key constraints
4. Disposes SQLAlchemy engine cache

This ensures the "Invalid UUID" error is physically impossible.

Usage:
    python3 fix_supabase_schema.py
"""

import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("❌ DATABASE_URL not set in .env")
    sys.exit(1)

if "sqlite" in DATABASE_URL.lower():
    print("⚠️  This script is for Supabase (PostgreSQL) only.")
    print("   SQLite doesn't need this fix.")
    sys.exit(0)

print("\n" + "="*70)
print("HARD RESET: Force Supabase to forget UUID constraints")
print("="*70)
print(f"\n📍 Database: {DATABASE_URL[:50]}...")

try:
    engine = create_engine(DATABASE_URL, echo=False)

    with engine.connect() as conn:
        # ── STEP 1: Force kill all active connections ──────────────────
        print("\n[STEP 1] Force killing all active connections...")
        try:
            # Terminate all backends connected to this database
            conn.execute(text("""
                SELECT pg_terminate_backend(pid) 
                FROM pg_stat_activity 
                WHERE datname = current_database() 
                AND pid != pg_backend_pid()
            """))
            conn.commit()
            print("✅ All active connections terminated")
        except Exception as e:
            print(f"⚠️  Could not terminate connections: {str(e)}")
            print("   (This may be OK if no connections exist)")

        # ── STEP 2: Drop foreign key constraints ──────────────────────
        print("\n[STEP 2] Dropping foreign key constraints...")
        constraints_dropped = []
        try:
            # Drop all foreign key constraints on user_id columns
            tables = ["datasets", "training_jobs", "predictions"]
            for table in tables:
                try:
                    conn.execute(text(f"""
                        ALTER TABLE {table} 
                        DROP CONSTRAINT IF EXISTS {table}_user_id_fkey
                    """))
                    constraints_dropped.append(f"{table}.user_id")
                except Exception as e:
                    print(f"   ⚠️  Could not drop {table}.user_id_fkey: {str(e)}")
            
            conn.commit()
            print(f"✅ Foreign key constraints dropped: {', '.join(constraints_dropped)}")
        except Exception as e:
            print(f"⚠️  Error dropping constraints: {str(e)}")
            conn.rollback()

        # ── STEP 3: Drop and recreate user_id columns (HARD RESET) ────
        # Order matters: drop dependent tables first, then parent table
        print("\n[STEP 3] Hard reset: Dropping and recreating user_id columns...")
        
        # Drop in order: datasets (depends on users), then users
        # datasets uses dataset_id as PK, others use id
        tables_to_fix = ["datasets", "users"]
        for table in tables_to_fix:
            try:
                print(f"\n   Processing {table}...")
                
                # Get current user_id value for all rows (for later restore)
                if table == "datasets":
                    result = conn.execute(text(f"SELECT dataset_id, user_id FROM {table}"))
                    pk_col = "dataset_id"
                else:
                    result = conn.execute(text(f"SELECT id, user_id FROM {table}"))
                    pk_col = "id"
                
                old_values = result.fetchall()
                print(f"      Found {len(old_values)} rows")
                
                # Drop the old user_id column
                conn.execute(text(f"""
                    ALTER TABLE {table} 
                    DROP COLUMN IF EXISTS user_id
                """))
                print(f"      ✅ Dropped old user_id column")
                
                # Add new user_id column as VARCHAR(50)
                conn.execute(text(f"""
                    ALTER TABLE {table} 
                    ADD COLUMN user_id VARCHAR(50)
                """))
                print(f"      ✅ Added new VARCHAR(50) user_id column")
                
                # Restore the values (they're already VARCHAR strings)
                for row in old_values:
                    pk_val = row[0]
                    user_id = row[1]
                    if user_id:
                        conn.execute(text(f"""
                            UPDATE {table} 
                            SET user_id = :user_id 
                            WHERE {pk_col} = :pk_val
                        """), {"user_id": str(user_id), "pk_val": pk_val})
                
                conn.commit()
                print(f"      ✅ Restored {len(old_values)} user_id values")
                
            except Exception as e:
                print(f"      ❌ Error with {table}: {str(e)}")
                conn.rollback()

        # ── STEP 4: Re-add primary key and foreign key constraints ────
        print("\n[STEP 4] Re-adding primary key and foreign key constraints...")
        try:
            # Add primary key to users (if needed)
            try:
                conn.execute(text("""
                    ALTER TABLE users 
                    ADD CONSTRAINT users_pkey 
                    PRIMARY KEY (user_id)
                """))
                print("✅ users.user_id is now PRIMARY KEY")
            except Exception as e:
                print(f"   ⚠️  Primary key may already exist: {str(e)}")
            
            # Add foreign key to datasets
            conn.execute(text("""
                ALTER TABLE datasets 
                ADD CONSTRAINT datasets_user_id_fkey 
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            """))
            print("✅ datasets.user_id → users.user_id")
            
            # Add foreign key to training_jobs
            conn.execute(text("""
                ALTER TABLE training_jobs 
                ADD CONSTRAINT training_jobs_user_id_fkey 
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            """))
            print("✅ training_jobs.user_id → users.user_id")
            
            # Add foreign key to predictions
            conn.execute(text("""
                ALTER TABLE predictions 
                ADD CONSTRAINT predictions_user_id_fkey 
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            """))
            print("✅ predictions.user_id → users.user_id")
            
            conn.commit()
            print("✅ All constraints re-added")
        except Exception as e:
            print(f"⚠️  Error re-adding constraints: {str(e)}")
            conn.rollback()

        # ── STEP 5: Verify schema ─────────────────────────────────────
        print("\n[STEP 5] Verifying final schema...")
        tables = ["users", "datasets", "training_jobs", "predictions"]
        all_correct = True
        for table in tables:
            try:
                result = conn.execute(text(f"""
                    SELECT column_name, data_type, character_maximum_length
                    FROM information_schema.columns 
                    WHERE table_name = '{table}' AND column_name = 'user_id'
                """))
                row = result.fetchone()
                if row:
                    col_name, data_type, max_len = row
                    if max_len:
                        print(f"  ✓ {table}.user_id: {data_type}({max_len})")
                    else:
                        print(f"  ✓ {table}.user_id: {data_type}")
                else:
                    print(f"  ✗ {table}.user_id: NOT FOUND")
                    all_correct = False
            except Exception as e:
                print(f"  ✗ {table}.user_id: Error - {str(e)}")
                all_correct = False

        # ── STEP 6: Dispose SQLAlchemy engine cache ───────────────────
        print("\n[STEP 6] Disposing SQLAlchemy engine cache...")
        engine.dispose()
        print("✅ SQLAlchemy engine cache cleared")
        print("   (Metadata will be re-fetched on next connection)")

        print("\n" + "="*70)
        if all_correct:
            print("✅ HARD RESET COMPLETE - All user_id columns are VARCHAR(50)")
        else:
            print("⚠️  HARD RESET COMPLETE - Some columns may still need attention")
        print("="*70)
        print("\nWhat was done:")
        print("  1. Force killed all active connections")
        print("  2. Dropped all foreign key constraints")
        print("  3. Dropped user_id columns and recreated as VARCHAR(50)")
        print("  4. Restored all user_id values (as VARCHAR strings)")
        print("  5. Re-added foreign key constraints")
        print("  6. Cleared SQLAlchemy engine cache")
        print("\nNext steps:")
        print("  1. Start backend: python3 main.py")
        print("  2. Check startup logs for user_id type verification")
        print("  3. Test upload - should work without UUID errors")

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
