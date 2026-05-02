import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    FLASK_SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "dev_secret")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev_jwt_secret")
    JWT_ACCESS_TOKEN_EXPIRES = 60 * 60 * 24 * 7  # 7 dias

    # Cookies HttpOnly
    JWT_TOKEN_LOCATION = ["cookies"]
    JWT_COOKIE_SECURE = os.getenv("JWT_COOKIE_SECURE", "False").lower() == "true"
    JWT_COOKIE_SAMESITE = "Lax"
    JWT_COOKIE_CSRF_PROTECT = False  # Simplificado; habilite se usar CSRF tokens
    JWT_ACCESS_COOKIE_NAME = "access_token_cookie"

    MONGO_DB_STRING = os.getenv("MONGO_DB_STRING", "mongodb://localhost:27017/soundcircle")
    FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")
    RAPID_API_SPOTIFY = os.getenv("RAPID_API_SPOTIFY", "")
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
