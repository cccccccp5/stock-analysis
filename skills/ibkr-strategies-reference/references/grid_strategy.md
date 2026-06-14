# Grid Strategy Reference (G_grid_accumulate)

Complete specification for the grid-accumulation strategy. Hardcoded SOP — when triggered by "网格 X $Y" or equivalents, Claude must execute this end-to-end without skipping phases.

---

## 1. Triggers

| User says | Parsed as |
|---|---|
| **`"网格 X $Y"`** | symbol=X, budget=Y, full SOP |
| **`"网格 X"`** | symbol=X, budget asked of user (no default) |
| **`"new strategy X $Y"`** | Same as 网格 X $Y |
| **`"G_grid X $Y"`** | Same (technical alias) |

After trigger: Claude executes Phase A → H. Do not split across multiple rounds asking for details.

**Allowed interrupt**: price verification fail (>2% disagreement) OR symbol not in user whitelist (if user set one).

---

## 2. Strategy concept (5 rules)

| # | Rule | Math / meaning |
|---|---|---|
| 1 | Fixed grid width | Determined by vol tier (4 tiers, §3) |
| 2 | Single-side cycle | One group BUY → SELL → next group |
| 3 | **Wait for fill before placing next layer** | Don't pre-place multiple layers (core discipline, prevents double-kill in trending markets) |
| 4 | **Accumulation by asymmetric size**: buy N, sell M (M < N) | Retained shares' cost basis = P_BUY − (M / (N − M)) × spread |
| 5 | Core position never traded; 10-20% rotates | In this strategy, the budget IS the rotation pool. "Core position" emerges naturally from retained shares per cycle. |

**Retention cost formula**:
```
retained_cost = (N × P_BUY − M × P_SELL) / (N − M)
              = P_BUY − (M / (N − M)) × spread
```

---

## 3. Volatility Tier table (hardcoded, do not override)

| Tier | 60d HV | Beta hint | Grid width % | Retention (N:M) | Anchor offset (vs mkt) | Example profile |
|---|---|---|---|---|---|---|
| **Ultra-high** | >70% | >3 | **10-15%** | **3:2** (33% retained) | **-3% to -5%** | Small-cap narrative stocks, AI infra, BTC miners |
| **High** | 40-70% | 1.5-3 | **6-10%** | 3:2 or 2:1 | -2% to -4% | Large semis, foreign large-caps |
| **Medium** | 25-40% | 1-1.5 | **4-6%** | **2:1** | -1% to -2% | EDA, mature growth, utilities-with-AI |
| **Low** | <25% | <1 | **2-4%** | 2:1 or 1:1 (no accumulation) | -0.5% to -1% | ETFs, utilities, defensive |

**Tier selection priority**:
1. If symbol already in `references/holdings.md` — use the recorded tier
2. Otherwise: web_search for Beta + 60d HV → infer
3. Boundary cases (e.g. HV 65% straddling High/Ultra-high) → **pick higher tier** (conservative: wider grid)

---

## 4. Retention Ratio comparison (hardcoded)

| N:M | Retained % | Retained cost discount (vs P_BUY) | Net cash per cycle | Use case |
|---|---|---|---|---|
| 2:1 | 50% | −1× spread (e.g. −12% if width 12%) | ~50% × N×P_BUY | Medium/Low vol, conservative accumulation |
| **3:2 (default)** | 33% | **−2× spread (e.g. −24%)** | **~25% × N×P_BUY** | **Ultra-high/High vol, balanced** |
| 4:3 | 25% | −3× spread (e.g. −36%) | ~15% × N×P_BUY | Aggressive accumulation, high per-cycle cash use |
| 5:4 | 20% | −4× spread (e.g. −48%) | ~5% × N×P_BUY | Extreme aggressive, minimal retention but maximal discount |

**Default**: **3:2**. Override rules: Medium/Low vol → 2:1. Ultra-high vol → can use 4:3 but Claude WARNs.

---

## 5. End-to-End SOP (Phase A → H)

Strict sequential execution. No skipping.

### Phase A: Real-time price verification (immutable)

**A1. Whitelist soft-check** (default skip)
```
Read config.yaml's symbol_whitelist
  [] (default) → skip, continue to A2
  Non-empty + X in list → pass
  Non-empty + X not in → STOP, "X not in whitelist, add first"
```

**A2. TRIPLE-SOURCE price verification** (CRITICAL — see `ibkr_quirks.md` for why)
```
- Source A: web_search Yahoo / Investing.com / Morningstar / TradingView / CNBC (pick 1)
- Source B: web_search a DIFFERENT source from the list
- Source C: **User's own real-time terminal screenshot** (broker app, TradingView mobile, etc.)
            OR python status.py --symbol X (IBKR delayed quote)

Match criteria:
  All 3 within 0.5% → use the average / official close
  A & B agree but C differs >2% → STOP, web-cache likely stale (3 sources can share upstream feed)
  Any pair differs >2% → STOP, report conflict, await user decision
  Time stamps must be within 5 trading days

⚠️ Lesson from real execution: Yahoo + Investing + Morningstar may ALL display the previous day's close while labeling it as "current". Two-source agreement is NOT sufficient. Always validate against user's broker app or status.py.
```

**A3. Required data points**
```
- 52-week high + % from ATH
- 5-day intraday range
- Any ±10% single-day move in past 30 days
- Beta / 60d HV (for vol tier)
- Market cap + 10d avg volume (liquidity check)
- Morningstar Fair Value (if available, as anchor reference)
```

**A4. 30-day event scan**
```
web_search "X 8-K filings / earnings / M&A / dilution / insider selling / management change in past 30 days"
Event categories:
- Earnings reports
- Convertibles / secondaries / buybacks
- Major contracts (>5% revenue)
- Acquisitions / divestitures
- C-suite changes
- Insider transactions
- Regulatory (SEC / FDA / antitrust)
Any major event → must appear in approval table "event watchlist"
```

**A5. IBKR live anchor calibration** (pre-placement, not in approval phase)
```
Before real placement:
   python status.py --symbol X  (or place_list.py's embedded quote)
   Pull IBKR live price (delayed 15min OK if no subscription)
   If web data vs IBKR data deviates >2% → recompute anchor

⚠️ KNOWN GAP: status.py may not output quote in its current implementation 
(symbol filter only filters positions/orders, not quote). Workaround:
- place_list.py prints market price in its DRY-RUN summary before "confirm?" prompt
- OR use IBKR Mosaic / TWS directly to view price
- OR rely on user's real-time terminal screenshot as the third source
```

### Phase B: Vol Tier + Strategy Mapping

**B1**. Check `references/holdings.md` — if symbol is recorded, use its vol tier.
**B2**. Otherwise:
```
- web_search "X 60d historical volatility" + Beta
- Estimate HV from past 30d daily volatility RMS, or infer from Beta
- Boundary values → round UP to higher tier (conservative)
```
**B3**. Map to (grid_width %, retention ratio, anchor_offset).

### Phase C: Capital allocation — TWO MODES

**Mode 1: Standard SOP** (default for first-time users, conservative)
```
Cycle_pool   = Budget × 90%
Cash_buffer  = Budget × 10%   # fees / slippage / contingency

Constraint:
- Cycle_pool ≥ 3 × single_cycle_capital (≥3 parallel cycles possible)
- single_cycle_capital ≈ N × P_BUY
- If Budget too small → Claude warns user to increase budget
```

**Mode 2: All-in single-cycle** (user-elected, aggressive, recommended for focused single-symbol play)
```
N × P_BUY ≈ Budget (use entire budget in one BUY)
Strict 3:2 retention (N must be multiple of 30 to keep M and (N-M) clean)
Allow over-budget ≤0.1% (e.g. 180 × $55.60 = $10,008 over $10,000 by 0.08%)
No reserved cash buffer (assumes user's broader account can cover fees / slippage)

Use case: user says "建仓网格 1万美金 X" with intent to deploy the full $10k on X immediately.
```

**Claude's choice**: Default to Mode 1 unless user explicitly says "all-in" / "use full budget" / "一次性买入所有". If user later says they want all-in for future trades, treat that as a durable preference and apply Mode 2 by default.

### Phase D: Anchor computation (mandatory math)

```python
# D1. Verified P_current from Phase A
P_current = verified_price

# D2. Compute P_BUY
buy_offset = vol_tier.anchor_offset_pct  # e.g. -0.04 for Ultra-high
P_BUY_raw  = P_current * (1 + buy_offset)
P_BUY      = snap_to_tick(P_BUY_raw, side='BUY')  # snap DOWN to .10/.60

# D3. Compute grid width and P_SELL
grid_width_pct = vol_tier.grid_width  # e.g. 0.12 for Ultra-high
spread_raw     = P_BUY * grid_width_pct
P_SELL_raw     = P_BUY + spread_raw
P_SELL         = snap_to_tick(P_SELL_raw, side='SELL')  # snap UP to .40/.90
spread_actual  = P_SELL - P_BUY  # actual spread post-snap

# D4. Compute N (BUY total), M (SELL), retained = N-M
# CHOICE based on Phase C mode:

# Mode 1 (standard):
single_cycle_budget = Cycle_pool / 3  # allows 3 parallel
N_raw = single_cycle_budget / P_BUY
N     = floor(N_raw / 30) * 30   # multiple of 30 keeps 3:2 strict, multiple of 10 fallback

# Mode 2 (all-in):
N_raw = Budget / P_BUY
N     = round(N_raw / 30) * 30   # nearest multiple of 30, accept ±0.1% over/under-budget

M_ratio = vol_tier.retention_ratio  # (3, 2) for 3:2
M       = N * M_ratio[1] // M_ratio[0]  # e.g. N=180, M=120 (strict 3:2)
retained = N - M
retained_cost = (N * P_BUY - M * P_SELL) / retained  # G_grid net cash cost formula
```

### Phase E: Stop-loss lines

```python
# Soft alert: retained_cost × 0.905, snap UP to SELL tick
soft_alert = snap_to_tick(retained_cost * 0.905, side='SELL')

# Hard stop: retained_cost × 0.85, snap UP to SELL tick
hard_stop  = snap_to_tick(retained_cost * 0.85, side='SELL')

# Max single-cycle loss = N × (P_BUY - hard_stop)
max_loss_per_cycle = N * (P_BUY - hard_stop)
```

**Critical**: Stop-loss is **not auto-placed in Phase G's basic mode** (because cost basis evolves per cycle). Use Phase H indicator-card monitoring + manual close. **OR** use SOP §8 OCO protection / Option B (see §13).

### Phase F: Approval table format

```markdown
# G_grid plan - X - <timestamp>

## Live data snapshot (triple-source verified)
| Field | Value | Source |
|---|---|---|
| Current price | $__ | A: $__, B: $__, C: $__ (user/IBKR), agreement within __% |
| 52w high | $__ (date) | distance from ATH __% |
| Beta / 60d HV | __ / __ | source |
| 5d range | $__ - $__ | — |
| Vol Tier | __ | (Ultra-high / High / Medium / Low) |
| Market cap | $__ | — |

## 30-day event watchlist
| Date | Event | Impact |
| (list all ±10% moves / 8-K / earnings) |

## Capital allocation ($Y budget, MODE: __)
| Bucket | Amount |
| Cycle pool | $__ (Mode 1: 90%, Mode 2: 100%) |
| Cash buffer | $__ (Mode 1: 10%, Mode 2: 0) |

## First-layer grid parameters
| Field | Value |
| Anchor BUY | $__ (.10 or .60 tick, offset __%) |
| Corresponding SELL | $__ (.40 or .90 tick, offset __%) |
| Grid width | $__ (__ %) |
| Retention | __:__ (N=__ / M=__ / retained __ shares) |
| Retained cost (net cash) | $__ (discount __%) |
| Per-cycle capital | $__ |

## Stop-loss / alerts
| Tier | Price | Action |
| Soft alert | $__ | Pause next-layer BUY |
| Hard stop | $__ | Force close |
| Max single-cycle loss | $__ (__% of budget) |

## Uncertainties / WARNs
(All non-deterministic items + decisions needed from user)

## Awaiting user "y" → Phase G placement
```

### Phase G: Real placement — TWO IMPLEMENTATIONS

**Implementation 1: Standard "wait for fill" mode** (SOP §2 rule 3 strict)

```bash
cd ~/ibkr-grid && source venv/bin/activate

# Single BUY, no pre-placed SELL/STP
python place_list.py \
    --symbol X --action BUY --qty N --price P_BUY \
    --tif GTC \
    --note "G_grid cycle1 BUY anchor P_BUY"

# Verify
python status.py --symbol X && python reconcile.py

# Wait for fill → indicator card (Phase H) → user pings on fill → place SELL ($P_SELL × M) GTC
```

Pros: minimal capital commitment, follows G_grid §2 rule 3 strictly.
Cons: user must be online to react to fills.

**Implementation 2: One-shot bracket with OCA protection** (SOP §8, recommended for first-timers + all-in mode)

See §13 below for the dual-order structure (Option B). This was developed in response to the IBKR bracket child-qty constraint (see `ibkr_quirks.md`).

### Phase H: Indicator card (post-fill)

Generated after BUY fill. Must contain: 4 IBKR Mosaic price alerts / trigger-action map / escalation rules / status update template. Missing any = Phase H incomplete. Format:

```markdown
# X G_grid indicator card - <fill date>

## Current state
- Holdings: N shares @ actual fill avg $__
- Retained cost (after cycle): $__
- Open orders: SELL $__ × M shares (GTC) [if Implementation 1]
- Cash in cycle pool: $__

## IBKR Mosaic 4 price alerts (USER MUST SET)
| Alert name | Trigger | Direction | Meaning / your action |
|---|---|---|---|
| **BUY trigger** | P_BUY + tick | ≥ | Notify Claude "fill?" |
| **Next-layer BUY prep** | P_BUY − spread | ≤ | Notify Claude → Claude gives next-layer BUY |
| **Soft alert** | soft_alert | ≤ | Notify Claude immediately → pause |
| **Hard stop** | hard_stop | ≤ | **Close position first** (IBKR Mosaic → Portfolio → X → Close Position → MKT) → then notify Claude |

IBKR alert path: Mosaic → top-right bell → New Alert → Single Condition → X Last Price → choose condition → Email / phone notification

## Trigger-action map
| Trigger | User does | Claude does |
|---|---|---|
| BUY fill (partial/full) | Notify qty + avg, set 4 alerts | Immediately give SELL placement command (Mode 1) or note bracket auto-activated (Mode 2) |
| SELL fill | Notify "SELL M shares done" | Give next-layer command (uplevel or downlevel based on tape) |
| Not filled in 24h | Notify tape state | Evaluate anchor adjustment |
| Drops below next-layer BUY | Notify | Give next-layer BUY (parallel cycle) |
| Soft alert triggered | Notify immediately | Pause, evaluate fundamentals |
| Hard stop triggered | Close first, then notify | Postmortem |
| Any 8-K | Notify | Evaluate within 24h |
| Earnings approaching | Pre-notify | Pre-fight cancel command 5 days out |

## Escalation rules (when to wake Claude)
**Must ping**:
1. Any fill event
2. Single-day drop >10% or rise >15%
3. Any 8-K filing
4. Account margin red warning
5. Correlated symbol single-day drop >10% (NVDA for AI infra, BTC for crypto miners)

**No need to ping**:
- Price oscillating in [next BUY, next SELL] range normally
- Normal ±5% moves
```

---

## 6. Failure modes + responses

| Failure mode | Trigger scenario | Response |
|---|---|---|
| Single-side rally | SELL fills then keeps rising | Retained shares appreciate; uplevel next BUY |
| Single-side crash | BUY fills then keeps falling | Soft alert → pause; hard stop → close |
| Sideways narrow oscillation | Doesn't break grid width | No cycle triggers, capital idle (opportunity cost) |
| Gap | Open price jumps grid | Actual fill diverges from plan, retained cost not as expected |
| Liquidity drought | Small-cap spread too wide | Pause, switch to large-cap |
| Fundamental break | Earnings disaster / major negative | Cancel all orders + evaluate hard stop |
| Black swan | Systemic risk (war / pandemic) | Close all + re-evaluate |

---

## 7. Hard constraints (immutable)

1. ❌ Skipping Phase A (price verification) and jumping to plan → severe failure mode
2. ❌ Producing plan with web 2-source disagreement >2% (must STOP)
3. ❌ Skipping 30-day event scan → replicates "missed major contract / dilution" pattern
4. ❌ Using P_SELL instead of retained_cost in stop-loss math → arithmetic error
5. ❌ Rounding vol tier boundary to lower tier (e.g. HV 65% → High instead of Ultra-high) → not conservative
6. ❌ In Mode 1, single_cycle_capital > Cycle_pool / 3 → can't run ≥3 parallel
7. ❌ Same symbol simultaneously in A+ bracket and G_grid → capital conflict
8. ⚠️ Whitelist default `[]` = no gate (see SKILL.md #6). If user sets whitelist and symbol not in → tool auto-rejects.

---

## 8. OCO protection (recommended for offline safety)

Grid's "wait for fill" discipline weakness: user offline during single-side crash can't react. Optional protection: after BUY fill, **manually place OCA**:
- SELL $P_SELL × M shares (GTC, normal grid exit)
- STP $hard_stop × full N shares (GTC, reduce-only, safety net)
- Two orders OCA-linked (any fill cancels the other)

**Trade-off**: Violates "wait for fill" rule, but provides offline protection.
**Recommended**: First-time users **strongly advised to enable**. Experienced traders can skip.

**For one-shot version (all 4 orders placed at entry, no waiting for fill), see §13 below.**

---

## 9. Relationship to A+ bracket

| Field | A+ bracket | G_grid_accumulate |
|---|---|---|
| Capital purpose | One-shot entry, hold to target | Cyclic, accumulate, rotate |
| Stop-loss | Auto STP (hardcoded) | Monitoring + user manual close (or OCO §8 / Option B §13) |
| Take-profit | Tiered TP (1.35× / 1.70× / 2.05×) | Single grid SELL, cyclic |
| Suits | Medium-term hold + clear thesis | High vol + long-term bullish + accumulation goal |

**Parallel rules**:
- **Same symbol cannot use both simultaneously**: capital conflict, SELL orders eat each other's quantity
- **Different symbols can parallel**: e.g. SYM1 on G_grid, SYM2 on A+ bracket
- **Disambiguation**: User says "网格 X" → G_grid. User says "建仓 X N 股" → A+ bracket.

---

## 10. Hard constraints (not bypassable)

(See §7. Also: Phase A is the entirety of Phase A — skipping any sub-step (A1-A5) replicates known failure cases.)

---

## 11. Version history

| Date | Change | Reason |
|---|---|---|
| 2026-05-22 v1 | Created G_grid_accumulate strategy | First real-money execution on a high-vol AI-infra name |
| 2026-05-22 v2 | Added Mode 2 (all-in single-cycle) + §13 Option B (dual-order workaround for IBKR bracket child-qty constraint) | Same-day execution discovered: (a) "≥3 parallel cycles" was too conservative for focused all-in plays; (b) IBKR forces bracket child qty = parent qty, preventing 3:2 retention in single-bracket form |

---

## 12. Reference case: first execution (2026-05-22)

**Input**: 网格 X $10000, X = high-vol AI-infra name
**Vol Tier**: Ultra-high (Beta >3, HV >70%)
**Price chain (anchored to triple-source-verified previous-day close $58.06)**:
- Anchor BUY: $55.60 (.60 tick, -4.24% offset)
- SELL: $62.40 (.40 tick, +12.23% spread)
- Retention 3:2: N=180, M=120, retained=60
- Retained cost (net cash): $42.00 (-24.46% vs P_BUY)
- Soft alert: $38.40
- Hard stop: $35.90
- Max single-cycle loss (Bracket A): $2,364
- Max retention loss (manual close at $35.90): $366 net cash / $1,182 account view

**Capital deployment (Mode 2 all-in)**:
- Bracket A (cycle portion): BUY 120 + TP 120 @ $62.40 + STP 120 @ $35.90 = $6,672 committed
- Independent BUY (retention): 60 @ $55.60 = $3,336 committed
- Total committed: $10,008 (over $10k by 0.08%)

**See §13 for the placement script template.**

---

## 13. Option B: Dual-order structure (one-shot, IBKR bracket child-qty workaround)

**Problem solved**: IBKR's bracket parent-child relationship forces child orders' quantity to equal the parent's. If you place `BUY 180` as parent and try to specify `SELL 120 @ TP` as child, IBKR overrides the child quantity to 180, breaking 3:2 retention.

**Solution**: Split the entry into two independent placements:
- **Bracket A** (cycle portion): Parent BUY M shares + Child TP M @ P_SELL + Child STP M @ hard_stop. Standard parent-child OCA. All children honor M because parent quantity is also M.
- **Independent BUY** (retention portion): N − M shares at P_BUY, GTC, no TP, no STP. Long-term hold managed by indicator-card monitoring.

When the limit price triggers, both orders fill (IBKR routes them independently at the same price). Net effect = N shares filled at P_BUY, M shares protected by bracket, (N−M) shares held as retention.

**Math identity** (preserves G_grid retention cost):
```
Total cash out:        N × P_BUY
TP fill cash in:       M × P_SELL  (only Bracket A's TP fires)
Net cash committed:    N × P_BUY − M × P_SELL
Net cash per retained: (N × P_BUY − M × P_SELL) / (N − M)
                     = retained_cost from §2 formula
```

So retained_cost is preserved despite the two-order split.

### Reference script template (ib_insync)

```python
from ib_insync import IB, Stock, LimitOrder, StopOrder
import time

ib = IB()
ib.connect('127.0.0.1', 4001, clientId=<unique_per_run>)

# Optional: cancel existing orders for the symbol before re-placing
to_cancel = [t for t in ib.openTrades() 
             if t.contract.symbol == 'SYMBOL' and t.order.orderId in [<ids>]]
for t in to_cancel:
    ib.cancelOrder(t.order)
ib.sleep(4)

sym = Stock('SYMBOL', 'SMART', 'USD')
ib.qualifyContracts(sym)
oca = f"SYMBOL_gridA_OCA_{int(time.time())}"

# ---- Bracket A: BUY M + TP M + STP M (parent-child OCA) ----
parent = LimitOrder('BUY', M, P_BUY, tif='GTC')
parent.transmit = False
parent.account = '<ACCOUNT_ID>'
parent_trade = ib.placeOrder(sym, parent)
ib.sleep(1)
pid = parent_trade.order.orderId

tp = LimitOrder('SELL', M, P_SELL, tif='GTC')
tp.parentId = pid; tp.ocaGroup = oca; tp.ocaType = 1
tp.transmit = False; tp.account = '<ACCOUNT_ID>'
ib.placeOrder(sym, tp)

stp = StopOrder('SELL', M, hard_stop, tif='GTC')
stp.parentId = pid; stp.ocaGroup = oca; stp.ocaType = 1
stp.transmit = True  # last child triggers full bracket transmission
stp.account = '<ACCOUNT_ID>'
ib.placeOrder(sym, stp)

ib.sleep(2)

# ---- Independent BUY: N − M (retention, no TP, no STP) ----
retention = LimitOrder('BUY', N - M, P_BUY, tif='GTC')
retention.account = '<ACCOUNT_ID>'
retention.orderRef = 'SYMBOL_grid_retention'  # tag for clarity in reconcile output
retention.transmit = True
ib.placeOrder(sym, retention)

ib.sleep(3)

# ---- Verify ----
for t in ib.openTrades():
    if t.contract.symbol == 'SYMBOL':
        p = t.order.lmtPrice if t.order.orderType == 'LMT' else t.order.auxPrice
        print(f"ID={t.order.orderId} {t.order.action} {t.order.orderType} qty={t.order.totalQuantity} ${p} parent={t.order.parentId} OCA={t.order.ocaGroup} ref={t.order.orderRef}")

ib.disconnect()
```

### Trigger-action map (Option B-specific)

| Event | What happens |
|---|---|
| Limit price hit | Both Bracket A's parent and the independent BUY fill (IBKR may execute in either order; same price LIMIT GTC, FIFO by submission time) |
| Price reaches P_SELL | Bracket A's TP fires → SELL M shares → STP (OCA-linked) auto-cancels. Retention (N−M) shares untouched |
| Price drops to hard_stop | Bracket A's STP fires → SELL M shares (market) → TP (OCA-linked) auto-cancels. Retention shares **unprotected** — user must close manually if desired |
| Retention shares require exit | User manually closes via IBKR Mosaic (Close Position → MKT or LMT) |

### When to use Option B vs Implementation 1

| Decision factor | Implementation 1 (sequential) | Option B (one-shot) |
|---|---|---|
| User availability | Must be online to react to fill | Can step away |
| Risk preference | Allows "wait and re-evaluate" between fill and SELL placement | Locks in SELL price at entry, no re-evaluation window |
| Discipline alignment | Strictly follows G_grid §2 rule 3 | Violates §2 rule 3 but mitigates with §8 OCO protection |
| Capital commitment | M × P_BUY first, rest as SELL waits for fill confirmation | Full N × P_BUY committed upfront |
| Suitable for | Conservative entries, second+ cycles | First entry, all-in sizing, time-constrained traders |

---

## 14. Maintaining this document

When updating retention ratios, vol tier thresholds, or other constants, version them in §11. Don't silently overwrite. Reference cases in §12 are immutable historical records of actual execution — add new ones, don't modify old ones.
