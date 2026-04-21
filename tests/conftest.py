import os
import tempfile

# src.config validates env at import time, so these have to be set first.
os.environ.setdefault("STRIPE_SECRET_KEY", "sk_test_dummy")
os.environ.setdefault("STRIPE_WEBHOOK_SECRET", "whsec_test_dummy_secret_for_tests_only")
os.environ.setdefault("DB_PATH", os.path.join(tempfile.gettempdir(), "stripe_test.db"))
