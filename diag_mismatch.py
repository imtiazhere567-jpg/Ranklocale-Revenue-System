import sqlite3
import json
from datetime import datetime

def dicts_from_rows(cursor):
    return [dict(zip([col[0] for col in cursor.description], row)) for row in cursor.fetchall()]

conn = sqlite3.connect('database.db')
conn.row_factory = sqlite3.Row

# Dashboard March 2026 -> February Breakdown
year_month_start = '2026-03-01'
next_month_start = '2026-04-01'

print("--- DASHBOARD RECOVERY BREAKDOWN (FEB PROJECTS) ---")
q_dash = """
    SELECT c.contract_name, p.amount, p.payment_date, c.date as contract_date
    FROM payments p JOIN contracts c ON p.contract_id = c.id
    WHERE p.payment_date >= ? AND p.payment_date < ?
    AND c.date >= '2026-02-01' AND c.date < '2026-03-01'
"""
cur = conn.execute(q_dash, (year_month_start, next_month_start))
dash_rows = dicts_from_rows(cur)
total_dash = sum(r['amount'] for r in dash_rows)
for r in dash_rows:
    print(f"Project: {r['contract_name']} | Pmt: {r['amount']} | Date: {r['payment_date']} | Created: {r['contract_date']}")
print(f"DASHBOARD TOTAL: {total_dash}")

print("\n--- CONTRACTS PAGE FILTER (FEB PROJECTS + MARCH PMTS) ---")
q_list = """
    SELECT c.contract_name, c.id, c.date as contract_date
    FROM contracts c
    WHERE c.date >= '2026-02-01' AND c.date < '2026-03-01'
    AND EXISTS (SELECT 1 FROM payments p2 WHERE p2.contract_id = c.id 
                AND p2.payment_date >= '2026-03-01' AND p2.payment_date < '2026-04-01')
"""
cur = conn.execute(q_list)
list_rows = dicts_from_rows(cur)
total_list_sum = 0
for c in list_rows:
    p_row = conn.execute("""
        SELECT SUM(amount) as amt FROM payments 
        WHERE contract_id = ? AND payment_date >= '2026-03-01' AND payment_date < '2026-04-01'
    """, (c['id'],)).fetchone()
    amt = p_row['amt'] or 0
    total_list_sum += amt
    print(f"Project: {c['contract_name']} | Recovered in Period: {amt}")
print(f"LIST TOTAL: {total_list_sum}")

conn.close()
