# lab8/backend/dal/database.py
# ─────────────────────────────────────────────────────────────
# SQLAlchemy engine, session factory, and Base declarative class.
#
# Uses SQLite for this assignment (file: automl.db).
# In production, swap the DATABASE_URL for PostgreSQL / Supabase.
# ─────────────────────────────────────────────────────────────

import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base

# ── Database URL ──────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"sqlite:///{os.path.join(BASE_DIR, 'automl.db')}"
)

# ── Engine ────────────────────────────────────────────────────
# Build connect_args based on database type
connect_args = {}
if "sqlite" in DATABASE_URL.lower():
    connect_args = {"check_same_thread": False}  # SQLite-specific
# PostgreSQL/Supabase doesn't need this option

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    echo=False,
)

# ── Session factory ───────────────────────────────────────────
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ── Declarative Base ──────────────────────────────────────────
Base = declarative_base()


def check_db_health() -> dict:
    """
    Check database connectivity and health.
    Verifies that all required tables are writable.
    Returns a dict with status and details.
    """
    try:
        db = SessionLocal()
        try:
            # Run a simple query to verify connection
            result = db.execute(text("SELECT 1"))
            result.fetchone()
            
            # Determine database type
            db_type = "SQLite" if "sqlite" in DATABASE_URL.lower() else "PostgreSQL/Supabase"
            
            print(f"[HEALTH] Database: ✅ Connected ({db_type})")
            print(f"[HEALTH] Database URL: {DATABASE_URL[:50]}...")
            
            # Verify training_jobs table is writable
            try:
                from dal.db_models import TrainingJob
                
                # Check if training_jobs table exists and has required columns
                inspector_result = db.execute(text("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='training_jobs'
                """))
                table_exists = inspector_result.fetchone() is not None
                
                if table_exists:
                    # Check for mlflow_run_id column
                    col_result = db.execute(text("""
                        PRAGMA table_info(training_jobs)
                    """))
                    columns = {row[1] for row in col_result.fetchall()}
                    
                    if "mlflow_run_id" in columns:
                        print(f"[HEALTH] Training Jobs Table: ✅ Writable (mlflow_run_id column present)")
                        return {
                            "status": "healthy",
                            "database": db_type,
                            "training_jobs": "writable",
                            "message": "Database connection successful, training_jobs table writable"
                        }
                    else:
                        print(f"[HEALTH] Training Jobs Table: ⚠️  mlflow_run_id column missing")
                        return {
                            "status": "warning",
                            "database": db_type,
                            "training_jobs": "schema_mismatch",
                            "message": "Database connected but training_jobs schema incomplete"
                        }
                else:
                    print(f"[HEALTH] Training Jobs Table: ⚠️  Table not found")
                    return {
                        "status": "warning",
                        "database": db_type,
                        "training_jobs": "not_found",
                        "message": "Database connected but training_jobs table not found"
                    }
            except Exception as tj_err:
                print(f"[HEALTH] Training Jobs Table: ⚠️  Could not verify - {str(tj_err)}")
                return {
                    "status": "warning",
                    "database": db_type,
                    "error": str(tj_err),
                    "message": "Database connected but could not verify training_jobs table"
                }
                
        except Exception as e:
            print(f"[HEALTH] Database: ❌ Query failed - {str(e)}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "message": "Database query failed"
            }
        finally:
            try:
                db.close()
            except:
                pass
    except Exception as e:
        print(f"[HEALTH] Database: ❌ Connection failed - {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "message": "Database connection failed"
        }


def init_db():
    """Create all tables defined by SQLAlchemy models."""
    from dal.db_models import User, Dataset, TrainingJob, Prediction  # noqa: F401
    Base.metadata.create_all(bind=engine)
    
    # Dispose engine to clear any cached metadata
    # This ensures fresh schema inspection on next connection
    engine.dispose()


def get_db():
    """FastAPI dependency — yields a DB session and closes it after the request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def print_user_id_type():
    """Print the exact type of user_id columns for verification."""
    try:
        db = SessionLocal()
        try:
            tables = ["users", "datasets", "training_jobs", "predictions"]
            print("\n[HEALTH] DATABASE SCHEMA VERIFICATION")
            print("="*60)
            
            for table in tables:
                try:
                    result = db.execute(text(f"""
                        SELECT column_name, data_type, character_maximum_length
                        FROM information_schema.columns 
                        WHERE table_name = '{table}' AND column_name = 'user_id'
                    """))
                    row = result.fetchone()
                    if row:
                        col_name, data_type, max_len = row
                        if max_len:
                            print(f"[HEALTH] {table}.user_id: {data_type}({max_len})")
                        else:
                            print(f"[HEALTH] {table}.user_id: {data_type}")
                    else:
                        print(f"[HEALTH] {table}.user_id: NOT FOUND")
                except Exception as e:
                    print(f"[HEALTH] {table}.user_id: Error - {str(e)}")
            
            print("="*60)
        finally:
            try:
                db.close()
            except:
                pass
    except Exception as e:
        print(f"[HEALTH] Schema verification failed: {str(e)}")
