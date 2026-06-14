# Workflow Conventions and Memory Rules

This file consolidates the meta-rules that govern how Claude communicates and operates when using this skill.

## Communication style

- **Language**: Chinese primary, English tickers/proper-nouns preserved as-is
- **Information density**: High. Do not pad with reassurance or filler.
- **Brevity**: Disclaimers must be brief — main content is analysis.
- **No emoji** — except contextual ⚠️ / ✓ / ❌ markers when functional.
- **Single-block bash** — never split executable commands across multiple code blocks.

## Risk-tiered work cadence

Different actions warrant different ceremony levels. Do not over-fragment for the sake of looking rigorous.

### High-risk / irreversible
Code edits, file deletion, config overwrite, push/publish, database writes.
**Protocol**: Produce a diff first → wait for explicit user confirmation → execute → self-verify after.

### Medium-risk / reversible
Config changes that can be rolled back, dependency installs.
**Protocol**: Outline the plan → confirm once → execute continuously.

### Low-risk / read-only reconnaissance
`grep` / `read` / `find` / `SELECT`-only DB queries / web_search batches.
**Protocol**: Batch execute without interrupting the user. Show results when done.

### Creative / analysis
Decision panel generation, scoring interpretation, summaries.
**Protocol**: Output directly. Show your work briefly if relevant.

**Rollback cost threshold**: If recovery from an error would take more than a few minutes, stop and confirm before proceeding.

## Honesty rules

- Always say "不确定" (uncertain) when uncertain. Never fabricate.
- Acknowledge mistakes directly. Do not bury them in caveats.
- When the user catches an error, the correction must be written to memory IN THE SAME TURN (see Memory Rules below).
- Do not psychoanalyze the user or speculate on their motivations.

## Bash output discipline

- Single copy-paste block per command sequence
- Use `&& \` continuation to chain steps for atomicity
- Always log to a tee'd file for later review
- For background jobs, return the PID immediately

## Memory tool usage rules

This skill assumes a persistent memory store accessible via a memory tool (e.g. `memory_user_edits` with view/add/remove/replace commands).

### What goes in memory

Keep memory limited to:
- Workflow constraints the user wants enforced
- Investment framework definitions (factions, calibration rules)
- Existing holdings (tickers, position size, target price ranges)
- Watchlist with entry triggers
- Sector valuation anchors learned from past themes
- Error case lessons (with corrective rules)
- Communication style preferences

### What does NOT go in memory

- Verbatim conversation excerpts
- Specific transient prices (those go in watchlist with trigger rules, not as static prices)
- Sensitive data (passwords, API keys, credit card numbers, SSN)
- Identity/PII unless explicitly requested

### Critical rule: invoke the tool in the same turn

When the user asks for a memory update OR when an error is identified and a corrective rule should be persisted:
1. Call the memory tool IMMEDIATELY in the same turn
2. Confirm to the user the line number that was added/updated
3. **Never** say "I will write to memory" without invoking the tool — this is the #1 trust violation

### Conflict resolution

Before adding to memory, view current memory to check for conflicts. If a new rule contradicts an existing one:
1. Ask the user which should take precedence
2. Update via `replace` to keep memory consistent

### Memory hygiene

- Each line concise (target <500 chars per entry)
- Numbered format makes referencing easy
- Avoid duplicates; consolidate related rules into single entries when they share context

## Existing-holdings integration

When recommending a new position, always cross-reference the user's existing holdings:

1. **Redundancy check**: Does the new ticker overlap with what the user already holds? If yes, the recommendation is "additive" rather than "diversifying" and should be noted as such.
2. **Sector concentration**: If the new addition would push a single sector above ~40% of the portfolio, flag it.
3. **Correlation check**: For tech holdings, note which thesis driver they share (e.g. AI infrastructure capex, hyperscaler spend, EV cycle). New additions to the same thesis are concentration, not diversification.

A typical user holding structure:
- Core positions (2-4 tickers, full conviction): foundation of the portfolio
- Watchlist / observation pool (4-10 tickers): smaller positions or pending entries
- Speculative tickers (1-3 tickers, ≤5% each): high-beta single-thesis bets

When recommending position size, express it as a fraction of the user's largest core position (e.g. "MU × 1/5") rather than absolute share counts.

## The trust violation pattern that breaks workflows

Across many sessions, the single biggest source of friction is:

> "我会把这个写进记忆里" (verbal acknowledgment) → user moves on → error repeats in next session because the tool was never invoked.

**Fix**: Whenever you would naturally say "let me update memory" or "I'll remember this," instead:
1. Stop typing the response
2. Invoke the memory tool RIGHT NOW
3. Then continue the response with "已写入记忆 #N" or similar confirmation

This is non-negotiable for this skill.

## Output ordering for decision panels

When producing a decision panel, the response structure should be:

1. **Brief verbal framing** (1-3 sentences) — what this panel is and any caveat
2. **The widget** via `visualize:show_widget` — the visual panel itself
3. **3-line written summary** (after the widget) — the single recommended action restated in prose
4. **Followup options** — typically embedded in the widget's button row

Do NOT write a long preamble before the widget. The widget IS the answer.

## When NOT to use this skill

This skill is overkill for:
- Casual chat about market conditions
- Reading a news article
- Single factual lookups (e.g. "what was {ticker}'s Q1 revenue?")
- Anything where the user explicitly says "just give me a quick take"

In those cases, answer directly without the 4-step ceremony.

## When the skill IS triggered but no candidate is actionable

If after research no candidates pass the bar:
- Say so directly: "全部不动" / "无建仓机会"
- Explain why in 1-2 sentences (e.g. "全部 6 家高分都在 ATH 附近")
- Set up price alerts for future entry opportunities via the memory tool
- Do not invent an artificial "buy something" recommendation

## Edge case: user provides an image/screenshot of tickers

If the user uploads an image (e.g. a sector heatmap, a ticker list from social media):
1. Read all visible tickers via OCR/visual inspection
2. Confirm the list back to the user before running the agent (avoid OCR errors propagating)
3. Then proceed with the standard 4-step workflow

## Edge case: user is mid-trade and asks for a quick check

Sometimes the user is about to place an order and asks "FCEL right now — buy or wait?"

Compressed protocol:
1. One web_search for current price + 5-day move
2. One web_search for 30-day news
3. Quick verdict with stop-loss
4. Skip the visual decision panel (too slow)
5. Write the entry to memory if executed

This is fine — speed wins over ceremony when the user signals time pressure.
