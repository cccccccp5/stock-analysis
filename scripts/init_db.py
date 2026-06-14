"""Initialize trade_journal.db schema."""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "trade_journal.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS research_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker TEXT NOT NULL,
    theme TEXT,
    scores_json TEXT,
    calibrated_score REAL,
    tier TEXT,
    entry_zone TEXT,
    stop_loss TEXT,
    sell_trigger TEXT,
    price_sources_json TEXT,
    note TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS decisions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    research_id INTEGER,
    ticker TEXT NOT NULL,
    action TEXT NOT NULL,
    strategy TEXT,
    budget REAL,
    approval_json TEXT,
    user_confirmed_at TEXT,
    status TEXT DEFAULT 'pending',
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (research_id) REFERENCES research_logs(id)
);

CREATE TABLE IF NOT EXISTS fills (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    decision_id INTEGER,
    ticker TEXT NOT NULL,
    side TEXT NOT NULL,
    qty REAL NOT NULL,
    avg_price REAL NOT NULL,
    commission REAL DEFAULT 0,
    strategy TEXT,
    slippage_vs_plan REAL,
    note TEXT,
    fill_time TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (decision_id) REFERENCES decisions(id)
);

CREATE TABLE IF NOT EXISTS position_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    snapshot_date TEXT NOT NULL,
    ticker TEXT NOT NULL,
    qty REAL,
    avg_cost REAL,
    market_price REAL,
    unrealized_pnl REAL,
    strategy TEXT,
    vol_tier TEXT
);

CREATE TABLE IF NOT EXISTS reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    period TEXT NOT NULL,
    stats_json TEXT,
    mistake_tags TEXT,
    lesson TEXT,
    reviewed_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS lessons (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    tags TEXT,
    body TEXT,
    merged_to_skill INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now'))
);
"""


def main():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SCHEMA)
    conn.commit()
    conn.close()
    print(f"Initialized: {DB_PATH}")


if __name__ == "__main__":
    main()
