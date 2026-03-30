"""
Ranklocale Revenue & Client Management System
Flask backend with full REST API
"""

from flask import Flask, request, jsonify, render_template, send_from_directory
from models import get_db, init_db, dicts_from_rows, dict_from_row, db_execute
from datetime import datetime, timedelta
import os

app = Flask(__name__, static_folder="static", template_folder="templates")


# ──────────────────────────────────────────────
# PAGES
# ──────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


# ──────────────────────────────────────────────
# DASHBOARD API
# ──────────────────────────────────────────────

@app.route("/api/dashboard")
def dashboard():
    conn = get_db()
    month = request.args.get("month")  # format: YYYY-MM
    if not month:
        month = datetime.now().strftime("%Y-%m")

    year_month_start = f"{month}-01"
    # Get last day of month
    y, m = int(month.split("-")[0]), int(month.split("-")[1])
    if m == 12:
        next_month_start = f"{y + 1}-01-01"
    else:
        next_month_start = f"{y}-{m + 1:02d}-01"

    # Total estimated revenue for the month
    with db_execute(conn, 
        "SELECT COALESCE(SUM(estimated_revenue), 0) as total FROM contracts WHERE date >= ? AND date < ?",
        (year_month_start, next_month_start)
    ) as cursor:
        total_sales = cursor.fetchone()["total"]

    # Total recovered (payments) for contracts in this month
    with db_execute(conn, """
        SELECT COALESCE(SUM(p.amount), 0) as total
        FROM payments p
        JOIN contracts c ON p.contract_id = c.id
        WHERE c.date >= ? AND c.date < ?
    """, (year_month_start, next_month_start)) as cursor:
        total_recovered = cursor.fetchone()["total"]

    total_pending = total_sales - total_recovered

    # Legacy Pending (outstanding debt from contracts created BEFORE this month)
    with db_execute(conn, """
        SELECT COALESCE(SUM(balance), 0) as total FROM (
            SELECT c.estimated_revenue - COALESCE((SELECT SUM(amount) FROM payments WHERE contract_id = c.id), 0) as balance
            FROM contracts c WHERE c.date < ?
        ) s
    """, (year_month_start,)) as cursor:
        legacy_pending = max(0, cursor.fetchone()["total"])

    # Legacy Breakdown (month by month)
    # Using TO_CHAR instead of strftime for PostgreSQL
    with db_execute(conn, """
        SELECT month_val, SUM(balance) as amount FROM (
            SELECT TO_CHAR(c.date, 'YYYY-MM') as month_val,
                   c.estimated_revenue - COALESCE((SELECT SUM(amount) FROM payments WHERE contract_id = c.id), 0) as balance
            FROM contracts c WHERE c.date < ?
        ) s
        GROUP BY month_val ORDER BY month_val DESC
    """, (year_month_start,)) as cursor:
        legacy_breakdown_rows = cursor.fetchall()
    
    legacy_breakdown = []
    for r in legacy_breakdown_rows:
        m_dt = datetime.strptime(r["month_val"], '%Y-%m')
        legacy_breakdown.append({
            "month": m_dt.strftime('%B %Y'),
            "month_val": r["month_val"],
            "amount": r["amount"]
        })

    # Upcoming deadlines (next 7 days)
    today = datetime.now().strftime("%Y-%m-%d")
    seven_days = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
    
    # Contract deadlines
    row_deadlines = dicts_from_rows(conn.execute("""
        SELECT 'Contract: ' || c.contract_name as title, c.deadline as date, cl.name as client_name, c.id as contract_id, 'contract' as type
        FROM contracts c
        LEFT JOIN clients cl ON c.client_id = cl.id
        WHERE c.deadline IS NOT NULL AND c.deadline <= ? AND c.deadline >= ?
          AND c.status IN ('In Progress', 'On Hold')
    """, (seven_days, today)).fetchall())

    # Milestone deadlines
    milestone_deadlines = dicts_from_rows(conn.execute("""
        SELECT 'Milestone: ' || m.description || ' (' || c.contract_name || ')' as title, m.due_date as date, cl.name as client_name, c.id as contract_id, 'milestone' as type
        FROM milestones m
        JOIN contracts c ON m.contract_id = c.id
        LEFT JOIN clients cl ON c.client_id = cl.id
        WHERE m.status = 'Pending' AND m.due_date <= ? AND m.due_date >= ?
    """, (seven_days, today)).fetchall())

    all_upcoming = sorted(row_deadlines + milestone_deadlines, key=lambda x: x['date'])[:10]

    # Overdue
    row_overdue = dicts_from_rows(conn.execute("""
        SELECT 'Contract: ' || c.contract_name as title, c.deadline as date, cl.name as client_name, c.id as contract_id, 'contract' as type
        FROM contracts c
        LEFT JOIN clients cl ON c.client_id = cl.id
        WHERE c.deadline IS NOT NULL AND c.deadline < ?
          AND c.status IN ('In Progress', 'On Hold')
    """, (today,)).fetchall())

    milestone_overdue = dicts_from_rows(conn.execute("""
        SELECT 'Milestone: ' || m.description || ' (' || c.contract_name || ')' as title, m.due_date as date, cl.name as client_name, c.id as contract_id, 'milestone' as type
        FROM milestones m
        JOIN contracts c ON m.contract_id = c.id
        LEFT JOIN clients cl ON c.client_id = cl.id
        WHERE m.status = 'Pending' AND m.due_date < ?
    """, (today,)).fetchall())

    all_overdue = sorted(row_overdue + milestone_overdue, key=lambda x: x['date'])

    # Recent contracts
    with db_execute(conn, """
        SELECT c.*, cl.name as client_name, b.name as bdo_name
        FROM contracts c
        LEFT JOIN clients cl ON c.client_id = cl.id
        LEFT JOIN bdos b ON c.bdo_id = b.id
        ORDER BY c.created_at DESC
        LIMIT 5
    """) as cursor:
        recent = dicts_from_rows(cursor.fetchall())

    # Contract counts by status
    with db_execute(conn, """
        SELECT status, COUNT(*) as count FROM contracts GROUP BY status
    """) as cursor:
        status_counts = dicts_from_rows(cursor.fetchall())

    # Recovered Breakdown (Shows WHERE the cash collected this month came from)
    with db_execute(conn, """
        SELECT TO_CHAR(c.date, 'YYYY-MM') as m_val, SUM(p.amount) as amt
        FROM payments p JOIN contracts c ON p.contract_id = c.id
        WHERE p.payment_date >= %s AND p.payment_date < %s GROUP BY m_val
        ORDER BY m_val DESC
    """, (year_month_start, next_month_start)) as cursor:
        recovered_data = cursor.fetchall()
    recovered_breakdown = [{"month": datetime.strptime(r['m_val'], "%Y-%m").strftime("%B %Y"), "amount": r['amt'], "m_val": r['m_val']} for r in recovered_data]

    # In Progress Breakdown (by contract start month)
    with db_execute(conn, """
        SELECT TO_CHAR(date, 'YYYY-MM') as m_val, COUNT(*) as count
        FROM contracts WHERE status = 'In Progress' GROUP BY m_val
        ORDER BY m_val DESC
    """) as cursor:
        ip_data = cursor.fetchall()
    in_progress_breakdown = [{"month": datetime.strptime(r['m_val'], "%Y-%m").strftime("%B %Y"), "count": r['count'], "m_val": r['m_val']} for r in ip_data]

    # Overdue Breakdown (by deadline month)
    with db_execute(conn, """
        SELECT TO_CHAR(deadline, 'YYYY-MM') as m_val, COUNT(*) as count
        FROM contracts WHERE status IN ('In Progress', 'On Hold') AND deadline < ? GROUP BY m_val
        ORDER BY m_val DESC
    """, (today,)) as cursor:
        ov_data = cursor.fetchall()
    
    # Add milestone overdue counts
    with db_execute(conn, """
        SELECT TO_CHAR(m.due_date, 'YYYY-MM') as m_val, COUNT(*) as count
        FROM milestones m JOIN contracts c ON m.contract_id = c.id
        WHERE m.status = 'Pending' AND m.due_date < ? GROUP BY m_val
    """, (today,)) as cursor:
        m_ov_data = cursor.fetchall()
        
    # Merge ov_data and m_ov_data
    merged_ov = {}
    for r in ov_data: merged_ov[r['m_val']] = merged_ov.get(r['m_val'], 0) + r['count']
    for r in m_ov_data: merged_ov[r['m_val']] = merged_ov.get(r['m_val'], 0) + r['count']
    overdue_breakdown = [{"month": datetime.strptime(m, "%Y-%m").strftime("%B %Y"), "count": c, "m_val": m} for m, c in merged_ov.items()]
    
    # Extra Metrics for Comparative UI
    
    # 1. Total Cash Collected This Month (regardless of contract date)
    with db_execute(conn, """
        SELECT COALESCE(SUM(amount), 0) as total FROM payments
        WHERE payment_date >= ? AND payment_date < ?
    """, (year_month_start, next_month_start)) as cursor:
        cash_this_month = cursor.fetchone()["total"]

    # 2. New In Progress This Month
    with db_execute(conn, """
        SELECT COUNT(*) as count FROM contracts 
        WHERE date >= ? AND date < ? AND status = 'In Progress'
    """, (year_month_start, next_month_start)) as cursor:
        new_in_progress = cursor.fetchone()["count"]

    # 3. Overdue This Month (Due this month and already past deadline)
    with db_execute(conn, """
        SELECT COUNT(*) as count FROM contracts
        WHERE status IN ('In Progress', 'On Hold') 
          AND deadline >= ? AND deadline < ? AND deadline < ?
    """, (year_month_start, next_month_start, today)) as cursor:
        overdue_this_month = cursor.fetchone()["count"]
        
    with db_execute(conn, """
        SELECT COUNT(*) as count FROM milestones
        WHERE status = 'Pending' 
          AND due_date >= ? AND due_date < ? AND due_date < ?
    """, (year_month_start, next_month_start, today)) as cursor:
        overdue_this_month += cursor.fetchone()["count"]

    conn.close()
    return jsonify({
        "month": month,
        "total_sales": total_sales,
        "total_recovered": total_recovered,
        "cash_this_month": cash_this_month,
        "total_pending": total_pending,
        "legacy_pending": legacy_pending,
        "legacy_breakdown": legacy_breakdown,
        "recovered_breakdown": recovered_breakdown,
        "in_progress_breakdown": in_progress_breakdown,
        "new_in_progress": new_in_progress,
        "overdue_breakdown": overdue_breakdown,
        "overdue_this_month": overdue_this_month,
        "upcoming_deadlines": all_upcoming,
        "overdue": all_overdue,
        "recent_contracts": recent,
        "status_counts": {r["status"]: r["count"] for r in status_counts},
        "total_contracts": sum(r["count"] for r in status_counts)
    })


# ──────────────────────────────────────────────
# CONTRACTS API
# ──────────────────────────────────────────────

@app.route("/api/contracts")
def list_contracts():
    conn = get_db()
    query = """
        SELECT c.*,
               cl.name as client_name,
               b.name as bdo_name,
               p.name as platform_name,
               pp.profile_name,
               pc.name as payment_channel_name,
               ct.name as client_type_name,
               COALESCE((SELECT SUM(amount) FROM payments WHERE contract_id = c.id), 0) as recovered
        FROM contracts c
        LEFT JOIN clients cl ON c.client_id = cl.id
        LEFT JOIN bdos b ON c.bdo_id = b.id
        LEFT JOIN platforms p ON c.platform_id = p.id
        LEFT JOIN platform_profiles pp ON c.platform_profile_id = pp.id
        LEFT JOIN payment_channels pc ON c.payment_channel_id = pc.id
        LEFT JOIN client_types ct ON c.client_type_id = ct.id
        WHERE 1=1
    """
    params = []

    # Filters
    if request.args.get("bdo_id"):
        query += " AND c.bdo_id = %s"
        params.append(request.args.get("bdo_id"))
    if request.args.get("client_id"):
        query += " AND c.client_id = %s"
        params.append(request.args.get("client_id"))
    if request.args.get("platform_id"):
        query += " AND c.platform_id = %s"
        params.append(request.args.get("platform_id"))
    if request.args.get("status"):
        query += " AND c.status = %s"
        params.append(request.args.get("status"))
    if request.args.get("client_type_id"):
        query += " AND c.client_type_id = %s"
        params.append(request.args.get("client_type_id"))
    if request.args.get("payment_channel_id"):
        query += " AND c.payment_channel_id = %s"
        params.append(request.args.get("payment_channel_id"))
    if request.args.get("date_from"):
        query += " AND c.date >= %s"
        params.append(request.args.get("date_from"))
    if request.args.get("date_to"):
        query += " AND c.date < %s"
        params.append(request.args.get("date_to"))

    # Payment Period Filters (for Dashboard Auditing)
    p_from = request.args.get("payment_date_from")
    p_to = request.args.get("payment_date_to")
    if p_from or p_to:
        query += " AND EXISTS (SELECT 1 FROM payments p2 WHERE p2.contract_id = c.id"
        if p_from:
            query += " AND p2.payment_date >= ?"
            params.append(p_from)
        if p_to:
            query += " AND p2.payment_date < ?"
            params.append(p_to)
        query += ")"

    if request.args.get("payment_status") == "pending":
        query += " AND c.estimated_revenue != COALESCE((SELECT SUM(amount) FROM payments WHERE contract_id = c.id), 0)"
    if request.args.get("payment_status") == "recovered":
        query += " AND COALESCE((SELECT SUM(amount) FROM payments WHERE contract_id = c.id), 0) > 0"
    if request.args.get("is_overdue") == "true":
        query += " AND c.deadline < CURRENT_DATE AND c.status NOT IN ('Completed', 'Cancelled')"
    if request.args.get("search"):
        query += " AND c.contract_name ILIKE ?"
        params.append(f"%{request.args.get('search')}%")

    query += " ORDER BY c.created_at DESC"

    # Execute search
    with db_execute(conn, query, tuple(params)) as cursor:
        contracts = cursor.fetchall()
    
    if contracts:
        contract_ids = [c['id'] for c in contracts]
        
        # Next Milestone logic
        with db_execute(conn, '''
            SELECT contract_id, MIN(due_date) as next_date 
            FROM milestones 
            WHERE status = 'Pending' AND contract_id = ANY(%s)
            GROUP BY contract_id
        ''', (contract_ids,)) as cursor:
            milestones = cursor.fetchall()
        milestone_map = {m['contract_id']: m['next_date'] for m in milestones}

        # Period Recovery logic
        period_map = {}
        if p_from or p_to:
            p_query = "SELECT contract_id, SUM(amount) as amt FROM payments WHERE contract_id = ANY(%s)"
            p_params = [contract_ids]
            if p_from:
                p_query += " AND payment_date >= %s"
                p_params.append(p_from)
            if p_to:
                p_query += " AND payment_date < %s"
                p_params.append(p_to)
            p_query += " GROUP BY contract_id"
            
            with db_execute(conn, p_query, tuple(p_params)) as cursor:
                p_rows = cursor.fetchall()
            period_map = {r['contract_id']: r['amt'] for r in p_rows}

        for c in contracts:
            c["pending"] = (c["estimated_revenue"] or 0) - (c["recovered"] or 0)
            c["next_milestone_date"] = milestone_map.get(c['id'])
            c["period_recovered"] = period_map.get(c['id'], 0) if (p_from or p_to) else None
            
    conn.close()
    return jsonify(contracts)


@app.route("/api/contracts", methods=["POST"])
def create_contract():
    data = request.json
    conn = get_db()
    with db_execute(conn, """
        INSERT INTO contracts (contract_name, date, deadline, workspace, approved_date,
                                delay_reason, client_id, bdo_id, platform_id, platform_profile_id,
                                payment_channel_id, client_type_id, budget, estimated_revenue, 
                                payment_structure, status, notes)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
    """, (
        data.get("contract_name"), data.get("date"), data.get("deadline"),
        data.get("workspace"), data.get("approved_date"), data.get("delay_reason"),
        data.get("client_id"), data.get("bdo_id"), data.get("platform_id"),
        data.get("platform_profile_id"), data.get("payment_channel_id"),
        data.get("client_type_id"), data.get("budget", 0), data.get("estimated_revenue", 0),
        data.get("payment_structure", "One-Time"), data.get("status", "In Progress"), data.get("notes")
    )) as cursor:
        contract_id = cursor.fetchone()["id"]
    
    milestones = data.get("milestones", [])
    if data.get("payment_structure") == "Milestone" and milestones:
        for m in milestones:
            conn.execute("INSERT INTO milestones (contract_id, description, amount, due_date) VALUES (?, ?, ?, ?)",
                         (contract_id, m.get("description"), m.get("amount"), m.get("due_date")))

    conn.commit()
    conn.close()
    return jsonify({"id": contract_id, "message": "Contract created"}), 201


@app.route("/api/contracts/<int:cid>")
def get_contract(cid):
    conn = get_db()
    with db_execute(conn, """
        SELECT c.*,
               cl.name as client_name,
               b.name as bdo_name,
               p.name as platform_name,
               pp.profile_name,
               pc.name as payment_channel_name,
               ct.name as client_type_name
        FROM contracts c
        LEFT JOIN clients cl ON c.client_id = cl.id
        LEFT JOIN bdos b ON c.bdo_id = b.id
        LEFT JOIN platforms p ON c.platform_id = p.id
        LEFT JOIN platform_profiles pp ON c.platform_profile_id = pp.id
        LEFT JOIN payment_channels pc ON c.payment_channel_id = pc.id
        LEFT JOIN client_types ct ON c.client_type_id = ct.id
        WHERE c.id = ?
    """, (cid,)) as cursor:
        contract = cursor.fetchone()

    if not contract:
        conn.close()
        return jsonify({"error": "Contract not found"}), 404

    # Get payments for this contract
    with db_execute(conn, """
        SELECT p.*, pc.name as channel_name
        FROM payments p
        LEFT JOIN payment_channels pc ON p.payment_channel_id = pc.id
        WHERE p.contract_id = ?
        ORDER BY p.payment_date DESC
    """, (cid,)) as cursor:
        payments = cursor.fetchall()
    contract["payments"] = payments

    recovered = sum(p["amount"] for p in payments)
    contract["recovered"] = recovered
    contract["pending"] = (contract["estimated_revenue"] or 0) - recovered

    # Attach milestones
    with db_execute(conn, """
        SELECT * FROM milestones WHERE contract_id = ? ORDER BY due_date ASC
    """, (cid,)) as cursor:
        contract["milestones"] = cursor.fetchall()

    conn.close()
    return jsonify(contract)


@app.route("/api/contracts/<int:cid>", methods=["PUT"])
def update_contract(cid):
    data = request.json
    conn = get_db()
    with db_execute(conn, """
        UPDATE contracts SET
            contract_name=?, date=?, deadline=?, workspace=?, approved_date=?,
            delay_reason=?, client_id=?, bdo_id=?, platform_id=?, platform_profile_id=?,
            payment_channel_id=?, client_type_id=?, budget=?, estimated_revenue=?, 
            payment_structure=?, status=?, notes=?,
            updated_at=CURRENT_TIMESTAMP
        WHERE id=?
    """, (
        data.get("contract_name"), data.get("date"), data.get("deadline"),
        data.get("workspace"), data.get("approved_date"), data.get("delay_reason"),
        data.get("client_id"), data.get("bdo_id"), data.get("platform_id"),
        data.get("platform_profile_id"), data.get("payment_channel_id"),
        data.get("client_type_id"), data.get("budget", 0), data.get("estimated_revenue", 0),
        data.get("payment_structure", "One-Time"), data.get("status", "In Progress"), data.get("notes"), cid
    )):
        pass
    conn.commit()
    conn.close()
    return jsonify({"message": "Contract updated"})


@app.route("/api/contracts/<int:cid>", methods=["DELETE"])
def delete_contract(cid):
    conn = get_db()
    with db_execute(conn, "DELETE FROM contracts WHERE id = ?", (cid,)):
        pass
    conn.commit()
    conn.close()
    return jsonify({"message": "Contract deleted"})


# ──────────────────────────────────────────────
# CLIENTS API
# ──────────────────────────────────────────────

@app.route("/api/clients")
def list_clients():
    conn = get_db()
    with db_execute(conn, """
        SELECT c.*,
               COUNT(con.id) as contract_count,
               COALESCE(SUM(con.estimated_revenue), 0) as total_revenue,
               COALESCE((SELECT SUM(p.amount) FROM payments p
                         JOIN contracts con2 ON p.contract_id = con2.id
                         WHERE con2.client_id = c.id), 0) as total_recovered
        FROM clients c
        LEFT JOIN contracts con ON c.id = con.client_id
        GROUP BY c.id
        ORDER BY c.name ASC
    """) as cursor:
        clients = cursor.fetchall()
    
    for c in clients:
        c["total_pending"] = c["total_revenue"] - c["total_recovered"]
    conn.close()
    return jsonify(clients)


@app.route("/api/clients", methods=["POST"])
def create_client():
    data = request.json
    conn = get_db()
    with db_execute(conn, """
        INSERT INTO clients (name, email, phone, company, status, notes)
        VALUES (?, ?, ?, ?, ?, ?)
        RETURNING id
    """, (
        data.get("name"), data.get("email"), data.get("phone"),
        data.get("company"), data.get("status", "Active"), data.get("notes")
    )) as cursor:
        client_id = cursor.fetchone()["id"]
        
    conn.commit()
    conn.close()
    return jsonify({"id": client_id, "message": "Client created"}), 201


@app.route("/api/clients/find-or-create", methods=["POST"])
def find_or_create_client():
    """Find a client by name, or create one if it doesn't exist."""
    data = request.json
    name = (data.get("name") or "").strip()
    if not name:
        return jsonify({"error": "Name is required"}), 400

    conn = get_db()
    # Try to find existing client (case-insensitive)
    with db_execute(conn, "SELECT * FROM clients WHERE LOWER(name) = LOWER(?)", (name,)) as cursor:
        existing = cursor.fetchone()

    if existing:
        conn.close()
        return jsonify({"id": existing["id"], "name": existing["name"], "created": False})

    # Create new client
    with db_execute(conn, "INSERT INTO clients (name, status) VALUES (?, 'Active') RETURNING id", (name,)) as cursor:
        client_id = cursor.fetchone()["id"]
        
    conn.commit()
    conn.close()
    return jsonify({"id": client_id, "name": name, "created": True}), 201


@app.route("/api/clients/<int:cid>")
def get_client(cid):
    conn = get_db()
    with db_execute(conn, "SELECT * FROM clients WHERE id = ?", (cid,)) as cursor:
        client = cursor.fetchone()
    if not client:
        conn.close()
        return jsonify({"error": "Client not found"}), 404

    # Legacy Pending (from before this month)
    today = datetime.now().strftime("%Y-%m-%d")
    with db_execute(conn, """
        SELECT COALESCE(SUM(balance), 0) as total FROM (
            SELECT c.estimated_revenue - COALESCE((SELECT SUM(amount) FROM payments WHERE contract_id = c.id), 0) as balance
            FROM contracts c WHERE c.date < ? AND c.client_id = ?
        ) s
    """, (today, cid)) as cursor:
        legacy_pending = cursor.fetchone()["total"]
    client["legacy_pending"] = legacy_pending

    # Get all contracts for this client
    with db_execute(conn, """
        SELECT c.*, b.name as bdo_name, p.name as platform_name,
               COALESCE((SELECT SUM(amount) FROM payments WHERE contract_id = c.id), 0) as recovered
        FROM contracts c
        LEFT JOIN bdos b ON c.bdo_id = b.id
        LEFT JOIN platforms p ON c.platform_id = p.id
        WHERE c.client_id = ?
        ORDER BY c.date DESC
    """, (cid,)) as cursor:
        contracts = cursor.fetchall()
        
    for c in contracts:
        c["pending"] = (c["estimated_revenue"] or 0) - c["recovered"]
    client["contracts"] = contracts

    # Payment history
    with db_execute(conn, """
        SELECT p.*, c.contract_name, pc.name as channel_name
        FROM payments p
        JOIN contracts c ON p.contract_id = c.id
        LEFT JOIN payment_channels pc ON p.payment_channel_id = pc.id
        WHERE c.client_id = ?
        ORDER BY p.payment_date DESC
    """, (cid,)) as cursor:
        client["payments"] = cursor.fetchall()

    conn.close()
    return jsonify(client)


@app.route("/api/clients/<int:cid>", methods=["PUT"])
def update_client(cid):
    data = request.json
    conn = get_db()
    with db_execute(conn, """
        UPDATE clients SET name=?, email=?, phone=?, company=?, status=?, notes=?,
               updated_at=CURRENT_TIMESTAMP
        WHERE id=?
    """, (
        data.get("name"), data.get("email"), data.get("phone"),
        data.get("company"), data.get("status", "Active"), data.get("notes"), cid
    )):
        pass
    conn.commit()
    conn.close()
    return jsonify({"message": "Client updated"})


@app.route("/api/clients/<int:cid>", methods=["DELETE"])
def delete_client(cid):
    conn = get_db()
    with db_execute(conn, "DELETE FROM clients WHERE id = ?", (cid,)):
        pass
    conn.commit()
    conn.close()
    return jsonify({"message": "Client deleted"})


# ──────────────────────────────────────────────
# PAYMENTS API
# ──────────────────────────────────────────────

@app.route("/api/payments")
def list_payments():
    conn = get_db()
    query = """
        SELECT p.*, c.contract_name, cl.name as client_name, pc.name as channel_name
        FROM payments p
        JOIN contracts c ON p.contract_id = c.id
        LEFT JOIN clients cl ON c.client_id = cl.id
        LEFT JOIN payment_channels pc ON p.payment_channel_id = pc.id
        WHERE 1=1
    """
    params = []

    if request.args.get("contract_id"):
        query += " AND p.contract_id = %s"
        params.append(request.args.get("contract_id"))
    if request.args.get("client_id"):
        query += " AND c.client_id = %s"
        params.append(request.args.get("client_id"))
    if request.args.get("date_from"):
        query += " AND p.payment_date >= %s"
        params.append(request.args.get("date_from"))
    if request.args.get("date_to"):
        query += " AND p.payment_date <= %s"
        params.append(request.args.get("date_to"))

    query += " ORDER BY p.payment_date DESC"

    with db_execute(conn, query, tuple(params)) as cursor:
        payments = cursor.fetchall()
        
    conn.close()
    return jsonify(payments)


@app.route("/api/payments", methods=["POST"])
def create_payment():
    data = request.json
    conn = get_db()
    with db_execute(conn, """
        INSERT INTO payments (contract_id, amount, payment_date, payment_channel_id, notes)
        VALUES (?, ?, ?, ?, ?)
        RETURNING id
    """, (
        data.get("contract_id"), data.get("amount"), data.get("payment_date"),
        data.get("payment_channel_id"), data.get("notes")
    )) as cursor:
        payment_id = cursor.fetchone()["id"]
    
    # Auto-Growth Budget logic
    cid = data.get("contract_id")
    if cid:
        with db_execute(conn, "SELECT budget, estimated_revenue, platform_id FROM contracts WHERE id = ?", (cid,)) as cursor:
            c_row = cursor.fetchone()
        with db_execute(conn, "SELECT SUM(amount) as s FROM payments WHERE contract_id = ?", (cid,)) as cursor:
            total_p = cursor.fetchone()["s"] or 0
        
        if total_p > (c_row["estimated_revenue"] or 0):
            fee = 0
            if c_row["platform_id"]:
                with db_execute(conn, "SELECT fee_percentage FROM platforms WHERE id = ?", (c_row["platform_id"],)) as cursor:
                    p_row = cursor.fetchone()
                    if p_row: fee = p_row["fee_percentage"] or 0
            
            new_budget = total_p / (1 - (fee / 100)) if fee < 100 else total_p
            with db_execute(conn, "UPDATE contracts SET budget = ?, estimated_revenue = ? WHERE id = ?", (new_budget, total_p, cid)):
                pass
    
    conn.commit()
    conn.close()
    return jsonify({"id": payment_id, "message": "Payment recorded"}), 201


@app.route("/api/payments/<int:pid>", methods=["DELETE"])
def delete_payment(pid):
    conn = get_db()
    with db_execute(conn, "DELETE FROM payments WHERE id = ?", (pid,)):
        pass
    conn.commit()
    conn.close()
    return jsonify({"message": "Payment deleted"})


# ──────────────────────────────────────────────
# BDOs API
# ──────────────────────────────────────────────

@app.route("/api/bdos")
def list_bdos():
    conn = get_db()
    with db_execute(conn, """
        SELECT b.*, COUNT(c.id) as contract_count
        FROM bdos b
        LEFT JOIN contracts c ON b.id = c.bdo_id
        GROUP BY b.id
        ORDER BY b.name
    """) as cursor:
        bdos = cursor.fetchall()
    conn.close()
    return jsonify(bdos)


@app.route("/api/bdos", methods=["POST"])
def create_bdo():
    data = request.json
    conn = get_db()
    with db_execute(conn,
        "INSERT INTO bdos (name, email, phone) VALUES (?, ?, ?) RETURNING id",
        (data.get("name"), data.get("email"), data.get("phone"))
    ) as cursor:
        bdo_id = cursor.fetchone()["id"]
        
    conn.commit()
    conn.close()
    return jsonify({"id": bdo_id, "message": "BDO added"}), 201


@app.route("/api/bdos/<int:bid>", methods=["PUT"])
def update_bdo(bid):
    data = request.json
    conn = get_db()
    with db_execute(conn,
        "UPDATE bdos SET name=?, email=?, phone=? WHERE id=?",
        (data.get("name"), data.get("email"), data.get("phone"), bid)
    ):
        pass
    conn.commit()
    conn.close()
    return jsonify({"message": "BDO updated"})


@app.route("/api/bdos/<int:bid>", methods=["DELETE"])
def delete_bdo(bid):
    conn = get_db()
    with db_execute(conn, "DELETE FROM bdos WHERE id = ?", (bid,)):
        pass
    conn.commit()
    conn.close()
    return jsonify({"message": "BDO deleted"})


# ──────────────────────────────────────────────
# PLATFORMS API
# ──────────────────────────────────────────────

@app.route("/api/platforms")
def list_platforms():
    conn = get_db()
    with db_execute(conn, "SELECT * FROM platforms ORDER BY name") as cursor:
        platforms = cursor.fetchall()
    conn.close()
    return jsonify(platforms)


@app.route("/api/platforms", methods=["POST"])
def create_platform():
    data = request.json
    conn = get_db()
    with db_execute(conn, "INSERT INTO platforms (name, fee_percentage) VALUES (?, ?) RETURNING id", 
                          (data.get("name"), data.get("fee_percentage", 0))) as cursor:
        pid = cursor.fetchone()["id"]
        
    conn.commit()
    conn.close()
    return jsonify({"id": pid, "message": "Platform added"}), 201

@app.route("/api/platforms/<int:pid>", methods=["PUT"])
def update_platform(pid):
    data = request.json
    conn = get_db()
    with db_execute(conn, "UPDATE platforms SET name = ?, fee_percentage = ? WHERE id = ?", 
                 (data.get("name"), data.get("fee_percentage", 0), pid)):
        pass
    conn.commit()
    conn.close()
    return jsonify({"message": "Platform updated"})


@app.route("/api/platforms/<int:pid>", methods=["DELETE"])
def delete_platform(pid):
    conn = get_db()
    with db_execute(conn, "DELETE FROM platforms WHERE id = ?", (pid,)):
        pass
    conn.commit()
    conn.close()
    return jsonify({"message": "Platform deleted"})


# ──────────────────────────────────────────────
# PLATFORM PROFILES API
# ──────────────────────────────────────────────

@app.route("/api/platform-profiles")
def list_profiles():
    conn = get_db()
    platform_id = request.args.get("platform_id")
    if platform_id:
        with db_execute(conn,
            "SELECT pp.*, p.name as platform_name FROM platform_profiles pp JOIN platforms p ON pp.platform_id = p.id WHERE pp.platform_id = ? ORDER BY pp.profile_name",
            (platform_id,)
        ) as cursor:
            profiles = cursor.fetchall()
    else:
        with db_execute(conn,
            "SELECT pp.*, p.name as platform_name FROM platform_profiles pp JOIN platforms p ON pp.platform_id = p.id ORDER BY p.name, pp.profile_name"
        ) as cursor:
            profiles = cursor.fetchall()
            
    conn.close()
    return jsonify(profiles)


@app.route("/api/platform-profiles", methods=["POST"])
def create_profile():
    data = request.json
    conn = get_db()
    with db_execute(conn,
        "INSERT INTO platform_profiles (platform_id, profile_name, profile_url) VALUES (?, ?, ?) RETURNING id",
        (data.get("platform_id"), data.get("profile_name"), data.get("profile_url"))
    ) as cursor:
        prof_id = cursor.fetchone()["id"]
        
    conn.commit()
    conn.close()
    return jsonify({"id": prof_id, "message": "Profile added"}), 201


@app.route("/api/platform-profiles/<int:pid>", methods=["DELETE"])
def delete_profile(pid):
    conn = get_db()
    with db_execute(conn, "DELETE FROM platform_profiles WHERE id = ?", (pid,)):
        pass
    conn.commit()
    conn.close()
    return jsonify({"message": "Profile deleted"})


# ──────────────────────────────────────────────
# PAYMENT CHANNELS API
# ──────────────────────────────────────────────

@app.route("/api/payment-channels")
def list_channels():
    conn = get_db()
    with db_execute(conn, "SELECT * FROM payment_channels ORDER BY name") as cursor:
        channels = cursor.fetchall()
    conn.close()
    return jsonify(channels)


@app.route("/api/payment-channels", methods=["POST"])
def create_channel():
    data = request.json
    conn = get_db()
    with db_execute(conn, "INSERT INTO payment_channels (name) VALUES (?) RETURNING id", (data.get("name"),)) as cursor:
        cid = cursor.fetchone()["id"]
        
    conn.commit()
    conn.close()
    return jsonify({"id": cid, "message": "Payment channel added"}), 201


@app.route("/api/payment-channels/<int:cid>", methods=["DELETE"])
def delete_channel(cid):
    conn = get_db()
    with db_execute(conn, "DELETE FROM payment_channels WHERE id = ?", (cid,)):
        pass
    conn.commit()
    conn.close()
    return jsonify({"message": "Payment channel deleted"})


# ──────────────────────────────────────────────
# CLIENT TYPES API
# ──────────────────────────────────────────────

@app.route("/api/client-types")
def list_client_types():
    conn = get_db()
    with db_execute(conn, "SELECT * FROM client_types ORDER BY name") as cursor:
        types = cursor.fetchall()
    conn.close()
    return jsonify(types)


@app.route("/api/client-types", methods=["POST"])
def create_client_type():
    data = request.json
    conn = get_db()
    with db_execute(conn, "INSERT INTO client_types (name) VALUES (?) RETURNING id", (data.get("name"),)) as cursor:
        tid = cursor.fetchone()["id"]
    conn.commit()
    conn.close()
    return jsonify({"id": tid, "message": "Client type added"}), 201


@app.route("/api/client-types/<int:tid>", methods=["DELETE"])
def delete_client_type(tid):
    conn = get_db()
    with db_execute(conn, "DELETE FROM client_types WHERE id = ?", (tid,)):
        pass
    conn.commit()
    conn.close()
    return jsonify({"message": "Client type deleted"})


# ──────────────────────────────────────────────
# REPORTS API
# ──────────────────────────────────────────────

@app.route("/api/reports/monthly")
def monthly_report():
    conn = get_db()
    # Get monthly summaries for all months using TO_CHAR
    with db_execute(conn, """
        SELECT
            TO_CHAR(c.date, 'YYYY-MM') as month,
            COUNT(c.id) as total_contracts,
            COALESCE(SUM(c.estimated_revenue), 0) as total_sales,
            COALESCE(SUM(
                (SELECT COALESCE(SUM(p.amount), 0) FROM payments p WHERE p.contract_id = c.id)
            ), 0) as total_recovered
        FROM contracts c
        WHERE c.date IS NOT NULL
        GROUP BY month
        ORDER BY month DESC
    """) as cursor:
        rows = cursor.fetchall()
            
    for r in rows:
        r["total_pending"] = r["total_sales"] - r["total_recovered"]
    conn.close()
    return jsonify(rows)


@app.route("/api/reports/by-bdo")
def bdo_report():
    conn = get_db()
    with db_execute(conn, """
        SELECT
            b.name as bdo_name,
            COUNT(c.id) as total_contracts,
            COALESCE(SUM(c.estimated_revenue), 0) as total_sales,
            SUM(CASE WHEN c.status = 'Completed' THEN 1 ELSE 0 END) as completed,
            SUM(CASE WHEN c.status = 'In Progress' THEN 1 ELSE 0 END) as in_progress
        FROM bdos b
        LEFT JOIN contracts c ON b.id = c.bdo_id
        GROUP BY b.id, b.name
        ORDER BY total_sales DESC
    """) as cursor:
        rows = cursor.fetchall()
    conn.close()
    return jsonify(rows)


@app.route("/api/reports/by-platform")
def platform_report():
    conn = get_db()
    with db_execute(conn, """
        SELECT
            p.name as platform_name,
            COUNT(c.id) as total_contracts,
            COALESCE(SUM(c.estimated_revenue), 0) as total_sales,
            COALESCE(SUM(
                (SELECT COALESCE(SUM(pay.amount), 0) FROM payments pay WHERE pay.contract_id = c.id)
            ), 0) as total_recovered
        FROM platforms p
        LEFT JOIN contracts c ON p.id = c.platform_id
        GROUP BY p.id, p.name
        ORDER BY total_sales DESC
    """) as cursor:
        rows = cursor.fetchall()
            
    for r in rows:
        r["total_pending"] = r["total_sales"] - r["total_recovered"]
    conn.close()
    return jsonify(rows)


@app.route("/api/reports/advanced")
def advanced_report():
    bdo_id = request.args.get("bdo_id")
    platform_id = request.args.get("platform_id")
    client_id = request.args.get("client_id")
    contract_id = request.args.get("contract_id")
    date_from = request.args.get("date_from")
    date_to = request.args.get("date_to")

    conn = get_db()
    
    where_clauses = ["1=1"]
    params = []
    
    if bdo_id:
        where_clauses.append("c.bdo_id = %s")
        params.append(bdo_id)
    if platform_id:
        where_clauses.append("c.platform_id = %s")
        params.append(platform_id)
    if client_id:
        where_clauses.append("c.client_id = %s")
        params.append(client_id)
    if contract_id:
        where_clauses.append("c.id = %s")
        params.append(contract_id)
    if date_from:
        where_clauses.append("c.date >= %s")
        params.append(date_from)
    if date_to:
        where_clauses.append("c.date <= %s")
        params.append(date_to)
        
    where_sql = " AND ".join(where_clauses)
    
    # Summary Stats
    stats_query = f"""
        SELECT 
            COUNT(c.id) as total_contracts,
            COALESCE(SUM(c.budget), 0) as total_gross,
            COALESCE(SUM(c.estimated_revenue), 0) as total_net,
            (SELECT COALESCE(SUM(p.amount), 0) 
             FROM payments p 
             JOIN contracts c2 ON p.contract_id = c2.id 
             WHERE {where_sql.replace('c.', 'c2.')}) as total_recovered
        FROM contracts c
        WHERE {where_sql}
    """
    with db_execute(conn, stats_query, params + params) as cursor:
        stats = cursor.fetchone()
    
    stats["total_pending"] = stats["total_net"] - stats["total_recovered"]
    stats["recovery_rate"] = round((stats["total_recovered"] / stats["total_net"] * 100), 1) if stats["total_net"] > 0 else 0
    
    # Monthly Trend (using TO_CHAR)
    trend_query = f"""
        SELECT 
            TO_CHAR(c.date, 'YYYY-MM') as month,
            SUM(c.estimated_revenue) as net_revenue,
            (SELECT SUM(p.amount) 
             FROM payments p 
             JOIN contracts c2 ON p.contract_id = c2.id 
             WHERE TO_CHAR(c2.date, 'YYYY-MM') = TO_CHAR(c.date, 'YYYY-MM') 
             AND {where_sql.replace('c.', 'c2.')}) as recovered
        FROM contracts c
        WHERE {where_sql}
        GROUP BY month
        ORDER BY month ASC
        LIMIT 24
    """
    with db_execute(conn, trend_query, params + params) as cursor:
        trend_rows = cursor.fetchall()
    
    # BDO Breakdown
    bdo_query = f"""
        SELECT 
            b.name as bdo_name,
            SUM(c.estimated_revenue) as revenue
        FROM bdos b
        JOIN contracts c ON b.id = c.bdo_id
        WHERE {where_sql}
        GROUP BY b.id, b.name
        ORDER BY revenue DESC
    """
    with db_execute(conn, bdo_query, params) as cursor:
        bdo_breakdown = cursor.fetchall()
    
    # Platform Breakdown
    platform_query = f"""
        SELECT 
            p.name as platform_name,
            SUM(c.estimated_revenue) as revenue
        FROM platforms p
        JOIN contracts c ON p.id = c.platform_id
        WHERE {where_sql}
        GROUP BY p.id, p.name
        ORDER BY revenue DESC
    """
    with db_execute(conn, platform_query, params) as cursor:
        platform_breakdown = cursor.fetchall()
    
    conn.close()
    
    return jsonify({
        "stats": stats,
        "trend": trend_rows,
        "bdo_breakdown": bdo_breakdown,
        "platform_breakdown": platform_breakdown
    })


# ──────────────────────────────────────────────
# CSV EXPORT
# ──────────────────────────────────────────────

@app.route("/api/export/contracts")
def export_contracts():
    conn = get_db()
    with db_execute(conn, """
        SELECT c.contract_name, c.date, c.deadline, c.workspace, c.approved_date,
               c.delay_reason, cl.name as client_name, b.name as bdo_name,
               p.name as platform, pp.profile_name, pc.name as payment_channel,
               ct.name as client_type, c.estimated_revenue, c.status, c.notes,
               COALESCE((SELECT SUM(amount) FROM payments WHERE contract_id = c.id), 0) as recovered
        FROM contracts c
        LEFT JOIN clients cl ON c.client_id = cl.id
        LEFT JOIN bdos b ON c.bdo_id = b.id
        LEFT JOIN platforms p ON c.platform_id = p.id
        LEFT JOIN platform_profiles pp ON c.platform_profile_id = pp.id
        LEFT JOIN payment_channels pc ON c.payment_channel_id = pc.id
        LEFT JOIN client_types ct ON c.client_type_id = ct.id
        ORDER BY c.date DESC
    """) as cursor:
        contracts = cursor.fetchall()

    if not contracts:
        return "No data to export", 404

    import csv
    import io
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=contracts[0].keys())
    writer.writeheader()
    writer.writerows(contracts)

    from flask import Response
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=contracts_export.csv"}
    )


# ──────────────────────────────────────────────

# Initialize DB on import if DATABASE_URL is available
# This prevents Vercel from failing the entire import phase if the env var isn't set yet.
from models import DATABASE_URL
if DATABASE_URL:
    with app.app_context():
        try:
            init_db()
        except Exception as e:
            print(f"Warning: Failed to initialize database: {e}")
else:
    print("Warning: DATABASE_URL not set. Skipping init_db().")

if __name__ == "__main__":
    print("\n  Ranklocale Revenue System running at http://localhost:5000\n")
    app.run(debug=True, port=5000)

# ==========================================
# MILESTONES API
# ==========================================

@app.route("/api/milestones", methods=["POST"], strict_slashes=False)
def add_milestone():
    data = request.json
    conn = get_db()
    with db_execute(conn, "INSERT INTO milestones (contract_id, description, amount, due_date, notes) VALUES (?, ?, ?, ?, ?) RETURNING id",
                         (data["contract_id"], data["description"], data["amount"], data["due_date"], data.get("notes"))) as cursor:
        mid = cursor.fetchone()["id"]
    conn.commit()
    conn.close()
    return jsonify({"id": mid, "message": "Milestone added"})

@app.route("/api/milestones/<int:mid>/pay", methods=["POST"], strict_slashes=False)
def pay_milestone(mid):
    data = request.json or {}  # optional args: payment_channel_id, payment_date, notes
    conn = get_db()
    with db_execute(conn, "SELECT * FROM milestones WHERE id=?", (mid,)) as cursor:
        milestone = cursor.fetchone()
    if not milestone:
        conn.close()
        return jsonify({"error": "Not found"}), 404
        
    with db_execute(conn, "UPDATE milestones SET status='Paid' WHERE id=?", (mid,)):
        pass
    
    pay_date = data.get("payment_date")
    if not pay_date:
        pay_date = datetime.now().strftime("%Y-%m-%d")
        
    notes = data.get("notes") or milestone.get("notes")
    if not notes:
        notes = f"Milestone Payment: {milestone['description']}"
        
    with db_execute(conn, "INSERT INTO payments (contract_id, amount, payment_date, payment_channel_id, notes) VALUES (?, ?, ?, ?, ?)",
                 (milestone["contract_id"], milestone["amount"], pay_date, data.get("payment_channel_id"), notes)):
        pass
    
    conn.commit()
    conn.close()
    return jsonify({"message": "Milestone marked as paid"})

@app.route("/api/milestones/<int:mid>", methods=["DELETE"])
def delete_milestone(mid):
    conn = get_db()
    with db_execute(conn, "DELETE FROM milestones WHERE id=?", (mid,)):
        pass
    conn.commit()
    conn.close()
    return jsonify({"message": "Milestone deleted"})
