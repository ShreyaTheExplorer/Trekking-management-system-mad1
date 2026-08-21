# Trekking Management System

A Python Flask-based web application for managing adventure trails, trek bookings, guide assignments, and participant rosters. Built using Flask Blueprints, WTForms, SQLAlchemy, and SQLite.

## Table of Contents
- [Features](#features)
  - [Trekkers](#1-trekkers)
  - [Trek Staff / Guides](#2-trek-staff--guides)
  - [System Administrators](#3-system-administrators)
- [Project Tech Stack](#project-tech-stack)
- [Directory Structure](#directory-structure)
- [Installation and Setup](#installation-and-setup)
- [Seeding Sample Data](#seeding-sample-data)
- [Running the Application](#running-the-application)
- [Running the Test Suite](#running-the-test-suite)
- [Demo video Link](https://drive.google.com/file/d/1sDZbLjsdsHr8N4RnJFpcFbApjoN5kQ_F/view?usp=sharing)

---

## Features

### 1. Trekkers
- **Register and Log In**: Create local email/password accounts.
- **Browse Open Treks**: Filter treks by location, difficulty (Easy, Moderate, Hard), month, or season.
- **Smart Recommendations**: View personalized recommendations under "Suggested for you" based on previous bookings (same difficulty or location).
- **Trek Details & Booking**: View detailed description, cover image, slots, price, and book a trek.
- **Booking Roster & Cancellations**: Manage active bookings and cancel them, which automatically returns slots back to the trek pool.

### 2. Trek Staff / Guides
- **Staff Registration**: Register with a profile containing experience years, certification, and bio. Requires admin approval before login.
- **Assigned Dashboard**: View all assigned treks and current participant counts.
- **Slot and Status Management**: Edit available slots (never lower than the number of already booked people) and status.
- **Trek Life Cycle Actions**: Mark a trek as started (**Closed** for bookings) or **Completed** (which automatically graduates all participants' booking statuses to Completed).
- **Roster view**: Check full participant profiles, contact information, and booking states.

### 3. System Administrators
- **Core Statistics**: View overall metrics (total treks, open treks, active bookings, pending staff).
- **Trek Management (CRUD)**: Create, edit, and delete treks (including managing slots and assigning approved staff guides).
- **Staff Approvals**: Approve or reject pending staff registrations. Approving a guide automatically issues a unique, sequential Staff ID (e.g., `STF-00001`) used for authentication.
- **Blacklist Control**: Blacklist or reinstate trekkers or staff members immediately to lock them out of the system.

---

## Project Tech Stack
- **Backend Framework**: Flask 3.1.3
- **ORM / Database**: SQLAlchemy 2.0.51 & Flask-SQLAlchemy 3.1.1 (SQLite)
- **Forms and Validation**: WTForms 3.2.2 & Flask-WTF 1.3.0
- **User Authentication**: Flask-Login 0.6.3
- **OAuth Authentication**: Authlib 1.7.2
- **Password Security**: Werkzeug 3.1.8 (bcrypt/scrypt hashing)

---

## Directory Structure
```
Trek_Mnmt_app/
├── app.py                  # Application factory configuration & CLI commands
├── extensions.py           # Flask extension initializations (db, login_manager, oauth)
├── config.py               # Application configuration parameters & environment settings
├── models.py               # Database schemas and business helper functions
├── utils.py                # Authorization decorators (admin_required, staff_required, etc.)
├── seed.py                 # Idempotent admin user initialization script
├── seed_demo_data.py       # Full database seeder (seeds Admin, Trekkers, Staff, Treks, and Bookings)
├── test_flows.py           # Unit tests checking end-to-end user journeys
├── requirements.txt        # Python dependency manifest
├── static/                 # Styles, images, and Javascript assets
│   ├── css/
│   │   └── style.css
│   └── images/
└── templates/              # HTML Templates (Jinja2)
    ├── admin/              # Admin pages
    ├── auth/               # Login, register, and status checks
    ├── staff/              # Staff portal
    ├── user/               # Trekker pages
    ├── macros/             # Reusable UI macros
    └── base.html           # Master layout template
```

---

## Installation and Setup

### Prerequisites
- Python 3.10+ installed on your system.

### Steps
1. **Clone or Navigate to the Directory**:
   ```bash
   cd c:\Users\VICTUS\OneDrive\Desktop\Trek_Mnmt_app
   ```

2. **Create and Activate a Virtual Environment**:
   ```bash
   # Windows PowerShell
   python -m venv venv
   .\venv\Scripts\activate
   ```

3. **Install Dependencies**:
   ```bash
   .\venv\Scripts\pip.exe install -r requirements.txt
   ```

---

## Seeding Sample Data

To set up a fresh database with realistic sample treks, staff, trekkers, and bookings, execute the seeder script:
```bash
.\venv\Scripts\python.exe seed_demo_data.py
```
This script will initialize `app.db` in the `instance` folder, seed 1 admin, 3 staff guides, 3 trekkers, 8 treks across different seasons, and several sample bookings.

---

## Running the Application

To run the Flask development server locally:
```bash
.\venv\Scripts\python.exe app.py
```
The server will start at `http://127.0.0.1:5000/`. Open this URL in your web browser.

---

## Running the Test Suite

To run the end-to-end integration test suite and verify system rules:
```bash
.\venv\Scripts\python.exe -m unittest test_flows.py
```
This validates filters, overbooking prevention, booking cancellations, and blacklist validation constraints.
