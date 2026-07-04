"""
Noema Backend — main.py
"""
import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.database import init_db, SessionLocal
from backend.routes import auth, users, submissions, constellation, admin, thoughts

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger("noema")


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("Noema starting up…")
    init_db()
    _seed_base_nodes()
    _ensure_admin()
    log.info("Noema is alive.")
    yield
    log.info("Noema shutting down.")


def _ensure_admin():
    """
    Smart admin setup:
    - First run: create admin from env vars
    - Subsequent runs: only fix hash if it is corrupted or password changed
    - Never re-hashes a valid working hash (that was breaking login on restart)
    """
    from backend.models import User, Role
    from backend.utils.security import hash_password, verify_password
    from datetime import datetime

    email    = os.getenv("ADMIN_EMAIL",    "").strip()
    username = os.getenv("ADMIN_USERNAME", "william").strip()
    password = os.getenv("ADMIN_PASSWORD", "").strip()

    if not email or not password:
        log.warning("Set ADMIN_EMAIL + ADMIN_PASSWORD env vars to create/repair admin.")
        return

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()

        if not user:
            # First run — create admin
            user = User(
                username=username,
                email=email,
                password_hash=hash_password(password),
                role=Role.admin,
                last_login=datetime.utcnow(),
            )
            db.add(user)
            db.commit()
            log.info("Admin created: @%s", username)
            return

        changed = False

        # Check if hash is valid bcrypt format
        hash_valid = (
            user.password_hash and
            (user.password_hash.startswith("$2b$") or
             user.password_hash.startswith("$2a$"))
        )

        if not hash_valid:
            # Hash is corrupted — fix it
            user.password_hash = hash_password(password)
            changed = True
            log.info("Admin hash was corrupted — repaired for @%s.", username)
        elif not verify_password(password, user.password_hash):
            # Valid hash but wrong password (env var changed) — update it
            user.password_hash = hash_password(password)
            changed = True
            log.info("Admin password updated for @%s.", username)
        else:
            log.info("Admin @%s is healthy — no hash changes needed.", username)

        # Ensure role and active are correct
        if user.role != Role.admin:
            user.role = Role.admin
            changed = True
        if not user.is_active:
            user.is_active = True
            changed = True

        if changed:
            db.commit()

    except Exception as e:
        db.rollback()
        log.error("Admin setup failed: %s", e)
    finally:
        db.close()


def _seed_base_nodes():
    from backend.models import ThoughtNode, ThoughtConnection, ConnectionType

    BASE = [
        ("The Watcher Within",        "consciousness","#c8a97e","Who observes the observer? At the edge of introspection lies an infinite recursion — the eye that cannot see itself.",.50,.44,24),
        ("The Permission of Being",   "existence",    "#c8a07e","Nobody asked to be here. And yet here we are, inventing reasons to stay, to build, to leave marks on a world that will outlast our reasons.",.22,.28,18),
        ("Simultaneity of Grief",     "time",         "#8bb5c8","Past and present collapse in loss. The person grieving now is also the child who did not yet know grief was already on its way.",.78,.26,19),
        ("Cartography of Attachment", "love",         "#a07ec8","To love is to memorize someone. Their particular weight of silence. A geography that becomes your own internal landscape.",.15,.62,16),
        ("Architecture of Sleep",     "dreams",       "#7ec8a0","Dreams build cities with impossible geometry. Every door opens into a different era. We forget the blueprints at the moment of waking.",.38,.78,17),
        ("Palimpsest",                "memory",       "#8bb5c8","Memory is not storage. It is constant rewriting — each recall leaves a new impression over the last, until the original is only its own ghost.",.72,.72,15),
        ("The Unnamed Fear",          "fear",         "#c87e8a","The fears that resist naming are the most sovereign. They do not require objects. They are the weather of the mind before the storm arrives.",.86,.50,14),
        ("Language Before Thought",   "consciousness","#c8a97e","Does the word precede the thought, or does the thought precede the word? Perhaps there are ideas that exist only in the silence between.",.30,.16,16),
        ("The Weight of the Present", "time",         "#8bb5c8","The present moment is the only real thing, yet it vanishes the moment you name it. We live permanently in a tense that does not exist.",.64,.13,17),
        ("Void as Foundation",        "existence",    "#c8a07e","Perhaps the void is not the absence of meaning but the precondition for it. Emptiness is what makes a vessel capable of holding anything.",.88,.74,13),
        ("The Myth of Closure",       "memory",       "#8bb5c8","Closure is a story we tell ourselves. Grief, love, loss — they do not close. They simply find new rooms to inhabit inside us.",.50,.84,14),
        ("Consciousness as Stranger", "consciousness","#c8a97e","What if awareness is not native to the body but a visitor — arriving, looking around, and gradually forgetting it was ever anywhere else?",.08,.38,14),
    ]
    EDGES = [
        (0,7,"expansion"),(0,1,"inspiration"),(0,11,"continuation"),
        (1,9,"expansion"),(2,5,"memory_link"),(2,8,"continuation"),
        (3,6,"emotional_resonance"),(3,10,"memory_link"),(4,5,"inspiration"),
        (5,10,"expansion"),(6,9,"existential_conflict"),(7,8,"contradiction"),
        (8,2,"expansion"),(11,0,"continuation"),(4,3,"emotional_resonance"),
        (1,11,"inspiration"),(6,2,"contradiction"),
    ]
    db = SessionLocal()
    try:
        if db.query(ThoughtNode).filter(ThoughtNode.is_base == True).count() > 0:  # noqa
            return
        nodes = []
        for title,cat,hex_,body,x,y,r in BASE:
            n = ThoughtNode(
                title=title, content=body, category=cat,
                hex_color=hex_, position_x=x, position_y=y,
                node_radius=r, is_base=True, author="William · The Architect",
            )
            db.add(n); nodes.append(n)
        db.flush()
        for a,b,ct in EDGES:
            db.add(ThoughtConnection(
                source_node_id=nodes[a].id,
                target_node_id=nodes[b].id,
                connection_type=ConnectionType(ct),
            ))
        db.commit()
        log.info("Seeded %d base nodes.", len(nodes))
    except Exception as e:
        db.rollback()
        log.warning("Node seeding skipped: %s", e)
    finally:
        db.close()


app = FastAPI(title="Noema API", version="2.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(submissions.router)
app.include_router(constellation.router)
app.include_router(admin.router)
app.include_router(thoughts.router)


@app.get("/health")
def health():
    return {"status": "alive", "version": "2.0.0"}

@app.get("/")
def root():
    return {"status": "alive", "platform": "Noema"}
