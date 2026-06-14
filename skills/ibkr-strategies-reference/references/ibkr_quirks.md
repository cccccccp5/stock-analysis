# IBKR API Quirks & Workarounds

Hard-won lessons from real-money execution on Interactive Brokers (TWS API via `ib_insync`). Read this BEFORE placing your first real order. Each quirk has been validated with live trades and documented to prevent recurrence.

---

## Quirk #1: Web 3-source price stale-cache trap

### Symptom

You web-search a ticker's price from 3 independent sources (e.g. Yahoo Finance, Investing.com, Morningstar). All three report the same number. Confidence is high. You proceed to compute your anchor based on that price.

Then you ask the user for an in-app screenshot, and the actual broker price is **~10% different**.

### Root cause

All three "independent" web sources may share the same upstream data feed (e.g. NASDAQ TotalView or IEX cloud), and that feed can lag — they all display **the previous day's close while labeling it as the current day's price**. You think you've triangulated; you've actually consulted three mirrors of the same stale cache.

### Real example (2026-05-22)

For ticker IREN:
- Yahoo Finance: "$52.71 +4.97 (+10.41%) At close: May 20 4:00 PM EDT" — labeled as 5/20, accurate for that date
- Investing.com: "As of May 21, 2026, IREN is trading at a price of $52.710 USD, with a previous close of $52.710" — labeled 5/21, but the price is actually 5/20's close
- Morningstar: "Price $52.68 May 20, 2026" — labeled 5/20

User's broker app screenshot of 5/21 close: **$58.06 (+10.15%)** — IREN had its second consecutive ~10% green day on 5/21. The web sources didn't reflect it; all three were showing 5/20's close.

Anchor would have been miscalculated by -10.2%.

### Workaround

**Triple-source verification requires THREE independent sources, where one is a non-web source**:
- Source A: web (Yahoo / Investing / Morningstar / TradingView / CNBC, pick 1)
- Source B: a DIFFERENT web source
- Source C: **user's own real-time broker app screenshot** OR an IBKR live quote (delayed 15min is fine)

Match criteria:
- All 3 within 0.5% → use the average
- A+B agree, C differs >2% → **STOP, web cache is stale**
- A and B disagree >2% → STOP, conflicting data
- Time stamps must be within 5 trading days

### Operational notes

- When user is in a different timezone, their "broker screenshot" might be from many hours ago — but as long as it's the previous trading day's close, it's authoritative.
- `python status.py --symbol X` may or may not output a live quote depending on implementation (see Quirk #4).
- `python place_list.py` typically prints market price in its DRY-RUN summary; use that as Source C if you have it.

---

## Quirk #2: Bracket order child quantity is forced to parent quantity

### Symptom

You construct a parent + child bracket via `ib_insync`:
```python
parent = LimitOrder('BUY', 30, 55.60, tif='GTC')
parent_trade = ib.placeOrder(stock, parent)
pid = parent_trade.order.orderId

tp = LimitOrder('SELL', 20, 62.40, tif='GTC')  # ← intentionally 20, not 30
tp.parentId = pid
tp.transmit = True
ib.placeOrder(stock, tp)
```

You expect TP to have qty=20. After placement, you query `ib.openTrades()` and see TP qty = **30** — IBKR silently rewrote your child quantity to match the parent.

### Root cause

IBKR's order management system enforces a "child orders must cover the full parent fill" invariant on bracket parent-child relationships. When you submit a child with `parentId` set and the child's quantity differs from the parent's, IBKR overrides the child quantity. This is by design — it prevents accidental under-coverage where, say, parent fills 30 but child only protects 20.

This is NOT a bug in `ib_insync`; it's an IBKR API behavior.

### Impact on G_grid_accumulate strategy

G_grid's core math relies on **buy N, sell M (where M < N)**, retaining (N - M) shares at a discounted net cost. Standard parent-child bracket structure forces M = N, breaking the retention mechanic.

### Workaround: Dual-order structure (Option B)

Instead of a single bracket, split the entry into two independent placements:

1. **Bracket A (cycle portion)**: Parent BUY M + Child TP M + Child STP M, all parent-child OCA-linked
2. **Independent BUY (retention portion)**: Buy (N − M) at the same price, GTC, no TP, no STP

When the limit price triggers, both orders fill at the same price level. The user's net position is N shares at P_BUY, but M of those are protected by the bracket (TP at P_SELL or STP at hard_stop), and (N − M) are unprotected (managed by indicator-card monitoring).

**Math identity** (preserves retention cost):
```
Total cash deployed:   N × P_BUY
TP fill cash returned: M × P_SELL  (only Bracket A's TP fires)
Net cash committed:    N × P_BUY − M × P_SELL
Net cost per retained: (N × P_BUY − M × P_SELL) / (N − M)
                     = G_grid retained_cost formula
```

So the G_grid retention math is preserved despite the order split.

### When this matters

- For 3:2 retention with strict ratios: N must be a multiple of 30, M = N × 2/3
- For 2:1 retention: N must be a multiple of 30, M = N / 2 → trivially clean
- For 4:3 retention: N must be a multiple of 40, M = N × 3/4 → keeps clean math

### Alternative that does NOT work

❌ **OCA-only without parent-child** (i.e. independent SELL TP + SELL STP with `ocaGroup` set but no `parentId`):

When BUY hasn't filled yet, the SELL TP and SELL STP are already active. If price spikes above the TP before BUY fills (e.g. premarket gap), the SELL TP fires and you end up **naked short**. Same for STP if price gaps down.

Parent-child is the mechanism that gates child activation on parent fill. You lose that with OCA-only.

---

## Quirk #3: Reduce-only flag is not exposed in `ib_insync` Order standard fields

### Context

When placing a STP order intended only to close an existing position (not to open a new short), you'd like to mark it as "reduce-only" so IBKR rejects the order if no position exists.

### Symptom

`ib_insync`'s `Order` class doesn't have a `reduceOnly` field in standard usage. Setting it via `Order.algoStrategy` or `Order.orderRef` doesn't work for stocks.

### Workaround

For brackets: rely on parent-child relationship — child orders only activate after parent fills, so a "naked STP" scenario is naturally prevented.

For non-bracket SELL/STP: place them only **after** BUY fill (the "wait for fill" discipline). This is why G_grid's standard SOP §2 rule 3 mandates this discipline.

For retention shares with no auto-STP: monitor manually via IBKR Mosaic price alerts.

---

## Quirk #4: `status.py` may not output a live quote

### Symptom

You expect `python status.py --symbol X` to print the current market price. Instead, it only shows positions and open orders, with no quote line.

### Cause

Many `status.py` implementations filter positions/orders by symbol but don't actively request a market data subscription for the queried symbol. The market price isn't pulled unless explicit code does so.

### Workaround

1. **Use `place_list.py` for quotes**: Its DRY-RUN summary typically prints "当前市价: $X" before asking for confirmation. You can run a tiny test order (e.g. BUY 1 share at $0.01, never fills, but the DRY-RUN shows the quote) and answer "N" at the prompt.
2. **Use the broker GUI**: IBKR Mosaic or TWS shows live (or 15min-delayed) prices natively.
3. **Add quote functionality to `status.py`**: implement `ib.reqMktData(contract)` + read `ticker.last` after a short wait. Note that without a market data subscription, you'll see Warning 10167 and get 15-minute-delayed prices ("DELAYED_FROZEN" market data type).

### Implementation snippet

```python
from ib_insync import IB, Stock

ib = IB()
ib.connect('127.0.0.1', 4001, clientId=99)

stock = Stock('SYMBOL', 'SMART', 'USD')
ib.qualifyContracts(stock)

ib.reqMarketDataType(4)  # 4 = DELAYED_FROZEN, falls back to delayed if no live subscription
ticker = ib.reqMktData(stock, '', False, False)
ib.sleep(2)
print(f"Last: ${ticker.last}, Bid: ${ticker.bid}, Ask: ${ticker.ask}")
ib.cancelMktData(stock)
ib.disconnect()
```

---

## Quirk #5: zsh doesn't support bash's `read -p prompt` syntax

### Symptom

On macOS (default shell zsh as of macOS Catalina+), the following bash idiom fails:
```bash
read -p "Continue? " answer
```
Error: `read: -p: no coprocess`

This breaks any multi-line script that uses interactive gates between command stages.

### Cause

zsh's `read` builtin uses a different syntax. The `-p` flag in zsh means "use coprocess for input", not "prompt string".

### Workarounds

**Option A: Use zsh-native prompt syntax**:
```bash
read "?Continue? " answer
```
(Question mark inside the quoted argument, no `-p` flag.)

**Option B: Print prompt with `echo -n`, then plain `read`**:
```bash
echo -n "Continue? "
read answer
```
This works on both bash and zsh.

**Option C: Skip interactive gates altogether**:
For high-risk operations, use the tool's built-in confirmation prompts (e.g. `place_list.py` prints DRY-RUN then asks "Confirm? [y/N]"). Don't add a second gate on top.

### Recommendation

For shareable scripts that might run on bash or zsh, use **Option B** (universally compatible).

---

## Quirk #6: Multi-account IBKR session can confuse position/order routing

### Symptom

Your IBKR login has multiple accounts (e.g. primary `Uxxxxxxx` and family `Uxxxxxxx`). When placing an order without explicitly setting `account=...`, IBKR may either:
- Route it to the primary account (default behavior)
- Reject with error 435 ("default account is invalid")

### Workaround

**Always set `account=...` explicitly on every `Order`**:
```python
order = LimitOrder('BUY', 100, 55.60, tif='GTC')
order.account = '<YOUR_ACCOUNT_ID>'  # explicit, not relying on default
```

Verify the connected account via `ib.managedAccounts()`:
```python
ib.connect(...)
print(ib.managedAccounts())  # → ['<ACCOUNT_1>', '<ACCOUNT_2>'] for multi-account login
print(ib.client.getAccounts())  # which is "current default"
```

---

## Quirk #7: Order ID resets to 1 when IB Gateway / TWS restarts

### Symptom

Yesterday your latest IREN order was orderId=43. Today, you restart IB Gateway. You place a new order and it comes back as orderId=5. Your snapshot files reference IDs from yesterday that now collide with today's IDs.

### Cause

IBKR's order IDs are session-scoped, not globally unique across restarts. The next-ID counter resets per Gateway session.

### Workaround

For long-term tracking, use the **`permId`** field instead of `orderId`:
- `orderId` = session-scoped, resets on restart
- `permId` = globally unique permanent ID assigned by IBKR after order acknowledgment

In `ib_insync`:
```python
trade = ib.placeOrder(contract, order)
ib.sleep(1)  # wait for IBKR to assign permId
permanent_id = trade.order.permId  # use this for long-term reconciliation
```

For snapshot files, store both `orderId` (current session) and `permId` (long-term identity).

---

## Quirk #8: Market data subscription warnings can be ignored if delayed data is acceptable

### Symptom

You see warnings like:
```
Warning 10167: 请求的市场数据没有订阅。显示延迟市场数据
Warning 2104, 2106, 2158: market data farm / historical data / sec-def connections normal
```

### Cause

- **10167**: You don't have a paid live market data subscription for this exchange. IBKR falls back to 15-minute-delayed data.
- **2104/2106/2158**: These are connection status acknowledgments, not errors. Connection is healthy.

### Action

- For long-horizon strategies (G_grid, A+ bracket with hold periods of days to weeks), **15-min delayed data is fine**. No subscription needed.
- For day-trading or scalping, subscribe to live market data for the relevant exchanges.
- The 2104/2106/2158 warnings can always be ignored.

---

## Summary table

| Quirk | Severity | Workaround complexity |
|---|---|---|
| #1: Web 3-source stale cache | **HIGH** (can cause 10%+ anchor errors) | Low (add user-screenshot check) |
| #2: Bracket child qty forced to parent | **HIGH** (breaks G_grid retention) | Medium (dual-order structure) |
| #3: Reduce-only flag not exposed | Medium | Low (use bracket or wait-for-fill) |
| #4: `status.py` no live quote | Medium (operational annoyance) | Low (use alternative quote sources) |
| #5: zsh `read -p` incompatibility | Low (script-level only) | Low (use `read "?prompt"` or `echo -n` + `read`) |
| #6: Multi-account routing | Medium | Low (always set `account=...`) |
| #7: orderId resets on restart | Low (only matters for cross-session tracking) | Low (use `permId` for long-term ID) |
| #8: Market data subscription warnings | Low | None needed (acceptable for slow strategies) |

---

## Adding new quirks

When you discover a new IBKR behavior during real-money execution, document it here with:
1. **Symptom** (what you saw)
2. **Root cause** (why it happened, with IBKR API context if known)
3. **Workaround** (concrete code or procedure)
4. **Real example with date** (so future readers can confirm the behavior hasn't changed)

Future readers thank you.
