#!/usr/bin/env python
"""
Add dataset_id, model_name, target_column columns to predictions table.
This is needed because the database is PostgreSQL (Supabase), not SQLite.
"""

import os
from sqlalchemy import create_engine, text

def add_prediction_metadata_columns():
    """Add metadata columns to predictions table."""
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("DATABASE_URL not set")
        return False
    
    engine = create_engine(db_url)
    
    with engine.connect() as conn:
        # Check if columns already exist
        check_cols = """
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'predictions' 
        AND column_name IN ('dataset_id', 'model_name', 'target_column')
        """
        result = conn.execute(text(check_cols))
        existing_cols = [row[0] for row in result.fetchall()]
        
        print(f"Existing columns in predictions table: {existing_cols}")
        
        # Add columns if they don't exist
        if 'dataset_id' not in existing_cols:
            print("Adding dataset_id column...")
            conn.execute(text("ALTER TABLE predictions ADD COLUMN dataset_id VARCHAR(50)"))
        
        if 'model_name' not in existing_cols:
            print("Adding model_name column...")
            conn.execute(text("ALTER TABLE predictions ADD COLUMN model_name VARCHAR(100)"))
        
        if 'target_column' not in existing_cols:
            print("Adding target_column column...")
            conn.execute(text("ALTER TABLE predictions ADD COLUMN target_column VARCHAR(255)"))
        
        conn.commit()
        
        # Verify columns were added
        result = conn.execute(text(check_cols))
        final_cols = [row[0] for row in result.fetchall()]
        print(f"Final columns in predictions table: {final_cols}")
        
        if 'dataset_id' in final_cols and 'model_name' in final_cols and 'target_column' in final_cols:
            print("✅ All columns added successfully!")
            return True
        else:
            print("❌ Some columns are still missing")
            return False

if __name__ == "__main__":
    success = add_prediction_metadata_columns()
    exit(0 if success else 1)
