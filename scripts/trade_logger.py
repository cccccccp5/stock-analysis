"""CLI for trade journal operations."""
import argparse
import json
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "trade_journal.db"
FILLS_DIR = Path(__file__).resolve().parent.parent / "journal" / "fills"


def connect():
    return sqlite3.connect(DB_PATH)


def cmd_research(args):
    conn = connect()
    conn.execute(
        """INSERT INTO research_logs (ticker, theme, scores_json, tier, note)
           VALUES (?, ?, ?, ?, ?)""",
        (args.ticker, args.theme, args.scores, args.tier, args.note),
    )
    conn.commit()
    rid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.close()
    print(f"research_logs id={rid}")


def cmd_decision(args):
    conn = connect()
    conn.execute(
        """INSERT INTO decisions (ticker, action, strategy, budget, status)
           VALUES (?, ?, ?, ?, ?)""",
        (args.ticker, args.action, args.strategy, args.budget, args.status),
    )
    conn.commit()
    did = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.close()
    print(f"decisions id={did}")


def cmd_fill(args):
    conn = connect()
    conn.execute(
        """INSERT INTO fills (ticker, side, qty, avg_price, strategy, note)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (args.ticker, args.side, args.qty, args.price, args.strategy, args.note),
    )
    conn.commit()
    fid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.close()

    FILLS_DIR.mkdir(parents=True, exist_ok=True)
    safe_ticker = args.ticker.replace("/", "_")
    md_path = FILLS_DIR / f"{safe_ticker}_fill_{fid}.md"
    md_path.write_text(
        f"# Fill #{fid} · {args.ticker}\n\n"
        f"- Side: {args.side}\n"
        f"- Qty: {args.qty}\n"
        f"- Avg price: {args.price}\n"
        f"- Strategy: {args.strategy or 'n/a'}\n"
        f"- Note: {args.note or ''}\n",
        encoding="utf-8",
    )
    print(f"fills id={fid}, markdown={md_path}")


def cmd_lesson(args):
    conn = connect()
    conn.execute(
        "INSERT INTO lessons (title, tags, body) VALUES (?, ?, ?)",
        (args.title, args.tags, args.body),
    )
    conn.commit()
    lid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.close()
    print(f"lessons id={lid}")


def cmd_list(args):
    conn = connect()
    rows = conn.execute(
        "SELECT id, ticker, side, qty, avg_price, fill_time FROM fills ORDER BY id DESC LIMIT ?",
        (args.limit,),
    ).fetchall()
    conn.close()
    for r in rows:
        print(r)


def main():
    parser = argparse.ArgumentParser(description="Trade journal CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("research")
    p.add_argument("--ticker", required=True)
    p.add_argument("--theme", default="")
    p.add_argument("--scores", default="{}")
    p.add_argument("--tier", default="")
    p.add_argument("--note", default="")
    p.set_defaults(func=cmd_research)

    p = sub.add_parser("decision")
    p.add_argument("--ticker", required=True)
    p.add_argument("--action", required=True)
    p.add_argument("--strategy", default="")
    p.add_argument("--budget", type=float, default=None)
    p.add_argument("--status", default="pending")
    p.set_defaults(func=cmd_decision)

    p = sub.add_parser("fill")
    p.add_argument("--ticker", required=True)
    p.add_argument("--side", required=True, choices=["BUY", "SELL"])
    p.add_argument("--qty", type=float, required=True)
    p.add_argument("--price", type=float, required=True)
    p.add_argument("--strategy", default="")
    p.add_argument("--note", default="")
    p.set_defaults(func=cmd_fill)

    p = sub.add_parser("lesson")
    p.add_argument("--title", required=True)
    p.add_argument("--tags", default="")
    p.add_argument("--body", default="")
    p.set_defaults(func=cmd_lesson)

    p = sub.add_parser("list")
    p.add_argument("--limit", type=int, default=10)
    p.set_defaults(func=cmd_list)

    args = parser.parse_args()
    if not DB_PATH.exists():
        print("DB not found. Run: python scripts/init_db.py")
        raise SystemExit(1)
    args.func(args)


if __name__ == "__main__":
    main()
