# Installation & Quickstart Guide

This document describes how to set up and run the Apex Credit application locally.

---

## 1. Backend Setup (FastAPI)

### Prerequisites
- Python 3.9+
- SQLite (included by default)

### Setup Steps
1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Seed the database and start the server:
   ```bash
   python verify_db.py
   python -m uvicorn app.main:app --reload --port 8000
   ```

---

## 2. Frontend Setup (React)

### Prerequisites
- Node.js (v18+)
- npm (v9+)

### Setup Steps
1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install Node packages:
   ```bash
   npm install
   ```
3. Start the dev server:
   ```bash
   npm run dev
   ```
4. Access the portal at `http://localhost:5173`.

---

## 3. Seed Credentials

Use these preloaded credentials to access different dashboard perspectives:
- **Applicant**: `applicant@demo.com` | `Password123@`
- **Underwriter**: `underwriter@demo.com` | `Password123@`
- **Credit Manager**: `manager@demo.com` | `Password123@`
- **Auditor**: `auditor@demo.com` | `Password123@`
