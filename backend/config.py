import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # App
    APP_NAME: str = "Noema"
    VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

    # Database — read from env, fixed postgres:// prefix at read time
    @property
    def DATABASE_URL(self) -> str:
        url = os.getenv("DATABASE_URL", "").strip()
        if not url:
            return "sqlite:///./noema.db"
        # Railway uses postgres:// — SQLAlchemy needs postgresql://
        if url.startswith("postgres://"):
            url = "postgresql://" + url[len("postgres://"):]
        return url

    # JWT
    SECRET_KEY: str = os.getenv(
        "SECRET_KEY",
        "noema-dev-secret-change-in-production-openssl-rand-hex-32"
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
        os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "10080")  # 7 days
    )

    # Email (SMTP)
    SMTP_HOST: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASS: str = os.getenv("SMTP_PASS", "")
    ADMIN_EMAIL: str = os.getenv("ADMIN_EMAIL", "")

    # CORS — comma-separated list of allowed origins
    @property
    def ALLOWED_ORIGINS(self) -> list:
        raw = os.getenv(
            "ALLOWED_ORIGINS",
            "http://localhost:3000,http://localhost:8000,http://127.0.0.1:8000"
        )
        return [o.strip() for o in raw.split(",") if o.strip()]


settings = Settings()
