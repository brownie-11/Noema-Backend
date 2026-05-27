"""
Standalone admin creation script.
Run once if you need to create an admin manually:

    python create_admin.py

Or set ADMIN_EMAIL + ADMIN_PASSWORD env vars and the server seeds the admin
automatically on first startup via _seed_admin() in main.py.
"""
import os
from backend.database import SessionLocal, init_db
from backend.models import User, UserRole
from backend.utils.security import hash_password
from datetime import datetime

USERNAME = os.getenv("ADMIN_USERNAME", "william")
EMAIL    = os.getenv("ADMIN_EMAIL",    "")
PASSWORD = os.getenv("ADMIN_PASSWORD", "")

if not EMAIL or not PASSWORD:
    print("ERROR: Set ADMIN_EMAIL and ADMIN_PASSWORD environment variables first.")
    print("  export ADMIN_EMAIL=your@email.com")
    print("  export ADMIN_PASSWORD=your-strong-password")
    exit(1)

init_db()
db = SessionLocal()

existing = db.query(User).filter(User.email == EMAIL).first()
if existing:
    if existing.role != UserRole.admin:
        existing.role = UserRole.admin
        db.commit()
        print(f"Existing user @{existing.username} promoted to admin.")
    else:
        print(f"Admin @{existing.username} already exists.")
else:
    admin = User(
        username=USERNAME,
        email=EMAIL,
        password_hash=hash_password(PASSWORD),
        role=UserRole.admin,
        last_login=datetime.utcnow(),
    )
    db.add(admin)
    db.commit()
    print(f"Admin created: @{admin.username} ({EMAIL})")

db.close()
