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
    ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "admin123")
    DEFAULT_TAX_RATE: float = float(os.getenv("DEFAULT_TAX_RATE", "19"))
    COMPANY_NAME: str = os.getenv("COMPANY_NAME", "Meine Firma GmbH")


settings = Settings()
