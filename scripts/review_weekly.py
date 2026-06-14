"""Generate weekly review markdown from trade_journal.db."""
import argparse
import json
import sqlite3
from collections import Counter
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "trade_journal.db"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="journal/reviews/latest_weekly.md")
    args = parser.parse_args()

    root = Path(__file__).resolve().parent.parent
    out_path = root / args.output
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if not DB_PATH.exists():
        out_path.write_text("# 周报\n\n数据库未初始化。请先运行 init_db.py\n", encoding="utf-8")
        print(f"Wrote: {out_path}")
        return

    conn = sqlite3.connect(DB_PATH)
    fills = conn.execute(
        "SELECT ticker, side, qty, avg_price, strategy, fill_time FROM fills ORDER BY id DESC LIMIT 50"
    ).fetchall()
    lessons = conn.execute(
        "SELECT id, title, tags, created_at FROM lessons WHERE merged_to_skill = 0 ORDER BY id DESC LIMIT 10"
    ).fetchall()
    conn.close()

    lines = [
        "# 交易周报",
        "",
        "## 近期成交",
        "",
        "| Ticker | Side | Qty | Price | Strategy | Time |",
        "|--------|------|-----|-------|----------|------|",
    ]
    if fills:
        for f in fills:
            lines.append(f"| {f[0]} | {f[1]} | {f[2]} | {f[3]} | {f[4] or '-'} | {f[5]} |")
    else:
        lines.append("| （暂无成交记录） | | | | | |")

    lines += [
        "",
        "## 待合并 Lessons",
        "",
    ]
    if lessons:
        for L in lessons:
            lines.append(f"- #{L[0]} [{L[2]}] {L[1]} ({L[3]})")
    else:
        lines.append("- （无）")

    lines += [
        "",
        "## 复盘动作",
        "",
        "1. 检查是否有 fill 未记录",
        "2. 检查验价是否均含盈立第三源",
        "3. 将重复出现的 lesson 人工合并进 Skill",
        "",
    ]

    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote: {out_path}")


if __name__ == "__main__":
    main()
