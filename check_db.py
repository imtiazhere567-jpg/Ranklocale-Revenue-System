import os
import psycopg2
from dotenv import load_dotenv
import sys

# 1. Load your credentials
load_dotenv()
from models import get_db

def check_everything():
    print("--- Supabase Diagnostic Tool ---")
    
    print("Attempting to connect...")

    try:
        # 2. Test Connection
        conn = get_db()
        print("Connection Successful!")
        
        # 3. Check for tables
        with conn.cursor() as cur:
            cur.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """)
            tables = [row['table_name'] for row in cur.fetchall()]
            
            if not tables:
                print("Supabase is EMPTY (No tables found).")
            else:
                print(f"Found {len(tables)} tables: {', '.join(tables)}")

        # 4. Try to Initialize Tables if missing
        if "contracts" not in tables:
            print("Attempting to create tables (init_db)...")
            sys.path.append(os.getcwd())
            from models import init_db
            try:
                init_db()
                print("Tables initialized successfully!")
            except Exception as e:
                print(f"Failed to initialize tables: {e}")
        
        conn.close()

    except Exception as e:
        print(f"CONNECTION ERROR: {e}")

if __name__ == "__main__":
    check_everything()
