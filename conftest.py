"""Makes the repo root importable for pytest and sets FAKE secrets so tests need no .env."""
import os

os.environ.setdefault("ADMIN_CODE", "TESTADMIN-0000")
os.environ.setdefault("CANARY", "TESTCANARY-ZZZ")
