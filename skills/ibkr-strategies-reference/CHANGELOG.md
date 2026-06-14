# Changelog

## v2 (2026-05-22)

### Added

- **`references/ibkr_quirks.md`** — New reference doc capturing 8 IBKR API quirks discovered during real-money execution. Read this BEFORE first order placement.
- **`references/grid_strategy.md` §13** — "Option B: Dual-order structure" — workaround for IBKR's bracket child-qty constraint that allows G_grid 3:2 retention to coexist with one-shot bracket placement.
- **`references/grid_strategy.md` Phase C Mode 2** — "All-in single-cycle" sizing mode for users who want to deploy the entire stated budget on one symbol immediately, rather than the default ≥3-parallel-cycle conservative sizing.
- **`SKILL.md` Path 2 Phase G** — Added "Implementation 2: One-shot bracket with OCA protection" alongside the original "wait for fill" Implementation 1, with decision matrix for choosing between them.
- **`references/grid_strategy.md` Phase A2** — Upgraded from "two-source verification" to **"triple-source verification"** (web A + web B + user broker screenshot / IBKR live quote). Documents the failure case where all three web sources displayed the previous day's close as "current".

### Changed

- **`references/grid_strategy.md` §11 history** — Added v2 entry documenting the new modes / quirks.
- **`SKILL.md` Workflow at a glance Path 2** — Phase C explicitly mentions the two sizing modes; Phase G explicitly mentions the two implementations.
- **`references/grid_strategy.md` §12** — Reference case updated to show the all-in sizing math (N=180, M=120, retained=60, retained cost $42.00) using Option B's dual-order structure.

### Removed (privacy scrub)

- All specific IBKR account IDs replaced with `<ACCOUNT_ID>` / `<YOUR_ACCOUNT_ID>` placeholders
- All specific position data (existing holdings in former v1)
- All personal references (researcher's nickname, communication app references)
- Cloud server IPs and SSH paths
- Brokerage-specific absolute path examples (replaced with `~/`)
- All specific ticker references in body text, EXCEPT for the §12 reference case which uses a generic "high-vol AI-infra name" descriptor and abstract numbers ($55.60 / $62.40 / $35.90) — these are kept for math clarity.

### Rationale for changes

The v1 of this skill captured a clean theoretical SOP for G_grid. In execution, two issues emerged:

1. **Sizing**: The "≥3 parallel cycles" constraint was too conservative for a user who wanted to deploy $10k all-in on a single symbol. v1's default sizing would have used only ~16.6% of the stated budget per cycle, dramatically underspending. v2 adds Mode 2 to explicitly support all-in.

2. **One-shot bracket**: G_grid §2 rule 3 ("wait for fill before placing next layer") is excellent discipline for cycling traders who are always at the screen, but a user wanting offline protection needs SELL TP and STP placed before stepping away. SOP §8 OCO protection was supposed to address this, but real placement revealed IBKR forces child qty = parent qty, breaking 3:2 retention. v2 §13 Option B is the workaround.

Both improvements emerged from a single afternoon of real-money execution. Documenting them prevents the next user from rediscovering the same lessons painfully.

---

## v1 (2026-05-22 morning)

### Initial release

- Core SKILL.md with A+ bracket and G_grid_accumulate strategies
- `references/strategies.md` with 8 exit strategies
- `references/grid_strategy.md` with Phase A → H SOP (Mode 1 sizing only, Implementation 1 placement only)
- `references/tick_rules.md` (not included in v2 shareable package — implementation-specific)
- `references/categories.md` (not included — user-maintained)
- `references/workflows.md` (not included — user-maintained)
- `references/holdings.md` (not included — contains personal positions)
