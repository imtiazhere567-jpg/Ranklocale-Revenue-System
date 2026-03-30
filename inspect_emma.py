import sqlite3

conn = sqlite3.connect('database.db')
conn.row_factory = sqlite3.Row

print("--- PAYMENTS FOR 'Emma Wilson' ---")
q = "SELECT c.id, c.contract_name, c.date, p.amount, p.payment_date FROM contracts c JOIN payments p ON c.id = p.contract_id WHERE c.contract_name LIKE '%Emma Wilson%'"
rows = conn.execute(q).fetchall()
for r in rows:
    print(dict(r))

print("\n--- ALL PAYMENTS IN MARCH 2026 ---")
q2 = "SELECT c.contract_name, c.date as contract_date, p.amount, p.payment_date FROM payments p JOIN contracts c ON p.contract_id = c.id WHERE p.payment_date >= '2026-03-01' AND p.payment_date < '2026-04-01'"
rows2 = conn.execute(q2).fetchall()
for r in rows2:
    print(dict(r))

conn.close()
