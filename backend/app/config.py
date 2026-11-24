import os


class Settings:
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", "postgresql+psycopg://crm:crm@localhost:5432/crm"
    )
    SECRET_KEY: str = os.getenv("SECRET_KEY", "bitte-in-produktion-aendern")
    TOKEN_EXPIRE_MINUTES: int = int(os.getenv("TOKEN_EXPIRE_MINUTES", "720"))
    CORS_ORIGINS: list[str] = os.getenv(
        "CORS_ORIGINS", "http://localhost:5173,http://localhost:8080"
    ).split(",")
    # Erster Admin wird beim Start angelegt, falls noch keine Benutzer existieren
    ADMIN_EMAIL: str = os.getenv("ADMIN_EMAIL", "admin@firma.de")
    SUPERUSER_EMAIL: str = os.getenv("SUPERUSER_EMAIL", "")   # REV02-07: wer das Protokoll öffnen darf
    ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "admin123")
    DEFAULT_TAX_RATE: float = float(os.getenv("DEFAULT_TAX_RATE", "19"))
    COMPANY_NAME: str = os.getenv("COMPANY_NAME", "Meine Firma GmbH")
    APP_URL: str = os.getenv("APP_URL", "")  # z. B. https://crm.firma.local – für Links in E-Mails/Kalender
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "/data/uploads")
    MAX_UPLOAD_MB: int = int(os.getenv("MAX_UPLOAD_MB", "50"))
    # E-Mail (optional, interner Mailserver)
    SMTP_HOST: str = os.getenv("SMTP_HOST", "")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "25"))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    SMTP_STARTTLS: bool = os.getenv("SMTP_STARTTLS", "false").lower() in ("1", "true", "ja")
    SMTP_FROM: str = os.getenv("SMTP_FROM", "klarcrm@firma.local")


settings = Settings()
