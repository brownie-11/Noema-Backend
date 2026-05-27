#!/usr/bin/env python3
"""
fix_hashes.py — One-time migration script
==========================================
Run this ONCE on your Railway machine (or locally against the db) to convert
all argon2 hashes to bcrypt.  After this, logins work normally.

Usage:
    DATABASE_URL=<your_railway_url> ADMIN_PASSWORD=<password> python fix_hashes.py

Or locally with the SQLite file:
    python fix_hashes.py
"""
import os
import sys

# Allow running from repo root without installing the package
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.database import engine, SessionLocal, init_db
from backend.models import User
from backend.utils.security import verify_password, hash_password, needs_rehash


def migrate():
    init_db()
    db = SessionLocal()
    total = 0
    fixed = 0
    skipped = 0
    failed = 0

    try:
        users = db.query(User).all()
        total = len(users)
        print(f"Found {total} user(s) in database.\n")

        for user in users:
            if not user.password_hash:
                print(f"  SKIP  @{user.username} — no hash stored")
                skipped += 1
                continue

            if not needs_rehash(user.password_hash):
                print(f"  OK    @{user.username} — already bcrypt")
                skipped += 1
                continue

            # argon2 hash detected — need the plaintext password to re-hash
            # For the admin account we can read from env var
            env_pass = os.getenv("ADMIN_PASSWORD", "")
            if user.role.value == "admin" and env_pass:
                if verify_password(env_pass, user.password_hash):
                    user.password_hash = hash_password(env_pass)
                    db.commit()
                    print(f"  FIXED @{user.username} (admin) — argon2 → bcrypt")
                    fixed += 1
                else:
                    print(f"  FAIL  @{user.username} — ADMIN_PASSWORD env var doesn't match stored hash")
                    failed += 1
            else:
                print(f"  SKIP  @{user.username} — argon2 hash but no plaintext available")
                print(f"        They will be prompted to reset password on next login.")
                skipped += 1

    finally:
        db.close()

    print(f"\n── Summary ──────────────────────")
    print(f"  Total:   {total}")
    print(f"  Fixed:   {fixed}")
    print(f"  Skipped: {skipped}")
    print(f"  Failed:  {failed}")
    print()
    if fixed > 0:
        print("✓ Migration complete. Deploy the fixed backend and logins will work.")
    else:
        print("No hashes migrated. Make sure ADMIN_PASSWORD env var is set correctly.")


if __name__ == "__main__":
    migrate()
