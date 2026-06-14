---
name: 13master-stock-research
description: 13-Master 六派系投资扫描系统 + 严格 4 步工作流 + 价格双源验真 + 决策面板可视化输出。Use whenever the user requests stock research, equity analysis, position sizing, entry/exit price decisions, batch ticker scoring, sector deep-dives, or any investment workflow involving DeepSeek-based scoring agents. Trigger on phrases like "深度研究"、"建仓"、"加仓"、"评分"、"决策面板"、"研究 XXX 这家公司"、"帮我看看 [ticker]"、"对比 X vs Y"、batch ticker lists, sector themes (HPC/humanoid/rare earth/semiconductor/etc), or any 13-master / agent_v4 / DeepSeek references. Also trigger when user mentions building observation watchlists, price alerts, or portfolio integration decisions.
---

# 13-Master Stock Research Skill

Six-faction investment scanning system with strict 4-step workflow, mandatory price verification, and visual decision panel output.

## Trigger contexts

Use this skill when the user:
- Requests deep research on a specific ticker or batch of tickers
- Wants entry/exit price decisions, position sizing, or stop-loss calibration
- References "13-Master"、"6 派系"、"V/M/H/R/I/G"、"agent_v4"、"DeepSeek 评分"
- Asks for sector/theme deep-dives (e.g. AI infrastructure, humanoid robots, rare earth, photonics, HPC)
- Wants to compare multiple tickers or evaluate against existing holdings
- Asks for an "observation watchlist" or price-alert setup
- Provides a ticker list image/screenshot and asks for batch analysis

## Core principles (non-negotiable)

1. **Facts over assumptions** — When uncertain, say "不确定" (uncertain). Never fabricate data points or extrapolate without source.
2. **Price verification is mandatory** — See `references/price-verification.md`. Every decision panel must satisfy these rules or be regenerated.
3. **Workflow steps cannot be skipped** — Especially step ② (fundamental verification). Jumping from agent scores directly to a decision panel is forbidden.
4. **Agent scores require manual calibration** — See `references/13-master-framework.md`. Raw agent output is a starting point, not the final answer.
5. **Output must be decision-actionable** — Every recommendation must specify entry zone, position cap, stop-loss, and sell trigger. No vague guidance.
6. **Visual decision panels follow strict design rules** — See `references/decision-panel-design.md`. Use the `visualize:show_widget` tool with semantic color tiers.

## The 4-Step Standard Workflow

This is the mandatory order. Do not skip steps. Do not reorder.

### Step 1: Industry + company initial research
- `web_search` for the theme/event anchor first (e.g. valuation benchmark, recent inflection event)
- For each ticker, capture: business description, latest quarter financials (revenue/EPS/backlog), recent 30-day catalysts, management commentary, key contracts
- Identify the **valuation anchor** for any new theme before scoring individual stocks (e.g. for HPC GPU-cloud the anchor was $50M/MW/year from a major hyperscaler-Anthropic deal; for colocation it was ~$1.83M/MW/year). This prevents scoring drift.

### Step 2: Generate agent_v4.py batch command
- Use the single-block bash format from `references/agent-prompt-templates.md`
- Inject theme event context as a shared file referenced by all prompts
- Include API key injection prefix (DeepSeek + price-data API)
- See `references/deepseek-agent-setup.md` for environment setup

### Step 3: Fundamental verification (CRITICAL — DO NOT SKIP)
After receiving agent output:
- For each high-scoring ticker (top quartile) AND each scoring anomaly: web_search the real 5/21-or-latest price + 30-day news
- Every data point must carry: **value / source / timestamp / scope / ⚠️ uncertainty flag**
- Specifically verify: latest quarter financials, recent contracts, insider transactions, management changes, single-day ±10% moves
- Cross-reference agent claims against fresh web data

### Step 4: 13-Master score interpretation + anomaly correction
- Apply the calibration rules from `references/13-master-framework.md`:
  - H faction systematically under-scores non-semiconductor hardware by ~+1.5
  - R faction "wafer scarcity" misjudgments should be reassigned to H
  - Agent same-score with vastly different fundamentals → manual correction required
  - V faction broadly low (≤2) signals sector froth, not scoring error
- Identify and explicitly mark anomalies

### Step 5: Visual decision panel
- See `references/decision-panel-design.md` for the strict design system
- Must include: entry zone / position cap / stop-loss / sell trigger / warning lines
- Must integrate with user's existing holdings (cross-reference for redundancy vs diversification)
- Three-tier classification: 立即可建 / 等回调 / 跳过

## Memory and recall rules

This skill assumes the user maintains a persistent memory store for:
- Existing holdings (core positions + watchlist)
- Past research outputs and watchlist entries with entry triggers
- Sector valuation anchors learned from prior themes
- Lessons from past errors (each correction case must be written to memory immediately, not deferred)

**Critical**: When a user requests a price/data correction or flags an error, write the correction to memory in the same turn using the appropriate memory tool. Never say "我会写入记忆" without actually invoking the memory tool — this is the #1 trust violation pattern.

## Reference files — read these when needed

- `references/13-master-framework.md` — Six factions defined (V/M/H/R/I/G), scoring scale, calibration rules, signal classification, consensus tier definitions. Read whenever scoring or interpreting agent output.
- `references/price-verification.md` — Mandatory price verification rules with anti-failure checklist. Read before EVERY decision panel.
- `references/agent-prompt-templates.md` — Single-block bash command templates for 1, 5, 14, 28-ticker batch runs. Includes theme event context pattern, prompt skeleton, API key injection.
- `references/decision-panel-design.md` — HTML widget design system, color tier semantics, ticker-card templates, metric block patterns, sample code.
- `references/deepseek-agent-setup.md` — Environment configuration, API key handling, log directory conventions, output report format.
- `references/workflow-conventions.md` — Communication style, risk-tiered cadence, memory tool usage rules, existing-holdings integration. Read this when uncertain about how to handle a user request.

## Communication style

- Chinese primary, English tickers and proper nouns kept as-is
- High information density preferred
- No emoji except contextual ⚠️ / ✓ / ❌ markers
- Single-block bash commands (never split across multiple code blocks)
- Acknowledge errors directly and write corrections to memory in same turn
- Disclaimers should be brief — most of the response is the actual analysis

## Anti-patterns (immediately recognize and reject)

| Anti-pattern | Why it's wrong |
|---|---|
| Using agent report timestamp as "current price" | Agent runs lag real-time by 30min-2hr. Re-verify before publishing decision panel. |
| Batch-inferring prices across tickers | Each ticker must have its own web_search with timestamp. |
| Omitting currency (USD/CAD/HKD) for cross-listed names | Caused historical errors (HUT on Nasdaq=USD ≠ TSX=CAD). |
| "Entry zone" guidance for tickers near 52w high | If price is at ATH, output "等回调到 X-Y" instead. Never recommend chasing tops. |
| Agent same-score for fundamentally different tickers | Apply manual correction in step ④. |
| Saying "我会写入记忆" without actually invoking memory tool | Violation of trust — always invoke the tool in the same turn. |
| Skipping step ② to jump to decision panel | The most common workflow violation. Verification is non-negotiable. |
| Recommending a position without specific entry price / position cap / stop / sell trigger | Output is not decision-actionable. |
