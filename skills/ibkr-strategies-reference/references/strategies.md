# Strategies Reference

8 strategies, hardcoded as `STRATEGIES` dict in `position_kit/generate.py` + shared with `place_bracket.py`.

---

## Quick Reference Table

| Strategy | Multipliers | Sell% | Best for | Default category |
|---|---|---|---|---|
| **B7_step35_前重_50_30_20** | 1.35 / 1.70 / 2.05 | 50 / 30 / 20 | High volatility + single-event driven, fast de-risking | `high_growth_small_cap`, `crypto_stock` |
| **B_50_100_200_equal** (default) | 1.5 / 2.0 / 3.0 | 33 / 33 / 34 | Steady appreciation, even realization | `high_growth`, `semi_equipment`, `semi_single_stock` |
| **B6_前重_50_30_20** (legacy) | 1.5 / 2.0 / 3.0 | 50 / 30 / 20 | Older front-loaded variant (50/100/200% intervals) | Replaced by B7, retained for compatibility |
| **B2_20_40_80_保守** | 1.2 / 1.4 / 1.8 | 33 / 33 / 34 | Recent IPO / high-uncertainty | `ipo_crypto` |
| **A_+100_全卖** | 2.0 | 100 | High HV + no tail position, double-and-out | (case-by-case) |
| **A_+200_全卖** | 3.0 | 100 | Low HV + long-term target, triple-and-out | (case-by-case) |
| **E_buy_hold** | — | — | Faith stocks / ETFs, no TPs (only manual stop-loss) | `semi_etf` |
| **G_grid_accumulate** | grid width 2-15% (vol-tiered) | retention 3:2 / 2:1 / 4:3 | Grid accumulation: long-term bullish + high vol + accumulating low-cost base | Cross-category, vol-tier-driven. See `grid_strategy.md`. |

---

## Decision Tree

```
What's the expected post-entry behavior?
│
├── Grid accumulation (long-term bullish + high vol + want low-cost base) → G_grid_accumulate
│   (Trigger: "网格 X $Y", auto vol-tier + retention ratio)
│   (See references/grid_strategy.md)
│
├── High vol + single-event driven (earnings/contract/regulatory) → B7_step35_前重_50_30_20
│   (Fast de-risking, 35% increments vs older 50% too wide)
│
├── Steady appreciation, even realization → B_50_100_200_equal
│   (Large-cap growth / semi equipment)
│
├── Recent IPO / unstable → B2_20_40_80_保守
│   (Early realization at 20/40/80%, for unstable IPOs)
│
├── HV high (60d HV > 50%), no tail position → A_+100_全卖
│   (Double-and-out)
│
├── HV low (60d HV < 30%), triple target → A_+200_全卖
│   (Patience-driven, triple-and-out)
│
└── Faith stock / ETF / long hold → E_buy_hold
    (No TPs, only manual stop-loss)
```

---

## Strategy math examples (cost = $100)

### B7_step35_前重_50_30_20 (recommended for high-vol single-event names)

| Tier | Multiplier | Trigger | Qty (per 100 shares) | Cumulative sell% |
|---|---|---|---|---|
| TP1 | 1.35× | $135.00 | 50 | 50% |
| TP2 | 1.70× | $170.00 | 30 | 80% |
| TP3 | 2.05× | $205.00 | 20 | 100% |
| Stop | 0.85× | $85.00 | 100 (manual / bracket) | — |

**Characteristic**: 35% increments (1.35 / 1.70 / 2.05 = +35/+70/+105% vs cost), front-loaded (50/30/20).
**Total sell revenue (full TP)**: $13,500 + $5,100 + $4,100 = $22,700 (+127% if all TPs fire)

### B_50_100_200_equal (default, large-cap growth)

| Tier | Multiplier | Trigger | Qty | Cumulative sell% |
|---|---|---|---|---|
| TP1 | 1.5× | $150.00 | 33 | 33% |
| TP2 | 2.0× | $200.00 | 33 | 66% |
| TP3 | 3.0× | $300.00 | 34 | 100% |
| Stop | 0.85× | $85.00 | 100 | — |

**Characteristic**: 50/100/200% intervals, even distribution.

### B2_20_40_80_保守 (IPO / fragile)

| Tier | Multiplier | Trigger | Qty | Cumulative sell% |
|---|---|---|---|---|
| TP1 | 1.2× | $120.00 | 33 | 33% |
| TP2 | 1.4× | $140.00 | 33 | 66% |
| TP3 | 1.8× | $180.00 | 34 | 100% |
| Stop | 0.85× | $85.00 | 100 | — |

**Characteristic**: Early realization, no swinging for fences, 20/40/80% triggers.

### A_+100_全卖

| Tier | Multiplier | Trigger | Qty | Cumulative sell% |
|---|---|---|---|---|
| TP1 | 2.0× | $200.00 | 100 | 100% |

### A_+200_全卖

| Tier | Multiplier | Trigger | Qty | Cumulative sell% |
|---|---|---|---|---|
| TP1 | 3.0× | $300.00 | 100 | 100% |

### E_buy_hold

No JSON output, only prints suggested stop-loss ($85 if cost $100). User places stop manually in IBKR client.

---

## Strategy override rules

User can explicitly combine `--strategy X --category Y` (even if X is not Y's default):

- `generate.py` / `place_bracket.py` detects mismatch → **prints WARN but continues**
- WARN example: `⚠️ strategy 'A_+100_全卖' is not the default for category 'high_growth' (default is 'B_50_100_200_equal'). Confirm?`
- Claude should **explain the override reason** in conversation (e.g. "I'm intentionally using A because HV is unusually high right now, want to lock in a quick double").

---

## Common strategy selection errors

1. **Small-cap growth using B default** → should use B7 front-loaded, otherwise volatility shakes out the tail
2. **Recent IPO (<6 months) using B default** → should use B2 conservative
3. **Semi ETF using B default with TPs** → should use E_buy_hold (ETFs are best long-hold with manual stop)
4. **Mixed thesis (e.g. crypto + AI dual-label) using B6** → if one thesis dominates, pick the appropriate strategy for that thesis
