# lab8/backend/utils/health_check.py
# ─────────────────────────────────────────────────────────────
# System Health Check Module
#
# Validates connectivity to external services:
# - Database (Supabase/SQLite)
# - Environment variables
# ─────────────────────────────────────────────────────────────

import os
from typing import Dict, List


def check_environment_variables() -> Dict[str, any]:
    """
    Validate that all required environment variables are set.
    Returns a dict with status and details.
    """
    print("\n" + "="*60)
    print("[HEALTH] ENVIRONMENT VALIDATION")
    print("="*60)
    
    required_vars = {
        "DATABASE_URL": "Database connection string",
        "JWT_SECRET_KEY": "JWT secret key (optional, has default)",
    }
    
    missing = []
    present = []
    
    for var_name, description in required_vars.items():
        value = os.getenv(var_name)
        if value:
            # Mask sensitive values
            if "TOKEN" in var_name or "SECRET" in var_name or "PASSWORD" in var_name:
                masked = value[:8] + "..." if len(value) > 8 else "***"
            else:
                masked = value[:40] + "..." if len(value) > 40 else value
            
            print(f"[HEALTH] ✅ {var_name}: {masked}")
            present.append(var_name)
        else:
            if var_name == "JWT_SECRET_KEY":
                print(f"[HEALTH] ⚠️  {var_name}: Using default (not recommended for production)")
                present.append(var_name)
            else:
                print(f"[HEALTH] ❌ {var_name}: MISSING")
                missing.append(var_name)
    
    if missing:
        print(f"\n[HEALTH] ⚠️  WARNING: Missing environment variables: {', '.join(missing)}")
        return {
            "status": "warning",
            "missing": missing,
            "present": present,
            "message": f"Missing {len(missing)} required environment variables"
        }
    else:
        print(f"\n[HEALTH] ✅ All environment variables present")
        return {
            "status": "healthy",
            "present": present,
            "message": "All environment variables configured"
        }


def print_health_report():
    """
    Print a comprehensive health report during startup.
    """
    print("\n" + "="*60)
    print("[HEALTH] SYSTEM STARTUP HEALTH CHECK")
    print("="*60)
    
    # Check environment variables
    env_status = check_environment_variables()
    
    # Check database (imported here to avoid circular imports)
    try:
        from dal.database import check_db_health
        db_status = check_db_health()
    except Exception as e:
        print(f"[HEALTH] Database: ❌ Import failed - {str(e)}")
        db_status = {"status": "unhealthy", "error": str(e)}
    
    # Print summary
    print("\n" + "="*60)
    print("[HEALTH] SUMMARY")
    print("="*60)
    print(f"[HEALTH] Environment: {env_status['status'].upper()}")
    print(f"[HEALTH] Database: {db_status['status'].upper()}")
    
    # Overall status
    statuses = [env_status['status'], db_status['status']]
    if 'unhealthy' in statuses:
        overall = "❌ UNHEALTHY"
    elif 'warning' in statuses:
        overall = "⚠️  WARNING"
    else:
        overall = "✅ HEALTHY"
    
    print(f"\n[HEALTH] OVERALL STATUS: {overall}")
    print("="*60 + "\n")
    
    return {
        "environment": env_status,
        "database": db_status,
        "overall": overall
    }
