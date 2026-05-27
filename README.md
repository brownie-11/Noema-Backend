# Noema Backend — Fix & Deploy Guide

## What was broken and what's fixed

| Bug | Root Cause | Fix |
|-----|-----------|-----|
| Login → "wrong credentials" | Password hashed with **argon2** on signup, but `security.py` only checked **bcrypt** — so every login failed | `security.py` now detects and verifies argon2 hashes, then auto-upgrades to bcrypt on first successful login |
| Railway crashes on startup | `bcrypt==3.2.2` conflicts with `passlib 1.7.4` on Python 3.11+ | Pinned `bcrypt==4.0.1` + added `argon2-cffi` |
| TablePlus shows nothing | Railway uses `postgres://` prefix — SQLAlchemy needs `postgresql://` | `config.py` rewrites the prefix automatically |
| Reset password 422 error | `auth_routes.py` used `Query` without importing it | Added `from fastapi import Query` |
| Admin hash repair ran but had wrong logic | `_reset_admin_password()` checked `$2b$` and skipped repair when hash was argon2 | New `_repair_admin_hash()` uses `needs_rehash()` from security module |

---

## Railway deployment steps

### 1. Set environment variables in Railway dashboard

```
DATABASE_URL        = (auto-set by Railway PostgreSQL plugin)
SECRET_KEY          = (run: openssl rand -hex 32)
ADMIN_EMAIL         = lampteywilliam48@gmail.com
ADMIN_USERNAME      = william
ADMIN_PASSWORD      = (your real password — same one you used when you signed up)
ALLOWED_ORIGINS     = https://your-frontend-domain.com,http://localhost:3000
```

### 2. Replace these files in your repo

Replace every file in `backend/` with the fixed versions from this package.
Replace `requirements.txt` and `Procfile` at the repo root.

### 3. Deploy

Push to Railway. On startup it will:
1. Create all tables if they don't exist
2. Seed the 12 base constellation nodes (skipped if already seeded)
3. Create admin account (skipped if email already exists)
4. **Repair the argon2 hash → bcrypt** using your `ADMIN_PASSWORD` env var

After one successful startup, login will work immediately.

### 4. Verify in TablePlus

Connect with your Railway PostgreSQL credentials:
- Host: from Railway Variables tab → `PGHOST`
- Port: `PGPORT`  
- Database: `PGDATABASE`
- User: `PGUSER`
- Password: `PGPASSWORD`

You should see tables: `users`, `submissions`, `thought_nodes`, `thought_connections`

---

## API endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | /signup | None | Create account |
| POST | /login | None | Login → JWT |
| GET | /me | User | Current user |
| POST | /submit-thought | User | Submit fragment |
| GET | /submissions/public | None | All approved thoughts |
| GET | /constellation | None | Full graph (nodes + edges) |
| GET | /admin/submissions | Admin | All submissions |
| POST | /admin/approve/{id} | Admin | Approve submission |
| POST | /admin/promote/{id} | Admin | Approve + place as node |
| POST | /admin/create-node | Admin | Create node directly |
| POST | /admin/connect-nodes | Admin | Connect two nodes |

Full docs: `https://your-railway-url.up.railway.app/docs`

---

## Emergency password reset (if needed)

Set `RESET_SECRET` env var to any secret string, then call:

```
POST https://your-api.up.railway.app/reset-password
  ?email=lampteywilliam48@gmail.com
  &new_password=YourNewPassword
  &reset_token=<RESET_SECRET>
```
