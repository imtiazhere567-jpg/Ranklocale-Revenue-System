import sqlite3
import os
from dotenv import load_dotenv
from models import get_db, init_db

load_dotenv()

def migrate():
    # Ensure tables are created first
    print("Initializing tables in Supabase...")
    try:
        init_db()
    except Exception as e:
        print(f"Warning: Table initialization failed or tables already exist: {e}")

    print("Connecting to databases...")
    sqlite_conn = sqlite3.connect("database.db")
    sqlite_conn.row_factory = sqlite3.Row
    
    try:
        pg_conn = get_db()
        pg_conn.autocommit = True
        pg_cursor = pg_conn.cursor()
    except Exception as e:
        print(f"RED ALERT: Could not connect to Supabase! {e}")
        return

    def get_sqlite_data(table):
        try:
            return [dict(row) for row in sqlite_conn.execute(f"SELECT * FROM {table}").fetchall()]
        except:
            return []

    try:
        # 1. Simple Tables
        simple_tables = ["bdos", "platforms", "payment_channels", "client_types"]
        for table in simple_tables:
            print(f"Migrating {table}...")
            data = get_sqlite_data(table)
            for row in data:
                columns = row.keys()
                values = [row[column] for column in columns]
                placeholders = ", ".join(["%s"] * len(values))
                cols_str = ", ".join(columns)
                
                query = f"INSERT INTO {table} ({cols_str}) VALUES ({placeholders}) ON CONFLICT DO NOTHING"
                pg_cursor.execute(query, values)
        
        # 2. Platform Profiles
        print("Migrating platform_profiles...")
        profiles = get_sqlite_data("platform_profiles")
        for row in profiles:
            pg_cursor.execute(
                "INSERT INTO platform_profiles (id, platform_id, profile_name, profile_url, created_at) VALUES (%s, %s, %s, %s, %s) ON CONFLICT DO NOTHING",
                (row['id'], row['platform_id'], row['profile_name'], row['profile_url'], row['created_at'])
            )

        # 3. Clients
        print("Migrating clients...")
        clients = get_sqlite_data("clients")
        for row in clients:
            pg_cursor.execute(
                "INSERT INTO clients (id, name, email, phone, company, status, notes, created_at, updated_at) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT DO NOTHING",
                (row['id'], row['name'], row.get('email'), row.get('phone'), row.get('company'), row['status'], row.get('notes'), row['created_at'], row.get('updated_at', row['created_at']))
            )

        # 4. Contracts
        print("Migrating contracts...")
        contracts = get_sqlite_data("contracts")
        for row in contracts:
            pg_cursor.execute("""
                INSERT INTO contracts (id, contract_name, date, deadline, workspace, approved_date, delay_reason, 
                                     client_id, bdo_id, platform_id, platform_profile_id, payment_channel_id, 
                                     client_type_id, budget, estimated_revenue, payment_structure, status, 
                                     notes, created_at, updated_at) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) 
                ON CONFLICT DO NOTHING
            """, (
                row['id'], row['contract_name'], row['date'], row.get('deadline'), row.get('workspace'), row.get('approved_date'), row.get('delay_reason'),
                row.get('client_id'), row.get('bdo_id'), row.get('platform_id'), row.get('platform_profile_id'), row.get('payment_channel_id'),
                row.get('client_type_id'), row.get('budget', 0), row.get('estimated_revenue', 0), row.get('payment_structure', 'One-Time'), row['status'],
                row.get('notes'), row['created_at'], row.get('updated_at', row['created_at'])
            ))

        # 5. Payments
        print("Migrating payments...")
        payments = get_sqlite_data("payments")
        for row in payments:
            pg_cursor.execute(
                "INSERT INTO payments (id, contract_id, amount, payment_date, payment_channel_id, notes, created_at) VALUES (%s, %s, %s, %s, %s, %s, %s) ON CONFLICT DO NOTHING",
                (row['id'], row['contract_id'], row['amount'], row['payment_date'], row.get('payment_channel_id'), row.get('notes'), row['created_at'])
            )

        # 6. Milestones
        print("Migrating milestones...")
        milestones = get_sqlite_data("milestones")
        for row in milestones:
            pg_cursor.execute(
                "INSERT INTO milestones (id, contract_id, description, amount, due_date, status, notes, created_at, updated_at) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT DO NOTHING",
                (row['id'], row['contract_id'], row['description'], row['amount'], row['due_date'], row['status'], row.get('notes'), row['created_at'], row.get('updated_at', row['created_at']))
            )

        # 7. Reset Serial Sequences (Crucial for Postgres IDs to work after migration)
        print("Syncing primary key sequences...")
        tables_to_reset = ["bdos", "platforms", "platform_profiles", "payment_channels", "client_types", "clients", "contracts", "payments", "milestones"]
        for table in tables_to_reset:
            try:
                pg_cursor.execute(f"SELECT setval(pg_get_serial_sequence('{table}', 'id'), COALESCE(MAX(id), 1)) FROM {table}")
            except:
                pass

        print("\nSUCCESS: Migration completed successfully!")

    except Exception as e:
        print(f"\nERRORS OCCURRED during migration: {e}")
    finally:
        sqlite_conn.close()
        pg_conn.close()

if __name__ == "__main__":
    migrate()

if __name__ == "__main__":
    migrate()
