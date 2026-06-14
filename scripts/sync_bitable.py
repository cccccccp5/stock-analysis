"""Sync SQLite fills to Feishu Bitable (optional, stage 5.3).

Requires config/feishu.yaml with app_id, app_secret, app_token, table_id.
Run with --dry-run to print records without API calls.
"""
import argparse
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "trade_journal.db"
CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "feishu.yaml"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if not DB_PATH.exists():
        print("No database. Run init_db.py first.")
        return

    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT id, ticker, side, qty, avg_price, fill_time FROM fills ORDER BY id DESC LIMIT 20"
    ).fetchall()
    conn.close()

    print(f"Found {len(rows)} fill(s) to sync")
    for r in rows:
        print(r)

    if args.dry_run:
        print("Dry run — no Feishu API call.")
        return

    if not CONFIG_PATH.exists():
        print(f"Missing {CONFIG_PATH}. Copy from feishu.yaml.example and fill credentials.")
        return

    print("Feishu sync not implemented in scaffold. Add API calls per open.feishu.cn docs.")


if __name__ == "__main__":
    main()
