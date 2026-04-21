import os
from dotenv import load_dotenv

load_dotenv()

STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")
DB_PATH = os.getenv("DB_PATH", "./stripe_integration.db")
PORT = int(os.getenv("PORT", "8000"))

if not STRIPE_SECRET_KEY:
    raise RuntimeError(
        "STRIPE_SECRET_KEY is not set. Copy .env.example to .env and add your Stripe test key."
    )
