import sqlite3
import random
from app import app
from models import get_db

with app.app_context():
    conn = get_db()
    
    # --- BDOS ---
    conn.executemany("INSERT INTO bdos (name, email) VALUES (?, ?)", [
        ("Shahab", "shahab@ranklocale.com"),
        ("Numan", "numan@ranklocale.com"),
        ("Ali", "ali@ranklocale.com")
    ])
    conn.commit()
    print("[OK] BDOs added")

    # --- Platforms ---
    platforms = conn.execute("SELECT id, name FROM platforms").fetchall()
    p_map = {row["name"]: row["id"] for row in platforms}
    
    conn.executemany("INSERT INTO platform_profiles (platform_id, profile_name, profile_url) VALUES (?, ?, ?)", [
        (p_map.get("Upwork"), "Ranklocale Main", "https://upwork.com/ag/ranklocale"),
        (p_map.get("Upwork"), "Shahab Personal", "https://upwork.com/fl/shahab"),
        (p_map.get("LinkedIn"), "Ranklocale LinkedIn", "https://linkedin.com/company/ranklocale"),
        (p_map.get("Fiverr"), "Ranklocale Fiverr", "https://fiverr.com/ranklocale")
    ])
    conn.commit()
    print("[OK] Profiles added")

    # --- Clients ---
    clients = [
        ("Ryan Thompson", "ryan@pestco.com", "+1-555-0101", "Pest Control Co", "Active"),
        ("Sarah Mitchell", "sarah@greenleaf.io", "+1-555-0202", "GreenLeaf Digital", "Active"),
        ("Ahmed Khan", "ahmed@techvista.pk", "+92-300-1234567", "TechVista Solutions", "Active"),
        ("Jessica Liu", "jessica@brightpath.com", "+1-555-0303", "BrightPath Marketing", "Active"),
        ("Michael Brown", "mike@brownlaw.com", "+1-555-0404", "Brown & Associates Law", "Active"),
        ("David Park", "david@startup.io", "+1-555-0505", "ParkTech Startup", "Active"),
        ("Emma Wilson", "emma@fashionhub.co", "+44-7700-900000", "FashionHub UK", "Active"),
        ("Carlos Reyes", "carlos@mxdesign.com", "+52-55-12345678", "MX Design Studio", "Inactive"),
        ("Fatima Hassan", "fatima@edutrain.ae", "+971-50-1234567", "EduTrain Academy", "Lead"),
        ("Tom Richards", "tom@richmedia.com", "+1-555-0606", "Rich Media Productions", "Active"),
    ]
    conn.executemany("INSERT INTO clients (name, email, phone, company, status) VALUES (?, ?, ?, ?, ?)", clients)
    conn.commit()
    print("[OK] Clients added")

    # Fetch lookup data
    bdos = {r["name"]: r["id"] for r in conn.execute("SELECT id, name FROM bdos").fetchall()}
    clts = {r["name"]: r["id"] for r in conn.execute("SELECT id, name FROM clients").fetchall()}
    channels = [r["id"] for r in conn.execute("SELECT id FROM payment_channels").fetchall()]
    types = [r["id"] for r in conn.execute("SELECT id FROM client_types").fetchall()]

    # --- Contracts ---
    contracts_data = [
        ("WP-WD-Pest-Ryan-Numan", "2026-01-15", "2026-02-15", "Ryan Thompson", "Numan", "Upwork", 800, "Completed", "Pest Control", "WordPress website redesign for pest control company", ""),
        ("SEO-GreenLeaf-Shahab", "2026-01-20", "2026-03-20", "Sarah Mitchell", "Shahab", "LinkedIn", 1200, "In Progress", "SEO Projects", "6-month SEO retainer for GreenLeaf Digital", ""),
        ("WP-Ecom-TechVista-Ali", "2026-02-01", "2026-03-01", "Ahmed Khan", "Ali", "Direct", 2500, "Completed", "E-commerce", "WooCommerce store with payment gateway integration", ""),
        ("SM-Management-BrightPath", "2026-02-10", "2026-04-10", "Jessica Liu", "Shahab", "Upwork", 1500, "In Progress", "Social Media", "Social media management and content creation", ""),
        ("WP-LawFirm-Brown-Numan", "2026-02-15", "2026-03-25", "Michael Brown", "Numan", "Upwork", 950, "In Progress", "Legal", "Law firm website with case management portal", ""),
        ("MVP-App-ParkTech-Ali", "2026-02-20", "2026-04-20", "David Park", "Ali", "LinkedIn", 3500, "In Progress", "App Development", "React Native MVP for SaaS product", ""),
        ("Shopify-FashionHub-Shahab", "2026-03-01", "2026-04-01", "Emma Wilson", "Shahab", "Fiverr", 600, "In Progress", "E-commerce", "Shopify store setup and theme customization", ""),
        ("Logo-Brand-MXDesign-Numan", "2026-01-05", "2026-01-25", "Carlos Reyes", "Numan", "Fiverr", 350, "Completed", "Branding", "Logo design and brand guidelines", ""),
        ("LMS-EduTrain-Ali", "2026-03-10", "2026-05-10", "Fatima Hassan", "Ali", "Direct", 4000, "In Progress", "LMS", "Custom Learning Management System", ""),
        ("VideoEdit-RichMedia-Shahab", "2026-03-05", "2026-03-28", "Tom Richards", "Shahab", "Upwork", 450, "In Progress", "Video", "YouTube channel video editing package", ""),
        ("SEO-Audit-Pest-Numan", "2026-03-15", "2026-04-15", "Ryan Thompson", "Numan", "Direct", 500, "In Progress", "SEO Projects", "Follow-up SEO audit and optimization", ""),
        ("WP-Maintenance-GreenLeaf", "2026-02-25", "2026-03-25", "Sarah Mitchell", "Shahab", "LinkedIn", 300, "On Hold", "Maintenance", "Monthly WordPress maintenance contract", "Client requested pause until April"),
    ]

    for c in contracts_data:
        conn.execute("""
            INSERT INTO contracts (
                contract_name, date, deadline, client_id, bdo_id, platform_id,
                estimated_revenue, status, workspace, notes, delay_reason,
                client_type_id, payment_channel_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            c[0], c[1], c[2], clts[c[3]], bdos[c[4]], p_map.get(c[5]),
            c[6], c[7], c[8], c[9], c[10], random.choice(types), random.choice(channels)
        ))
    conn.commit()
    print(f"[OK] {len(contracts_data)} Contracts added")

    conts = {r["contract_name"]: r["id"] for r in conn.execute("SELECT id, contract_name FROM contracts").fetchall()}

    # --- Payments ---
    payments_data = [
        ("WP-WD-Pest-Ryan-Numan", 400, "2026-01-25", "First milestone"),
        ("WP-WD-Pest-Ryan-Numan", 400, "2026-02-15", "Final payment"),
        ("WP-Ecom-TechVista-Ali", 1000, "2026-02-10", "Upfront payment"),
        ("WP-Ecom-TechVista-Ali", 1500, "2026-03-01", "Completion payment"),
        ("Logo-Brand-MXDesign-Numan", 350, "2026-01-20", "Full payment"),
        ("SEO-GreenLeaf-Shahab", 400, "2026-02-20", "Month 1 retainer"),
        ("SEO-GreenLeaf-Shahab", 400, "2026-03-20", "Month 2 retainer"),
        ("SM-Management-BrightPath", 500, "2026-03-01", "First month"),
        ("WP-LawFirm-Brown-Numan", 475, "2026-03-01", "50% upfront"),
        ("MVP-App-ParkTech-Ali", 1500, "2026-03-01", "Phase 1 payment"),
        ("Shopify-FashionHub-Shahab", 300, "2026-03-10", "50% deposit"),
        ("VideoEdit-RichMedia-Shahab", 200, "2026-03-15", "Advance payment"),
        ("LMS-EduTrain-Ali", 1000, "2026-03-15", "25% upfront"),
    ]

    for p in payments_data:
        conn.execute("INSERT INTO payments (contract_id, amount, payment_date, payment_channel_id, notes) VALUES (?, ?, ?, ?, ?)", 
                    (conts[p[0]], p[1], p[2], random.choice(channels), p[3]))
    conn.commit()
    print(f"[OK] {len(payments_data)} Payments added")
    print("\nAll dummy data populated! Refresh your browser.")

    conn.close()
