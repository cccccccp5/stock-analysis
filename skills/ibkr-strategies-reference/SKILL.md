---
name: ibkr-trading
description: Systematic IBKR trading skill. Triggers on phrases like "网格 X $Y" / "G_grid X $Y" / "建仓 X N 股" / "挂止盈 X" / "止损 X" / "new strategy X $Y" / "Cycle N X". Encodes A+ bracket (multi-TP exit) and G_grid_accumulate (grid accumulation with 3:2 retention) strategies, tick-rule invariants, and IBKR API workarounds. Symbols are user-defined. Tooling assumed at ~/ibkr-grid/ (place_list.py / place_bracket.py / status.py / reconcile.py / cancel_grid.py).
---

# IBKR Trading Skill

Unified system for researching, planning, and executing positions on Interactive Brokers. Encodes a strategy framework (research → category → strategy → TP/STP), tooling conventions, and hard invariants discovered through real-money execution.

---

## Core Invariants (NEVER violate)

1. **Tick rule** — BUY limit/trigger price last digit must be `.10` or `.60`; SELL must be `.40` or `.90`. Avoids the `.00` / `.50` integer-wall queue priority hit. Implement in `tick_rules.snap_to_tick()`.
2. **Conservative snap direction** — BUY snaps DOWN (cost edge ↓), SELL snaps UP (profit/stop edge ↑). Hardcoded in `tick_rules.py`.
3. **A+ bracket structure** — Any entry with stop-loss MUST use A+ bracket structure (3+ independent brackets, each containing BUY + TP + STP, OCA-linked per bracket). NEVER attach a single oversized STP to a flat list of orders (over-sell disaster).
4. **`--force` transparency** — If a TP price deviates from market by >50%, tool MUST BLOCK and require `--force` flag. The `--force` decision must be surfaced to the user in the approval table.
5. **Cost basis is not assumed** — Before placing real TP/STP based on a filled position, recompute from actual fill average. Using BUY limit price as the "budget price" (entry-price param) is acceptable as long as you understand TPs/STPs will be slightly conservative.
6. **Whitelist default = empty** — In `config.yaml`, `symbol_whitelist: []` by default (no gate). User can set `symbol_whitelist: ["SYM1", "SYM2"]` to enforce a hard gate. With no whitelist, the duty of "don't trade the wrong ticker" falls to invariant #8 below.
7. **Uncertainty stated explicitly** — Never fabricate data. When unsure, say "uncertain" out loud.
8. **Real-time price verification — triple-source** — Any "建仓 / 网格 / 加仓 / 调仓" trigger MUST verify the anchor against:
   - Web source A (Yahoo / Investing / Morningstar / TradingView / CNBC)
   - Web source B (different from A, same list)
   - **User's own real-time terminal screenshot OR `status.py`-pulled IBKR quote**
   
   If web A and B disagree by >2% → STOP. If web A+B agree but user's screenshot disagrees by >2% → STOP (web 3-source can be stale-cached from one upstream feed, see `ibkr_quirks.md`).
9. **G_grid Phase A is mandatory** — Receiving a "网格 X $Y" trigger means you MUST execute `grid_strategy.md` Phase A in full (price + 52w high + 5d range + 30-day events + Beta/HV). Skipping any sub-step is the same failure mode as missing major news (e.g. unannounced contracts, dilutive offerings).

---

## Workflow at a glance

### Path 1: A+ bracket (single entry, multi-TP exit)

Trigger: `"建仓 X N 股 [本金 $Y]"` / `"place bracket X qty N"`

```
1. Category inference        From references/categories.md (user-maintained) + Claude's knowledge → present table to user
2. Strategy selection        Defaulted from category, user can override
3. Pull market price         python status.py --symbol X    (in ~/ibkr-grid/, venv activated)
4. Limit price decision      Pick legal BUY tick (.10/.60), offset +0.4% to +1.5% above market for high fill probability
5. Tick snap                 All prices (entry/TP/STP) via ibkr_grid.tick_rules.snap_to_tick()
6. Compute TPs + STP         cost × strategy multipliers (SELL snap up), cost × stop_loss_pct (SELL snap up)
7. Approval table            Tabular: Bracket / Qty / BUY / TP / STP / OCA group + R:R + total capital
8. User confirmation         Wait for "y" / "confirmed"
9. Place real orders         python place_bracket.py ... --force (TP3 must BLOCK without --force)
10. Verify                   python status.py --symbol X && python reconcile.py
11. Post-fill review         Recompute with actual fill avg cost (may not need re-placing TPs if entry-price was conservative)
```

### Path 2: G_grid_accumulate (grid buying with 3:2 retention)

Trigger: `"网格 X $Y"` (X=symbol, Y=budget), `"new strategy X $Y"`, `"G_grid X $Y"`

**Core behavior**: Claude reads the full grid_strategy.md SOP and produces all phases (A → H) in one shot. User provides only symbol + budget.

```
Phase A: Real-time price verification     Triple-source + 52w high + 5d range + 30-day events + Beta/HV
Phase B: Vol Tier determination           4 tiers (Ultra-high / High / Medium / Low) → grid width % + retention ratio
Phase C: Capital allocation               Two sizing modes:
                                            - Default SOP: 90% cycle pool / 10% cash buffer, single cycle ≤ pool/3 (allows ≥3 parallel)
                                            - All-in mode: single cycle uses near-full budget (N × P_BUY ≈ Y, strict 3:2 + multiple-of-10)
Phase D: Anchor computation               P_BUY = P_current × (1 + offset), snap; P_SELL = P_BUY + spread, snap
Phase E: Stop-loss lines                  Soft alert = retained_cost × 0.905; Hard stop = retained_cost × 0.85
Phase F: Approval table                   Snapshot + event watchlist + grid params + stop-loss + R:R + uncertainties
Phase G: Real placement (after user y)    
                                          Single-cycle, single-BUY mode:
                                            python place_list.py --symbol X --action BUY --qty N --price P_BUY --tif GTC
                                          
                                          Single-cycle, one-shot bracket mode (SOP §8 OCO protection):
                                            Custom ib_insync script (see grid_strategy.md §13) — dual-order structure:
                                              Bracket A: BUY M + TP M + STP M (parent-child OCA, M = N × 2/3)
                                              Independent: BUY N-M (retention, no TP/STP)
                                              Reason: IBKR forces bracket child qty = parent qty (see ibkr_quirks.md)
Phase H: Indicator card                   4 price alerts in IBKR Mosaic + trigger-action map + escalation rules
```

**See `references/grid_strategy.md` for the complete SOP.**

---

## Decision tree on first contact

| User says... | Claude does... |
|---|---|
| `"建仓 X N 股"` | Read references/strategies.md → choose default from references/categories.md → produce A+ bracket approval table → wait for y → place_bracket.py |
| **`"网格 X $Y"` / `"new strategy X $Y"` / `"G_grid X $Y"`** | **Read `references/grid_strategy.md` end-to-end. Execute Phase A → H strictly.** No skipping Phase A regardless of how confident you feel about the symbol. |
| `"挂止盈 / 出 TP 方案"` | Ask filled qty + avg cost + strategy preference; call `python skills/position_kit/generate.py` to produce TP JSON |
| `"改 X 的策略"` | Read references/strategies.md → diff table (old TPs vs new TPs) → user confirm → regenerate JSON |
| `"止损呢"` | Emphasize: STP is auto-managed inside A+ bracket (OCA reduce-only). G_grid has no auto-STP unless you use Option B / SOP §8 OCO protection (see grid_strategy.md). |
| `"<framework> says X 得 N.M 分"` | Synthesize → category → strategy. Reference references/holdings.md (user-maintained) for sizing context. |
| **`"X fill 了 N 股 @ $P"` (G_grid follow-up)** | Immediately produce SELL placement command per retention ratio + update indicator card |
| **`"X 到 $P 了"` (price alert fired)** | Look up indicator card → corresponding action (place / pause / close) |

---

## Communication norms (recommended)

- **Language**: User preference (Chinese in original deployment).
- **Style**: High information density, tables / code blocks / number contrasts, minimal prose paragraphs.
- **Risk tiers**:
  - **High-risk / irreversible** (code edits, file deletion, push/publish, real money order placement): produce diff → wait for explicit confirmation → post-change self-verification.
  - **Medium-risk / reversible**: confirm plan → execute continuously.
  - **Low-risk / read-only** (grep / SELECT / status.py): batch without interruption.
  - **Creative / analysis**: output directly.
- **When uncertain**: Say "uncertain" out loud. Never fabricate.
- **Approval tables**: Numbers precise to the cent. Include deviation from market + R:R + cash buffer.

---

## Hard constraints (not bypassable)

- ⚠️ Whitelist `[]` default = no gate. If user manually sets whitelist and symbol not in it → tool auto-rejects.
- ❌ TP deviates from market >50% without `--force` → tool auto-BLOCKS.
- ❌ Single oversized STP on a flat list (place_list mode + 100-share STP) → over-sell risk, MUST use A+ bracket.
- ❌ Assume cost basis (pre-fill) for placing TP → entry-price as ceiling is OK; recompute with real fill avg is safer.
- ❌ Edit JSON output file by hand → loses audit trail. Always re-run generate.py to overwrite.
- ❌ Place stop-loss in ibkr-grid tools outside A+ bracket → user must place manually in IBKR client (unless Option B / OCO protection, see grid_strategy.md).

---

## Related references

- `references/grid_strategy.md` — Complete G_grid_accumulate SOP. **MUST read on every "网格 X $Y" trigger**.
- `references/strategies.md` — 8 exit strategies (B7 / B / B2 / B6 / A_+100 / A_+200 / E_buy_hold / G_grid_accumulate) with multipliers and decision tree.
- `references/ibkr_quirks.md` — **NEW** — IBKR API gotchas discovered in real-money execution. Read before any first-time order placement.

---

## Version notes

See `CHANGELOG.md` for what changed in v2 vs v1 (v2 adds Option B dual-order workaround + sizing all-in mode + IBKR quirks doc).
