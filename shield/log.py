"""Layer 7: SQLite log. Only the MASKED prompt is ever stored."""
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import config

SCHEMA = """CREATE TABLE IF NOT EXISTS requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT, shield_on INTEGER, prompt_masked TEXT,
    verdict TEXT, blocked_by TEXT, attack_type TEXT, risk_score REAL,
    latency_total_ms REAL, latency_json TEXT)"""


def connect():
    """Open the database (creating the folder and table if needed)."""
    Path(config.DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(config.DB_PATH)
    conn.execute(SCHEMA)
    return conn


def log_request(shield_on: bool, prompt_masked: str, result: dict) -> None:
    conn = connect()
    with conn:
        conn.execute(
            "INSERT INTO requests (ts, shield_on, prompt_masked, verdict, blocked_by, attack_type, "
            "risk_score, latency_total_ms, latency_json) VALUES (?,?,?,?,?,?,?,?,?)",
            (datetime.now(timezone.utc).isoformat(timespec="seconds"), int(shield_on), prompt_masked,
             result["verdict"], result["blocked_by"], result["attack_type"], result["risk_score"],
             result["latency_ms"]["total"], json.dumps(result["latency_ms"])))
    conn.close()
