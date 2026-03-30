import sqlite3

def fix_all_negative_pending():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    
    # Find all contracts where recovered > estimated_revenue
    q = """
        SELECT c.id, c.contract_name, c.budget, c.estimated_revenue, c.platform_id,
               (SELECT SUM(amount) FROM payments WHERE contract_id = c.id) as total_p
        FROM contracts c
    """
    rows = conn.execute(q).fetchall()
    
    fixed_count = 0
    for r in rows:
        total_p = r["total_p"] or 0
        est_rev = r["estimated_revenue"] or 0
        
        if total_p > est_rev:
            print(f"Fixing Contract: {r['contract_name']} | Old Est: {est_rev} | New Total: {total_p}")
            # Fetch fee
            fee = 0
            if r["platform_id"]:
                p_row = conn.execute("SELECT fee_percentage FROM platforms WHERE id = ?", (r["platform_id"],)).fetchone()
                if p_row: fee = p_row["fee_percentage"] or 0
            
            # Recalculate
            new_budget = total_p / (1 - (fee / 100)) if fee < 100 else total_p
            conn.execute("UPDATE contracts SET budget = ?, estimated_revenue = ? WHERE id = ?", (new_budget, total_p, r["id"]))
            fixed_count += 1
            
    conn.commit()
    conn.close()
    print(f"DONE. Fixed {fixed_count} contracts.")

if __name__ == "__main__":
    fix_all_negative_pending()
