#!/usr/bin/env python3
"""Parse ticker and context for 13-Master Lite deep research."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

TRIGGER_WORDS = (
    "深度研究",
    "研究",
    "deep research",
    "deep-research",
)

TICKER_RE = re.compile(r"\b([A-Z]{1,5}(?:\.[A-Z]{1,2})?)\b")


def parse_ticker(text: str) -> str | None:
    cleaned = text.strip()
    for word in TRIGGER_WORDS:
        cleaned = re.sub(re.escape(word), " ", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    if not cleaned:
        return None
    match = TICKER_RE.search(cleaned.upper())
    return match.group(1) if match else None


def load_holdings_summary() -> dict:
    path = ROOT / "config" / "holdings.yaml"
    if not path.exists():
        return {"core_positions": [], "watchlist": [], "note": "holdings.yaml missing"}
    try:
        import yaml  # type: ignore

        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        return {
            "core_positions": data.get("core_positions") or [],
            "watchlist": data.get("watchlist") or [],
        }
    except Exception as exc:  # noqa: BLE001
        return {"error": str(exc)}


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/prep_us_lite_research.py '<user text>' [job_id]", file=sys.stderr)
        return 2

    user_text = sys.argv[1]
    job_id = sys.argv[2] if len(sys.argv) > 2 else None
    ticker = parse_ticker(user_text)

    payload = {
        "user_text": user_text,
        "ticker": ticker,
        "job_id": job_id,
        "parse_ok": ticker is not None,
        "holdings": load_holdings_summary(),
        "portfolio_health_path": str(ROOT / "data" / "portfolio_health.md"),
        "price_discipline_path": str(
            ROOT / "skills" / "us-stock-lite" / "references" / "price-discipline.md"
        ),
        "output_dir": str(ROOT / "data" / "deep_research_results"),
    }

    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if ticker else 1


if __name__ == "__main__":
    raise SystemExit(main())
