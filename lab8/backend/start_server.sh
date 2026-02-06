#!/bin/bash
# Start the backend server with venv activated

echo "🔧 Activating virtual environment..."
source venv/bin/activate

echo "📊 Checking DATABASE_URL..."
python -c "
import os
from dotenv import load_dotenv
load_dotenv()
db_url = os.getenv('DATABASE_URL', 'NOT SET')
if 'postgresql' in db_url:
    print('✅ Using Supabase PostgreSQL')
elif 'sqlite' in db_url:
    print('⚠️  Using SQLite (local)')
else:
    print('❌ DATABASE_URL not configured')
print(f'   URL: {db_url[:60]}...')
"

echo ""
echo "🚀 Starting FastAPI server..."
echo "   Press Ctrl+C to stop"
echo ""

python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
