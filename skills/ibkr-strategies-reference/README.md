# IBKR Trading Skill v2 (Shareable)

A Claude skill for systematic stock trading on Interactive Brokers, combining a 13-Master research framework, structured exit strategies (A+ bracket), and grid accumulation (G_grid_accumulate).

## What's in this package

| File | Purpose |
|---|---|
| `SKILL.md` | Main skill manifest. Triggers + workflow + invariants. |
| `references/grid_strategy.md` | G_grid_accumulate strategy SOP (Phase A → H), with **Option B (双单结构 / dual-order workaround)** for IBKR's bracket child-qty constraint. |
| `references/strategies.md` | 8 exit strategies (B7 / B / B2 / B6 / A_+100 / A_+200 / E_buy_hold / G_grid_accumulate). |
| `references/ibkr_quirks.md` | **NEW** — IBKR API limitations and workarounds discovered during real-money execution (web-source stale data, bracket child-qty forcing, market data subscription, status.py quote gap, zsh `read -p` incompatibility). |
| `CHANGELOG.md` | Version notes (v2 added Option B + Quirks doc). |

## Prerequisites (build your own toolchain)

This skill assumes you've built (or will build) a CLI on top of `ib_insync`:

- `~/ibkr-grid/place_list.py` — place flat list of orders
- `~/ibkr-grid/place_bracket.py` — place A+ bracket (parent + multi-TP + STP)
- `~/ibkr-grid/status.py` — view positions + open orders + (optionally) live quote
- `~/ibkr-grid/reconcile.py` — diff local snapshots vs IBKR open orders
- `~/ibkr-grid/cancel_grid.py` — cancel by symbol / orderId

If you don't have the tooling, you can still use this skill as a design reference and write your own equivalents on top of `ib_insync` or any other IBKR API wrapper.

## How to use as a Claude skill

1. Drop the contents into your `~/.claude/skills/` directory (or wherever your Claude client loads skills from).
2. The skill will trigger on phrases like:
   - `网格 X $Y` / `G_grid X $Y` / `new strategy X $Y` — invokes G_grid_accumulate
   - `建仓 X N 股` / `place bracket X` — invokes A+ bracket
   - `挂止盈` / `止损` / `cycle 2 anchor` — generates incremental orders
3. Claude will read SKILL.md → relevant references → execute Phase A → G with mandatory price verification.

## Hard prerequisites for safe execution

- ⚠️ Live IBKR account with API enabled (TWS or IB Gateway running on `127.0.0.1:4001` or `:7497`).
- ⚠️ User explicit confirmation before any real-money order.
- ⚠️ User real-time price screenshot or independent quote source for anchor verification (web 3-source consensus is **not enough** — see `ibkr_quirks.md`).

## What's NOT included (deliberately removed for privacy)

- Specific account IDs
- Current positions / cost basis
- Personal communications / brokerage credentials
- Cloud server IPs and SSH paths
- Personal investment thesis specifics

You can layer those in as your own private fork.

## License / Attribution

Free to use, modify, and share. Built from real-money execution lessons on 2026-05-22 (IREN $10k G_grid first run). No warranty — your trades, your responsibility.
