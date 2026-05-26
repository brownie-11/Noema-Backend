import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.config import settings
from backend.database import init_db
from backend.routes import auth_routes, users, submissions, thought_nodes, admin

logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("noema")


# ── Startup / Shutdown ────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Noema backend starting — initialising database…")
    init_db()
    _seed_base_nodes()
    _seed_admin() 
    logger.info("Database ready. Noema is alive.")
    yield
    logger.info("Noema backend shutting down.")


def _seed_base_nodes():
    """
    Seed the 12 curator base nodes on first run.
    These are immutable and map exactly to the archNodes in the frontend.
    """
    from backend.database import SessionLocal
    from backend.models import ThoughtNode, ThoughtConnection, ConnectionType

    BASE_NODES = [
        {"title": "The Watcher Within", "cat": "consciousness", "hex": "#c8a97e",
         "body": "Who observes the observer? At the edge of introspection lies an infinite recursion — the eye that cannot see itself.", "x": .22, "y": .35, "r": 20},
        {"title": "Dissolution of Self", "cat": "existence", "hex": "#c8a07e",
         "body": "There are moments — deep meditation, grief, ecstasy — when the boundary between self and world dissolves.", "x": .58, "y": .45, "r": 18},
        {"title": "Simultaneity of Grief", "cat": "time", "hex": "#8bb5c8",
         "body": "Past and present collapse in loss. The person grieving now is also the child who did not yet know grief was already on its way.", "x": .78, "y": .26, "r": 19},
        {"title": "Cartography of Attachment", "cat": "love", "hex": "#a07ec8",
         "body": "To love is to memorize someone. Their particular weight of silence. A geography that becomes your own internal landscape.", "x": .15, "y": .62, "r": 16},
        {"title": "Architecture of Sleep", "cat": "dreams", "hex": "#7ec8a0",
         "body": "Dreams build cities with impossible geometry. Every door opens into a different era. We forget the blueprints at the moment of waking.", "x": .38, "y": .78, "r": 17},
        {"title": "Palimpsest", "cat": "memory", "hex": "#8bb5c8",
         "body": "Memory is not storage. It is constant rewriting — each recall leaves a new impression over the last, until the original is only its own ghost.", "x": .72, "y": .72, "r": 15},
        {"title": "The Unnamed Fear", "cat": "fear", "hex": "#c87e8a",
         "body": "The fears that resist naming are the most sovereign. They do not require objects. They are the weather of the mind before the storm arrives.", "x": .86, "y": .50, "r": 14},
        {"title": "Language Before Thought", "cat": "consciousness", "hex": "#c8a97e",
         "body": "Does the word precede the thought, or does the thought precede the word? Perhaps there are ideas that exist only in the silence between.", "x": .30, "y": .16, "r": 16},
        {"title": "The Weight of the Present", "cat": "time", "hex": "#8bb5c8",
         "body": "The present moment is the only real thing, yet it vanishes the moment you name it. We live permanently in a tense that does not exist.", "x": .64, "y": .13, "r": 17},
        {"title": "Void as Foundation", "cat": "existence", "hex": "#c8a07e",
         "body": "Perhaps the void is not the absence of meaning but the precondition for it. Emptiness is what makes a vessel capable of holding anything.", "x": .88, "y": .74, "r": 13},
        {"title": "The Myth of Closure", "cat": "memory", "hex": "#8bb5c8",
         "body": "Closure is a story we tell ourselves. Grief, love, loss — they do not close. They simply find new rooms to inhabit inside us.", "x": .50, "y": .84, "r": 14},
        {"title": "Consciousness as Stranger", "cat": "consciousness", "hex": "#c8a97e",
         "body": "What if awareness is not native to the body but a visitor — arriving, looking around, and gradually forgetting it was ever anywhere else?", "x": .08, "y": .38, "r": 14},
    ]

    BASE_EDGES = [
        (0, 7, ConnectionType.expansion), (0, 1, ConnectionType.inspiration),
        (0, 11, ConnectionType.continuation), (1, 9, ConnectionType.expansion),
        (2, 5, ConnectionType.memory_link), (2, 8, ConnectionType.continuation),
        (3, 6, ConnectionType.emotional_resonance), (3, 10, ConnectionType.memory_link),
        (4, 5, ConnectionType.inspiration), (5, 10, ConnectionType.expansion),
        (6, 9, ConnectionType.existential_conflict), (7, 8, ConnectionType.contradiction),
        (8, 2, ConnectionType.expansion), (11, 0, ConnectionType.continuation),
        (4, 3, ConnectionType.emotional_resonance), (1, 11, ConnectionType.inspiration),
        (6, 2, ConnectionType.contradiction),
    ]

    db = SessionLocal()
    try:
        if db.query(ThoughtNode).filter(ThoughtNode.is_base == True).count() > 0:
            return  # already seeded

        nodes = []
        for n in BASE_NODES:
            node = ThoughtNode(
                title=n["title"], content=n["body"], category=n["cat"],
                hex_color=n["hex"], position_x=n["x"], position_y=n["y"],
                node_radius=n["r"], is_base=True, author="William · The Architect",
            )
            db.add(node)
            nodes.append(node)
        db.flush()  # assign IDs

        for src_idx, tgt_idx, conn_type in BASE_EDGES:
            db.add(ThoughtConnection(
                source_node_id=nodes[src_idx].id,
                target_node_id=nodes[tgt_idx].id,
                connection_type=conn_type,
            ))

        db.commit()
        logger.info("Seeded %d base constellation nodes.", len(nodes))
    except Exception as e:
        db.rollback()
        logger.warning("Seeding skipped or failed: %s", e)
    finally:
        db.close()

# ── Seed admin user on first run ─────────────────────────────
def _seed_admin():
    from backend.database import SessionLocal
    from backend.models import User, UserRole
    from backend.utils.security import hash_password
    from datetime import datetime

    ADMIN_EMAIL    = "lampteywilliam48@gmail.com"      # ← change this
    ADMIN_USERNAME = "william"             # ← change this
    ADMIN_PASSWORD = "Quabena_419"  # ← change this

    db = SessionLocal()
    try:
        exists = db.query(User).filter(User.email == ADMIN_EMAIL).first()
        if not exists:
            admin = User(
                username=ADMIN_USERNAME,
                email=ADMIN_EMAIL,
                password_hash=hash_password(ADMIN_PASSWORD),
                role=UserRole.admin,
                last_login=datetime.utcnow(),
            )
            db.add(admin)
            db.commit()
            print(f"Admin seeded: @{ADMIN_USERNAME}")
    except Exception as e:
        db.rollback()
        print("Admin seed skipped:", e)
    finally:
        db.close()
# ── App ───────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Noema API",
    description="Backend for the cinematic philosophy platform — Noema.",
    version=settings.VERSION,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Routers ───────────────────────────────────────────────────────────────────

app.include_router(auth_routes.router)
app.include_router(users.router)
app.include_router(submissions.router)
app.include_router(thought_nodes.router)
app.include_router(admin.router)


# ── Health ────────────────────────────────────────────────────────────────────

@app.get("/", tags=["Health"])
def root():
    return {"status": "alive", "platform": "Noema", "version": settings.VERSION}


@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok"}
