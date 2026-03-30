import sqlite3

def dicts_from_rows(cursor):
    return [dict(zip([col[0] for col in cursor.description], row)) for row in cursor.fetchall()]

conn = sqlite3.connect('database.db')
conn.row_factory = sqlite3.Row

# Dashboard March 2026 -> Legacy Pending (before March)
year_month_start = '2026-03-01'

print("--- LEGACY PENDING DIAGNOSTIC ---")
# Manual check: sum(estimated_rev - actual_payments) for contracts before March
q_check = """
    SELECT c.contract_name, c.date, c.estimated_revenue, 
           COALESCE((SELECT SUM(amount) FROM payments WHERE contract_id = c.id), 0) as paid
    FROM contracts c WHERE c.date < ?
"""
rows = dicts_from_rows(conn.execute(q_check, (year_month_start,)))
total_manual = 0
for r in rows:
    balance = r['estimated_revenue'] - r['paid']
    total_manual += balance
    print(f"Project: {r['contract_name']} | Rev: {r['estimated_revenue']} | Paid: {r['paid']} | Balance: {balance}")

print(f"\nGRAND TOTAL PENDING (MANUAL): {total_manual}")

# Simulating new query
q_new = """
    SELECT COALESCE(SUM(balance), 0) as total FROM (
        SELECT c.estimated_revenue - COALESCE((SELECT SUM(amount) FROM payments WHERE contract_id = c.id), 0) as balance
        FROM contracts c WHERE c.date < ?
    )
"""
new_total = conn.execute(q_new, (year_month_start,)).fetchone()['total']
print(f"GRAND TOTAL PENDING (NEW QUERY): {new_total}")

conn.close()
