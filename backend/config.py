import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    APP_NAME: str = "Noema"
    VERSION: str  = "1.0.0"

    @property
    def DEBUG(self) -> bool:
        return os.getenv("DEBUG", "false").lower() == "true"

    @property
    def DATABASE_URL(self) -> str:
        url = os.getenv("DATABASE_URL", "").strip()
        if not url:
            return "sqlite:///./noema.db"
        # Railway gives postgres:// — SQLAlchemy needs postgresql://
        if url.startswith("postgres://"):
            url = "postgresql://" + url[len("postgres://"):]
        return url

    @property
    def SECRET_KEY(self) -> str:
        return os.getenv(
            "SECRET_KEY",
            "noema-dev-secret-CHANGE-in-production"
        )

    ALGORITHM: str = "HS256"

    @property
    def ACCESS_TOKEN_EXPIRE_MINUTES(self) -> int:
        return int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "10080"))  # 7 days

    @property
    def SMTP_HOST(self) -> str:
        return os.getenv("SMTP_HOST", "smtp.gmail.com")

    @property
    def SMTP_PORT(self) -> int:
        return int(os.getenv("SMTP_PORT", "587"))

    @property
    def SMTP_USER(self) -> str:
        return os.getenv("SMTP_USER", "")

    @property
    def SMTP_PASS(self) -> str:
        return os.getenv("SMTP_PASS", "")

    @property
    def ADMIN_EMAIL(self) -> str:
        return os.getenv("ADMIN_EMAIL", "")

    @property
    def ALLOWED_ORIGINS(self) -> list:
        raw = os.getenv(
            "ALLOWED_ORIGINS",
            "http://localhost:3000,http://localhost:8000,http://127.0.0.1:8000"
        )
        return [o.strip() for o in raw.split(",") if o.strip()]


settings = Settings()
