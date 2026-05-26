# Noema — Backend

> A living philosophy platform. Thought persists. Users persist. Nothing is forgotten.

---

## Stack

| Layer | Technology |
|---|---|
| Runtime | Python 3.11+ |
| Framework | FastAPI |
| Database | SQLite (via SQLAlchemy ORM) |
| Auth | JWT (python-jose) + bcrypt (passlib) |
| Email | SMTP (async, non-blocking) |

---

## Project Structure

```
noema_backend/
│
├── backend/
│   ├── main.py             ← FastAPI app, startup, seeding
│   ├── config.py           ← Settings from .env
│   ├── database.py         ← SQLAlchemy engine + session
│   ├── models.py           ← ORM models (User, Submission, ThoughtNode, ThoughtConnection)
│   ├── schemas.py          ← Pydantic request/response schemas
│   ├── auth.py             ← authenticate_user helper
│   ├── dependencies.py     ← FastAPI dependency injection (get_current_user, get_current_admin)
│   │
│   ├── routes/
│   │   ├── auth_routes.py  ← POST /signup  POST /login  GET /me  POST /logout
│   │   ├── users.py        ← GET /users/me/submissions  GET /users/{id}
│   │   ├── submissions.py  ← POST /submit-thought  GET /submissions/public
│   │   ├── thought_nodes.py← GET /constellation  PATCH /constellation/nodes/{id}/position
│   │   └── admin.py        ← All /admin/* endpoints
│   │
│   └── utils/
│       ├── security.py     ← hash_password / verify_password
│       ├── token.py        ← create_access_token / decode_access_token
│       └── email_service.py← SMTP submission notification
│
├── requirements.txt
├── .env.example
└── README.md
```

---

## Quick Start

### 1. Install dependencies

```bash
cd noema_backend
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env — at minimum set SECRET_KEY and ADMIN_EMAIL
```

Generate a secure secret key:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### 3. Run the server

```bash
uvicorn backend.main:app --reload --port 8000
```

The API is now live at **http://localhost:8000**

Interactive docs: **http://localhost:8000/docs**

On first boot, the server automatically:
- Creates all database tables
- Seeds the 12 curator base constellation nodes (immutable)

### 4. Create your first admin

```bash
python - <<'EOF'
from backend.database import SessionLocal, init_db
from backend.models import User, UserRole
from backend.utils.security import hash_password
from datetime import datetime

init_db()
db = SessionLocal()
admin = User(
    username="william",
    email="admin@noema.com",
    password_hash=hash_password("your-strong-password"),
    role=UserRole.admin,
    last_login=datetime.utcnow(),
)
db.add(admin)
db.commit()
print(f"Admin created: @{admin.username}")
db.close()
EOF
```

---

## API Reference

### Authentication

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/signup` | — | Create account → returns JWT |
| `POST` | `/login` | — | Login → returns JWT |
| `GET` | `/me` | Bearer | Current user info |
| `POST` | `/logout` | Bearer | Invalidate session (client-side) |

**Signup**
```json
POST /signup
{
  "username": "elara",
  "email": "elara@mind.com",
  "password": "atleast8chars"
}
```

**Login**
```json
POST /login
{
  "email": "elara@mind.com",
  "password": "atleast8chars"
}
```

Both return:
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "user": { "id": 1, "username": "elara", "email": "...", "role": "user", ... }
}
```

---

### Submissions

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/submit-thought` | Bearer | Submit a thought fragment |
| `GET` | `/submissions/public` | — | All approved thoughts (Explore Minds) |
| `GET` | `/submissions/public?category=dreams` | — | Filter by category |
| `GET` | `/users/me/submissions` | Bearer | Your own submissions |

**Submit a thought**
```json
POST /submit-thought
Authorization: Bearer <token>

{
  "content": "The fears that resist naming are the most sovereign.",
  "title": "The Unnamed Fear",
  "category": "fear"
}
```

Returns the submission with `status: "pending"`. Admin notification email is sent automatically.

---

### Constellation

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `GET` | `/constellation` | — | All nodes + connections |
| `GET` | `/constellation/nodes` | — | All nodes |
| `GET` | `/constellation/connections` | — | All edges |
| `PATCH` | `/constellation/nodes/{id}/position` | Bearer | Save dragged position |

**Save node position**
```json
PATCH /constellation/nodes/3/position
Authorization: Bearer <token>

{ "position_x": 0.42, "position_y": 0.71 }
```

---

### Admin

All `/admin/*` endpoints require a user with `role: "admin"`.

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/admin/users` | List all users |
| `DELETE` | `/admin/users/{id}` | Deactivate user |
| `GET` | `/admin/submissions` | All submissions |
| `GET` | `/admin/submissions?status_filter=pending` | Filter by status |
| `POST` | `/admin/approve/{id}` | Approve submission |
| `POST` | `/admin/reject/{id}` | Reject submission |
| `DELETE` | `/admin/submissions/{id}` | Delete spam |
| `POST` | `/admin/create-node` | Add thought node |
| `POST` | `/admin/connect-nodes` | Link two nodes |
| `DELETE` | `/admin/nodes/{id}` | Remove non-base node |
| `DELETE` | `/admin/connections/{id}` | Remove an edge |
| `POST` | `/admin/promote/{submission_id}` | Approve + create node in one step |

**Approve and create a node from a submission**
```
POST /admin/promote/7
Authorization: Bearer <admin-token>
```

---

## Database Schema

```
users
  id, username*, email*, password_hash, role, is_active, created_at, last_login

submissions
  id, user_id → users, title, content, category, status, admin_note,
  created_at, reviewed_at, thought_node_id → thought_nodes

thought_nodes
  id, title, content, category, author, position_x, position_y, node_radius,
  hex_color, is_base, created_by → users, created_at

thought_connections
  id, source_node_id → thought_nodes, target_node_id → thought_nodes,
  connection_type, created_at
```

**Connection types:** `contradiction`, `continuation`, `inspiration`,
`emotional resonance`, `existential conflict`, `memory link`, `expansion`

---

## Email Setup (Gmail)

1. Enable **2-Step Verification** on your Google account
2. Generate an **App Password** at myaccount.google.com/apppasswords
3. Set in `.env`:

```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=yourname@gmail.com
SMTP_PASS=xxxx xxxx xxxx xxxx   # App password (spaces OK)
ADMIN_EMAIL=yourname@gmail.com
```

Email is fire-and-forget — a failed send never blocks or errors the API.

---

## Connecting the Frontend (noema_v5.html)

Replace the localStorage-only calls with real API calls. Example pattern:

```javascript
const API = 'http://localhost:8000';
let token = localStorage.getItem('noema_token');

// SIGNUP
async function signup() {
  const res = await fetch(`${API}/signup`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, email, password })
  });
  const data = await res.json();
  if (res.ok) {
    token = data.access_token;
    localStorage.setItem('noema_token', token);
    currentUser = data.user.username;
    updateAuthUI();
  }
}

// SUBMIT THOUGHT
async function sendFragment() {
  const res = await fetch(`${API}/submit-thought`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({ content: thought, title, category })
  });
}

// LOAD CONSTELLATION
async function loadConstellation() {
  const res = await fetch(`${API}/constellation`);
  const { nodes, connections } = await res.json();
  // nodes and connections map directly to archNodes / archEdges
}

// SAVE NODE POSITION (on drag end)
async function saveNodePosition(nodeId, x, y) {
  await fetch(`${API}/constellation/nodes/${nodeId}/position`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({ position_x: x, position_y: y })
  });
}

// EXPLORE MINDS — approved submissions
async function loadPublicThoughts(category = 'all') {
  const url = category === 'all'
    ? `${API}/submissions/public`
    : `${API}/submissions/public?category=${category}`;
  const res = await fetch(url);
  return res.json(); // array of approved submissions
}
```

---

## Security Notes

- Passwords are hashed with **bcrypt** (cost factor 12) — never stored in plain text
- JWT tokens are signed with HS256 — rotate `SECRET_KEY` periodically
- SQL injection is impossible — SQLAlchemy ORM uses parameterised queries
- Admin routes require role check on every request (not just token presence)
- Base constellation nodes (`is_base=True`) cannot be deleted via any endpoint
- Email credentials are read from `.env` only — never hardcoded

---

## Production Checklist

- [ ] Set a real `SECRET_KEY` (32+ random bytes)
- [ ] Set `DEBUG=false`
- [ ] Replace SQLite with PostgreSQL (`DATABASE_URL=postgresql://...`)
- [ ] Add HTTPS (reverse proxy via Nginx or Caddy)
- [ ] Restrict `ALLOWED_ORIGINS` to your actual domain
- [ ] Add rate limiting (e.g. `slowapi`)
- [ ] Implement token denylist for true logout (Redis)
- [ ] Set up log aggregation
