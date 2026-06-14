# 13-Master Six-Faction Framework

The scoring system uses six investment "factions" (派系), each representing a school of investment philosophy. Each faction scores 0-10. The overall score is the average, then qualitative tier mapping produces a consensus signal.

## Faction definitions

| Code | Name (中) | Lens | Score-high signals |
|------|----------|------|-------------------|
| **V** | 价值派 (Value) | Earnings, FCF, margins, dividend, P/E vs peers | Stable profits, reasonable multiples, capital return, durable moat |
| **M** | 宏观派 (Macro) | Sector tailwinds, cycle position, fiscal/monetary backdrop | Aligned with cycle, policy tailwinds, secular themes |
| **H** | 硬科技派 (HardTech) | Technology moat, manufacturing depth, R&D leadership | Patents, process leadership, supply-chain criticality |
| **R** | 资源派 (Resource) | Physical scarcity, commodity backing, government strategic interest | Mine/reserve assets, processing monopoly, strategic minerals |
| **I** | 创新派 (Innovation) | Disruptive tech, TAM expansion, new business model | First-mover, platform plays, founder-led, hyper-growth |
| **G** | 地缘派 (Geopolitics) | National security exposure, sanctions positioning, supply chain reshoring | Defense ties, reshoring beneficiaries, sanctions winners |

## Scoring scale

- 0-2: Strong reject for this faction
- 3-4: Weak/skeptical
- 5-6: Neutral / mild positive
- 7-8: Strong positive
- 9-10: Conviction high (rare, usually requires multiple catalysts aligned)

Noise estimate: σ ≈ 0.4-0.5. Score differences <0.5 should be treated as same tier.

## Consensus tier mapping (qualitative output)

After averaging the six factions:
- **HARDTECH_BUYS_ONLY** — H dominates other factions; tech moat trade
- **INNOVATION_BUYS_ONLY** — I dominates; growth/story trade, V faction strongly reject
- **VALUE_REJECTS** — V faction at 1-2 even if other factions high; sector overheating signal
- **SELL** — overall <3.0 with multiple weak factions
- **STRONG_SELL** — overall <2.5, no clear positive faction

## Calibration rules (mandatory adjustments)

These are corrections to systematic biases observed in the agent. Apply BEFORE producing the final decision panel.

### Rule 1: H-faction under-scores non-semiconductor hardware (+1.5)
The agent treats precision mechanical, optical components, industrial sensors, fuel cells, and similar hardware as "less serious tech" than semiconductors. For tickers in actuator, sensor, fuel-cell, motor, machine-vision, lidar, or precision-instrument categories, **add +1.5 to the H-faction score**.

### Rule 2: R-faction "wafer scarcity" misjudgments → reassign to H
The agent sometimes triggers high R-faction scores for semiconductor companies based on "wafer scarcity" framing. R-faction should only be high for actual physical/mineral scarcity (rare earth, uranium, lithium). For semiconductor tickers, ignore R-faction inflation and credit the moat to H instead.

### Rule 3: Same-score with vastly different fundamentals → manual correction
The agent occasionally returns identical scores for tickers with massively different fundamentals (e.g. two HPC neoclouds with $99B vs $69M backlog scoring identically). In this case:
- Down-grade the smaller/weaker one
- Up-grade the larger/stronger one with confirmed contracts
- The historical error cases to recognize: BTDR=CRWV at 4.00 (corrected to 3.4 vs 4.5), KEEL=GLXY at 4.54 (KEEL corrected to 3.5-3.8 due to no anchor tenant).

### Rule 4: V-faction broadly ≤2 = sector froth, NOT scoring error
If across a sector batch, V-faction scores cluster at 1-2 (Value masters all reject), this is a meaningful signal that the entire sector is in a momentum/story regime. Do NOT manually inflate V scores to "fix" them. Instead, treat the V-faction floor as a warning indicator for the user's sizing decision.

### Rule 5: Insider selling / management departures
Agent rarely captures insider transactions. Manually verify via web_search and **subtract 0.5-1.0 from V faction** if multiple executives sold recently within the past month.

### Rule 6: Recent contract announcements not in agent output
Critical contract wins announced in the past 7-14 days are typically missed by the agent. Always verify via 30-day web_search. If a major new contract is found, **add 0.5-1.0 to the relevant faction** (H for tech wins, G for defense/sovereign deals, I for hyperscaler partnerships).

## Optimism bias correction

After applying all faction calibrations, apply a final **−0.3 to −1.5 optimism bias adjustment** to the overall score depending on:
- −0.3: stable large-cap, well-known business
- −0.7: mid-cap with strong narrative
- −1.0: small-cap story stock with limited revenue
- −1.5: pre-revenue or extreme momentum (>50% gain in past month)

## Color coding for visual outputs

When rendering changes/improvements/deterioration:
- **Purple** — qualitative change (regime shift, new model)
- **Green** — improvement / positive surprise
- **Red** — deterioration / negative surprise / risk flag
- **Amber** — caution / wait-state / mixed signals

## Output format expectations

When summarizing scores in a decision panel or table:
```
[TICKER] V=X.X M=X.X H=X.X R=X.X I=X.X G=X.X | avg=X.XX → 校正后=X.XX
Consensus: [tag]
Key thesis: [one sentence]
Key risk: [one sentence]
```
