"""
Ranklocale Revenue System — Database Models & Helpers (PostgreSQL version)
Migrated from SQLite to support Vercel + Supabase.
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

# Connection parameters (preferred for stability)
DBHOST = os.getenv("DBHOST")
DBUSER = os.getenv("DBUSER")
DBPASS = os.getenv("DBPASS")
DBNAME = os.getenv("DBNAME")
DBPORT = os.getenv("DBPORT", "5432")
DATABASE_URL = os.getenv("DATABASE_URL")

def get_db():
    """Get a database connection with dict-like cursor (resilient version)."""
    try:
        if DBHOST and DBUSER and DBPASS and DBNAME:
            # Connect using individual components (avoid URI parsing bugs with @ symbols)
            conn = psycopg2.connect(
                host=DBHOST,
                user=DBUSER,
                password=DBPASS,
                dbname=DBNAME,
                port=DBPORT,
                cursor_factory=RealDictCursor
            )
        elif DATABASE_URL:
            # Fallback to single string URI
            conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        else:
            raise ValueError("No database connection settings found (DBHOST, DBUSER, etc. or DATABASE_URL)!")
        return conn
    except Exception as e:
        print(f"Error connecting to database: {e}")
        raise

class db_execute:
    """Helper to mimic sqlite3.Connection.execute and return a cursor."""
    def __init__(self, conn, sql, params=None):
        self.conn = conn
        self.sql = sql.replace('?', '%s') # Convert SQLite to Postgres placeholders
        self.params = params
        self.cursor = None

    def __enter__(self):
        self.cursor = self.conn.cursor()
        self.cursor.execute(self.sql, self.params or ())
        return self.cursor

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.cursor:
            self.cursor.close()

def init_db():
    """Create all tables in Postgres if they don't exist."""
    conn = get_db()
    with conn.cursor() as cursor:
        # --- BDOs ---
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bdos (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                email TEXT,
                phone TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # --- Platforms ---
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS platforms (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                fee_percentage DOUBLE PRECISION DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # --- Platform Profiles ---
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS platform_profiles (
                id SERIAL PRIMARY KEY,
                platform_id INTEGER NOT NULL,
                profile_name TEXT NOT NULL,
                profile_url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (platform_id) REFERENCES platforms(id) ON DELETE CASCADE
            )
        """)

        # --- Payment Channels ---
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS payment_channels (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # --- Client Types ---
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS client_types (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # --- Clients ---
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS clients (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT,
                phone TEXT,
                company TEXT,
                status TEXT DEFAULT 'Active' CHECK(status IN ('Active','Inactive','Lead')),
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # --- Contracts ---
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS contracts (
                id SERIAL PRIMARY KEY,
                contract_name TEXT NOT NULL,
                date DATE,
                deadline DATE,
                workspace TEXT,
                approved_date DATE,
                delay_reason TEXT,
                client_id INTEGER,
                bdo_id INTEGER,
                platform_id INTEGER,
                platform_profile_id INTEGER,
                payment_channel_id INTEGER,
                client_type_id INTEGER,
                budget DOUBLE PRECISION DEFAULT 0,
                estimated_revenue DOUBLE PRECISION DEFAULT 0,
                payment_structure TEXT DEFAULT 'One-Time' CHECK(payment_structure IN ('One-Time','Milestone')),
                status TEXT DEFAULT 'In Progress' CHECK(status IN ('In Progress','Completed','On Hold','Cancelled')),
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE SET NULL,
                FOREIGN KEY (bdo_id) REFERENCES bdos(id) ON DELETE SET NULL,
                FOREIGN KEY (platform_id) REFERENCES platforms(id) ON DELETE SET NULL,
                FOREIGN KEY (platform_profile_id) REFERENCES platform_profiles(id) ON DELETE SET NULL,
                FOREIGN KEY (payment_channel_id) REFERENCES payment_channels(id) ON DELETE SET NULL,
                FOREIGN KEY (client_type_id) REFERENCES client_types(id) ON DELETE SET NULL
            )
        """)

        # --- Payments ---
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                id SERIAL PRIMARY KEY,
                contract_id INTEGER NOT NULL,
                amount DOUBLE PRECISION NOT NULL,
                payment_date DATE NOT NULL,
                payment_channel_id INTEGER,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (contract_id) REFERENCES contracts(id) ON DELETE CASCADE,
                FOREIGN KEY (payment_channel_id) REFERENCES payment_channels(id) ON DELETE SET NULL
            )
        """)

        # --- Milestones ---
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS milestones (
                id SERIAL PRIMARY KEY,
                contract_id INTEGER NOT NULL,
                description TEXT NOT NULL,
                amount DOUBLE PRECISION NOT NULL,
                due_date DATE NOT NULL,
                status TEXT DEFAULT 'Pending' CHECK(status IN ('Pending','Paid')),
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (contract_id) REFERENCES contracts(id) ON DELETE CASCADE
            )
        """)

        # Seed defaults
        _seed_defaults(cursor)
        conn.commit()
    conn.close()

def _seed_defaults(cursor):
    """Seed default platforms, channels, and types."""
    platforms = ["Upwork", "LinkedIn", "Fiverr", "Direct", "Referral", "Other"]
    for p in platforms:
        cursor.execute("INSERT INTO platforms (name) VALUES (%s) ON CONFLICT (name) DO NOTHING", (p,))

    channels = ["Wise", "PayPal", "Bank Transfer", "Payoneer", "Crypto", "Cash", "Other"]
    for c in channels:
        cursor.execute("INSERT INTO payment_channels (name) VALUES (%s) ON CONFLICT (name) DO NOTHING", (c,))

    types = ["One-time", "Retainer", "Hourly", "Monthly", "Project-based"]
    for t in types:
        cursor.execute("INSERT INTO client_types (name) VALUES (%s) ON CONFLICT (name) DO NOTHING", (t,))

def dict_from_row(row):
    """Convert a row to a dict."""
    if row is None:
        return None
    return dict(row)

def dicts_from_rows(rows):
    """Convert a list of rows to a list of dicts."""
    return [dict(row) for row in rows]
