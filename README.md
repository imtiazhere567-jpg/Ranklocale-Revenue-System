# Ranklocale Revenue & Client Management System

A professional, full-stack financial reporting and client management system. Optimized for fast deployment on **Vercel** with a **Supabase (PostgreSQL)** backend.

## 🚀 Key Features
- **Advanced Dashboard**: Real-time sales, recovery, and pending debt analytics.
- **Client Management**: Track multiple contracts, platforms, and payment channels.
- **Milestone Tracking**: Automate payment logging via scheduled milestones.
- **Production Ready**: Optimized for Vercel + Supabase out-of-the-box.

## 🛠️ Setup Instructions

### 1. Cloud Database (Supabase)
1. Create a project at [Supabase.com](https://supabase.com).
2. Grab your connection string from **Project Settings > Database**.
3. (Optional) Run `python migrate_data.py` locally to upload your existing data.

### 2. Deployment (Vercel)
1. Push this repository to your GitHub account.
2. Import the project into **Vercel**.
3. Add your `DATABASE_URL` as an Environment Variable in the Vercel dashboard.

## 📝 Technologies
- **Backend**: Python (Flask)
- **Database**: PostgreSQL (Supabase) / psycopg2
- **Frontend**: Vanilla JS / HTML5 / CSS3 (Optimized for modern browsers)
- **deployment**: Vercel Serverless Functions

---
*Created for Ranklocale — Optimized for growth.*
