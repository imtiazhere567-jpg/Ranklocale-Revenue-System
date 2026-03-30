"""Seed realistic dummy data for testing the Ranklocale Revenue System."""
import requests, random

BASE = "http://localhost:5000/api"

def post(path, data):
    r = requests.post(f"{BASE}{path}", json=data)
    try:
        return r.json()
    except Exception:
        return {"status": r.status_code}

def get(path):
    return requests.get(f"{BASE}{path}").json()

# ─── BDOs ───
bdos = [
    {"name": "Shahab", "email": "shahab@ranklocale.com"},
    {"name": "Numan", "email": "numan@ranklocale.com"},
    {"name": "Ali", "email": "ali@ranklocale.com"},
]
for b in bdos:
    post("/bdos", b)
print("[OK] BDOs added")

# ─── Platform Profiles ───
platforms = get("/platforms")
upwork = next((p for p in platforms if p["name"] == "Upwork"), None)
linkedin = next((p for p in platforms if p["name"] == "LinkedIn"), None)
fiverr = next((p for p in platforms if p["name"] == "Fiverr"), None)
direct = next((p for p in platforms if p["name"] == "Direct"), None)

if upwork:
    post("/platform-profiles", {"platform_id": upwork["id"], "profile_name": "Ranklocale Main", "profile_url": "https://upwork.com/ag/ranklocale"})
    post("/platform-profiles", {"platform_id": upwork["id"], "profile_name": "Shahab Personal", "profile_url": "https://upwork.com/fl/shahab"})
if linkedin:
    post("/platform-profiles", {"platform_id": linkedin["id"], "profile_name": "Ranklocale LinkedIn", "profile_url": "https://linkedin.com/company/ranklocale"})
if fiverr:
    post("/platform-profiles", {"platform_id": fiverr["id"], "profile_name": "Ranklocale Fiverr", "profile_url": "https://fiverr.com/ranklocale"})
print("[OK] Profiles added")

# ─── Clients ───
clients_data = [
    {"name": "Ryan Thompson", "email": "ryan@pestco.com", "phone": "+1-555-0101", "company": "Pest Control Co", "status": "Active"},
    {"name": "Sarah Mitchell", "email": "sarah@greenleaf.io", "phone": "+1-555-0202", "company": "GreenLeaf Digital", "status": "Active"},
    {"name": "Ahmed Khan", "email": "ahmed@techvista.pk", "phone": "+92-300-1234567", "company": "TechVista Solutions", "status": "Active"},
    {"name": "Jessica Liu", "email": "jessica@brightpath.com", "phone": "+1-555-0303", "company": "BrightPath Marketing", "status": "Active"},
    {"name": "Michael Brown", "email": "mike@brownlaw.com", "phone": "+1-555-0404", "company": "Brown & Associates Law", "status": "Active"},
    {"name": "David Park", "email": "david@startup.io", "phone": "+1-555-0505", "company": "ParkTech Startup", "status": "Active"},
    {"name": "Emma Wilson", "email": "emma@fashionhub.co", "phone": "+44-7700-900000", "company": "FashionHub UK", "status": "Active"},
    {"name": "Carlos Reyes", "email": "carlos@mxdesign.com", "phone": "+52-55-12345678", "company": "MX Design Studio", "status": "Inactive"},
    {"name": "Fatima Hassan", "email": "fatima@edutrain.ae", "phone": "+971-50-1234567", "company": "EduTrain Academy", "status": "Lead"},
    {"name": "Tom Richards", "email": "tom@richmedia.com", "phone": "+1-555-0606", "company": "Rich Media Productions", "status": "Active"},
]
for c in clients_data:
    post("/clients", c)
print("[OK] Clients added")

# Reload lookup data
all_bdos = get("/bdos")
all_clients = get("/clients")
all_platforms = get("/platforms")
all_profiles = get("/platform-profiles")
all_channels = get("/payment-channels")
all_types = get("/client-types")

def find_id(lst, name_key, name):
    item = next((x for x in lst if x[name_key].lower() == name.lower()), None)
    return item["id"] if item else None

# ─── Contracts ───
contracts_data = [
    {
        "contract_name": "WP-WD-Pest-Ryan-Numan",
        "date": "2026-01-15", "deadline": "2026-02-15",
        "client": "Ryan Thompson", "bdo": "Numan", "platform": "Upwork",
        "estimated_revenue": 800, "status": "Completed",
        "workspace": "Pest Control", "notes": "WordPress website redesign for pest control company"
    },
    {
        "contract_name": "SEO-GreenLeaf-Shahab",
        "date": "2026-01-20", "deadline": "2026-03-20",
        "client": "Sarah Mitchell", "bdo": "Shahab", "platform": "LinkedIn",
        "estimated_revenue": 1200, "status": "In Progress",
        "workspace": "SEO Projects", "notes": "6-month SEO retainer for GreenLeaf Digital"
    },
    {
        "contract_name": "WP-Ecom-TechVista-Ali",
        "date": "2026-02-01", "deadline": "2026-03-01",
        "client": "Ahmed Khan", "bdo": "Ali", "platform": "Direct",
        "estimated_revenue": 2500, "status": "Completed",
        "workspace": "E-commerce", "notes": "WooCommerce store with payment gateway integration"
    },
    {
        "contract_name": "SM-Management-BrightPath",
        "date": "2026-02-10", "deadline": "2026-04-10",
        "client": "Jessica Liu", "bdo": "Shahab", "platform": "Upwork",
        "estimated_revenue": 1500, "status": "In Progress",
        "workspace": "Social Media", "notes": "Social media management and content creation"
    },
    {
        "contract_name": "WP-LawFirm-Brown-Numan",
        "date": "2026-02-15", "deadline": "2026-03-25",
        "client": "Michael Brown", "bdo": "Numan", "platform": "Upwork",
        "estimated_revenue": 950, "status": "In Progress",
        "workspace": "Legal", "notes": "Law firm website with case management portal"
    },
    {
        "contract_name": "MVP-App-ParkTech-Ali",
        "date": "2026-02-20", "deadline": "2026-04-20",
        "client": "David Park", "bdo": "Ali", "platform": "LinkedIn",
        "estimated_revenue": 3500, "status": "In Progress",
        "workspace": "App Development", "notes": "React Native MVP for SaaS product"
    },
    {
        "contract_name": "Shopify-FashionHub-Shahab",
        "date": "2026-03-01", "deadline": "2026-04-01",
        "client": "Emma Wilson", "bdo": "Shahab", "platform": "Fiverr",
        "estimated_revenue": 600, "status": "In Progress",
        "workspace": "E-commerce", "notes": "Shopify store setup and theme customization"
    },
    {
        "contract_name": "Logo-Brand-MXDesign-Numan",
        "date": "2026-01-05", "deadline": "2026-01-25",
        "client": "Carlos Reyes", "bdo": "Numan", "platform": "Fiverr",
        "estimated_revenue": 350, "status": "Completed",
        "workspace": "Branding", "notes": "Logo design and brand guidelines"
    },
    {
        "contract_name": "LMS-EduTrain-Ali",
        "date": "2026-03-10", "deadline": "2026-05-10",
        "client": "Fatima Hassan", "bdo": "Ali", "platform": "Direct",
        "estimated_revenue": 4000, "status": "In Progress",
        "workspace": "LMS", "notes": "Custom Learning Management System"
    },
    {
        "contract_name": "VideoEdit-RichMedia-Shahab",
        "date": "2026-03-05", "deadline": "2026-03-28",
        "client": "Tom Richards", "bdo": "Shahab", "platform": "Upwork",
        "estimated_revenue": 450, "status": "In Progress",
        "workspace": "Video", "notes": "YouTube channel video editing package"
    },
    {
        "contract_name": "SEO-Audit-Pest-Numan",
        "date": "2026-03-15", "deadline": "2026-04-15",
        "client": "Ryan Thompson", "bdo": "Numan", "platform": "Direct",
        "estimated_revenue": 500, "status": "In Progress",
        "workspace": "SEO Projects", "notes": "Follow-up SEO audit and optimization"
    },
    {
        "contract_name": "WP-Maintenance-GreenLeaf",
        "date": "2026-02-25", "deadline": "2026-03-25",
        "client": "Sarah Mitchell", "bdo": "Shahab", "platform": "LinkedIn",
        "estimated_revenue": 300, "status": "On Hold",
        "workspace": "Maintenance", "notes": "Monthly WordPress maintenance contract",
        "delay_reason": "Client requested pause until April"
    },
]

contract_ids = []
for c in contracts_data:
    body = {
        "contract_name": c["contract_name"],
        "date": c["date"],
        "deadline": c["deadline"],
        "client_id": find_id(all_clients, "name", c["client"]),
        "bdo_id": find_id(all_bdos, "name", c["bdo"]),
        "platform_id": find_id(all_platforms, "name", c["platform"]),
        "estimated_revenue": c["estimated_revenue"],
        "status": c["status"],
        "workspace": c.get("workspace", ""),
        "notes": c.get("notes", ""),
        "delay_reason": c.get("delay_reason", ""),
        "client_type_id": find_id(all_types, "name", random.choice(["Fixed", "Hourly", "Retainer"])),
        "payment_channel_id": find_id(all_channels, "name", random.choice(["Payoneer", "Wise", "Bank Transfer"])),
    }
    result = post("/contracts", body)
    contract_ids.append(result.get("id"))
print(f"[OK] {len(contracts_data)} Contracts added")

# Reload contracts for payments
all_contracts = get("/contracts")

# ─── Payments ───
payments_data = [
    # Ryan's completed contract - fully paid
    {"contract": "WP-WD-Pest-Ryan-Numan", "amount": 400, "date": "2026-01-25", "notes": "First milestone"},
    {"contract": "WP-WD-Pest-Ryan-Numan", "amount": 400, "date": "2026-02-15", "notes": "Final payment"},
    # TechVista - fully paid
    {"contract": "WP-Ecom-TechVista-Ali", "amount": 1000, "date": "2026-02-10", "notes": "Upfront payment"},
    {"contract": "WP-Ecom-TechVista-Ali", "amount": 1500, "date": "2026-03-01", "notes": "Completion payment"},
    # Logo - fully paid
    {"contract": "Logo-Brand-MXDesign-Numan", "amount": 350, "date": "2026-01-20", "notes": "Full payment"},
    # Partial payments on active contracts
    {"contract": "SEO-GreenLeaf-Shahab", "amount": 400, "date": "2026-02-20", "notes": "Month 1 retainer"},
    {"contract": "SEO-GreenLeaf-Shahab", "amount": 400, "date": "2026-03-20", "notes": "Month 2 retainer"},
    {"contract": "SM-Management-BrightPath", "amount": 500, "date": "2026-03-01", "notes": "First month"},
    {"contract": "WP-LawFirm-Brown-Numan", "amount": 475, "date": "2026-03-01", "notes": "50% upfront"},
    {"contract": "MVP-App-ParkTech-Ali", "amount": 1500, "date": "2026-03-01", "notes": "Phase 1 payment"},
    {"contract": "Shopify-FashionHub-Shahab", "amount": 300, "date": "2026-03-10", "notes": "50% deposit"},
    {"contract": "VideoEdit-RichMedia-Shahab", "amount": 200, "date": "2026-03-15", "notes": "Advance payment"},
    {"contract": "LMS-EduTrain-Ali", "amount": 1000, "date": "2026-03-15", "notes": "25% upfront"},
]

for p in payments_data:
    contract = next((c for c in all_contracts if c["contract_name"] == p["contract"]), None)
    if contract:
        body = {
            "contract_id": contract["id"],
            "amount": p["amount"],
            "payment_date": p["date"],
            "notes": p.get("notes", ""),
            "payment_channel_id": find_id(all_channels, "name", random.choice(["Payoneer", "Wise", "Bank Transfer"])),
        }
        post("/payments", body)
print(f"[OK] {len(payments_data)} Payments added")

print("\nAll dummy data populated! Refresh your browser.")
