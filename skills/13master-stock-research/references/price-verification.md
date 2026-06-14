# Price Verification — Mandatory Rules

Every decision panel that includes price-based recommendations MUST satisfy ALL rules below. If any rule is violated, the panel must be regenerated. This file is the consolidated lesson from past errors.

## The 8 mandatory rules

### Rule 1: Per-ticker individual web_search
- Each ticker must have its own `web_search` call to pull the latest closing price
- **Never** infer ticker B's price from ticker A's batch search result
- For batches of 5+ tickers, run searches one ticker at a time

### Rule 2: Two-source corroboration with timestamps
- Every price must have ≥2 sources cross-referenced
- Acceptable source set: Yahoo Finance + Robinhood + Investing.com + Morningstar + Benzinga + Google Finance + Stock Titan
- Tag the timestamp explicitly: e.g. "5/21 14:23 EDT" or "5/21 close"
- If two sources disagree by >2%, flag as ⚠️ and pull a third

### Rule 3: 52-week high + distance-from-ATH must be displayed
- Every ticker card must show: current price, 52w high, % distance from ATH
- If price is within 5% of ATH → display "ATH 附近" warning badge
- If price is within 10% of ATH → display amber distance label

### Rule 4: "已涨过头" tickers — no entry zone, only "等回调"
- If a ticker is near ATH (within 5%) OR has gained >50% in past month, you MUST NOT recommend an "entry zone"
- Instead, output the **wait-for-pullback zone**: "等回调到 $X-Y"
- Specify the pullback magnitude required (e.g. -15% from current)

### Rule 5: 30-day single-day ±10% move check
- For each ticker, web_search recent ±10% moves within the past 30 days
- These large moves often indicate missed catalysts that change the investment thesis
- Historical failure case: missing a +22% single-day move on a key ticker because of NVDA partnership announcement caused a $26 vs $34 price error

### Rule 6: Agent timestamp ≠ real-time price
- Agent runs (DeepSeek-based scoring) take ~1-30 minutes per ticker
- After agent batch completes, RE-PULL all prices via web_search before producing the decision panel
- Especially critical if agent batch ran >1 hour before the panel is produced

### Rule 7: Currency tagging (USD/CAD/HKD/EUR)
- For cross-listed companies, ALWAYS confirm the trading venue and currency
- Common traps:
  - HUT on Nasdaq = USD, HUT.TO on TSX = CAD (historical 25% error case)
  - IRDM, manufacturer-cross-listed dual-listings
  - European companies (STM as NYSE ADR vs Milan EPA listing — different prices)
- If currency is ambiguous in source, search "ticker market venue" explicitly

### Rule 8: Errors must be written to memory immediately
- When the user catches a price error, the correction goes into the persistent memory store IN THE SAME TURN
- Use the memory tool — do not say "I will write to memory" without invoking the tool
- Failing this rule causes repeated errors and trust loss

## Pre-publication checklist (run mentally before sending decision panel)

For each ticker in the panel:
- [ ] Price has been web_searched within the past 6 hours? Y/N
- [ ] Two sources agree within 2%? Y/N
- [ ] 52w high and % distance from ATH labeled? Y/N
- [ ] If near ATH, "等回调" wording used instead of "进场区间"? Y/N
- [ ] 30-day ±10% moves checked? Y/N
- [ ] Currency tagged? Y/N
- [ ] Recent material news (past 7 days) verified? Y/N

If any answer is No, fix BEFORE publishing.

## Common error patterns to recognize

### Pattern A: Stale agent data
**Symptom**: Decision panel shows prices clearly weeks old.
**Cause**: Used agent report price directly.
**Fix**: Re-verify via web_search at the moment of panel generation.

### Pattern B: Currency mixup
**Symptom**: Price seems wildly off vs intraday data.
**Cause**: Quoted CAD price on a USD trade decision (or vice versa).
**Fix**: Always confirm trading venue before quoting.

### Pattern C: Missing big move
**Symptom**: Recommend entry near "current price" but the ticker actually moved +20% in the past week.
**Cause**: Skipped the 30-day move check.
**Fix**: Run "{ticker} stock 30 day move" or check 1-month % change before publishing.

### Pattern D: Ghost contracts not in agent output
**Symptom**: Decision panel rates a ticker as middling, but a major recent contract win wasn't captured.
**Cause**: Agent ran before the news broke.
**Fix**: Always web_search "{ticker} latest contract announcement 30 days" during step ②.

### Pattern E: Saying "I'll write to memory" without actually doing it
**Symptom**: Same error repeats across sessions.
**Cause**: Verbal acknowledgment not followed by tool invocation.
**Fix**: When user requests memory update, IMMEDIATELY invoke the memory tool, then confirm to user the line number that was added.

## Mandatory price-source query templates

For each ticker:
1. `"{ticker} stock price {today's date}"`
2. `"{ticker} 52 week high low"`
3. `"{ticker} latest earnings {past quarter}"`
4. `"{ticker} news 30 days insider selling contract"`

Run all four BEFORE producing any decision recommendation.
