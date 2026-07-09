"""
seed.py — one-off script alternative to `flask --app app seed-db`.
Run with: python seed.py
Safe to re-run — seed_admin() is idempotent.
"""

from app import create_app
from extensions import db
from models import seed_admin

app = create_app()

with app.app_context():
    db.create_all()
    admin = seed_admin()
    print(f"Database ready. Admin user '{admin.username}' is set up.")