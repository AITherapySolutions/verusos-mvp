import os
import secrets

class Settings:
    PROJECT_NAME: str = "VerusOS"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    DATABASE_URL: str = os.environ.get("DATABASE_URL", "")
    SESSION_SECRET: str = os.environ.get("SESSION_SECRET", "verusos-secret-key")
    
    ADMIN_API_KEY: str = os.environ.get("ADMIN_API_KEY", secrets.token_urlsafe(32))
    
    TIER_1_DEADLINE_HOURS: int = 1
    TIER_2_DEADLINE_HOURS: int = 4
    TIER_3_DEADLINE_HOURS: int = 24
    TIER_4_DEADLINE_HOURS: int = 72
    
    LATE_NIGHT_HOURS: list = ["12am", "1am", "2am", "3am", "4am", "5am", "6am"]

settings = Settings()
