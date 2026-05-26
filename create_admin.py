from backend.database import SessionLocal, init_db
from backend.models import User, UserRole
from backend.utils.security import hash_password
from datetime import datetime

init_db()

db = SessionLocal()

admin = User(
    username="william",
    email="lampteywilliam48@gmail.com",
    password_hash=hash_password("Quabena_419"),
    role=UserRole.admin,
    last_login=datetime.utcnow(),
)

db.add(admin)
db.commit()

print("Admin created:", admin.username)

db.close()