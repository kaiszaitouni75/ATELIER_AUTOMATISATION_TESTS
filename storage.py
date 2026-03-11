"""
storage.py — Persistance SQLite des runs de tests.
"""
import json
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_results.db")

# ── Anti-spam : 1 run toutes les 5 minutes maximum ──────────────────────────
MIN_INTERVAL_SECONDS = 300


def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS runs (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                api           TEXT    NOT NULL,
                timestamp     TEXT    NOT NULL,
                passed        INTEGER,
                failed        INTEGER,
                errors        INTEGER,
                total         INTEGER,
                error_rate    REAL,
                availability  REAL,
                latency_avg   INTEGER,
                latency_p95   INTEGER,
                tests_json    TEXT
            )
        """)
        conn.commit()


def save_run(run: dict) -> int:
    s = run["summary"]
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute("""
            INSERT INTO runs
              (api, timestamp, passed, failed, errors, total,
               error_rate, availability, latency_avg, latency_p95, tests_json)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)
        """, (
            run["api"], run["timestamp"],
            s["passed"], s["failed"], s["errors"], s["total"],
            s["error_rate"], s["availability"],
            s["latency_ms_avg"], s["latency_ms_p95"],
            json.dumps(run["tests"], ensure_ascii=False),
        ))
        conn.commit()
        return cur.lastrowid


def list_runs(limit: int = 50) -> list:
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT * FROM runs ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
    result = []
    for row in rows:
        d = dict(row)
        d["tests"] = json.loads(d.pop("tests_json", "[]"))
        result.append(d)
    return result


def seconds_since_last_run() -> float:
    """Retourne le nombre de secondes depuis le dernier run (inf si aucun)."""
    from datetime import datetime, timezone
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute(
            "SELECT timestamp FROM runs ORDER BY id DESC LIMIT 1"
        ).fetchone()
    if not row:
        return float("inf")
    last = datetime.fromisoformat(row[0])
    now  = datetime.now(timezone.utc)
    return (now - last).total_seconds()


def export_json(limit: int = 200) -> list:
    return list_runs(limit=limit)
