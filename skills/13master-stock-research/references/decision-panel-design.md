# Decision Panel Design System

The decision panel is the final visual output of the 4-step workflow. It must satisfy strict design rules so the user can scan it in seconds and identify actionable trades.

## Core principles

1. **One-glance lock-in** — The single highest-conviction action (if any) must be visually dominant. Other tiers progressively de-emphasize.
2. **Tier-based color semantics** — Three tiers with distinct visual treatments. No more, no less.
3. **Data density inverse pyramid** — Top tier gets full detail; "wait for pullback" tier gets one line each; "skip" tier gets a compact grid.
4. **Price + ATH distance + tier badge** — Every ticker card must show all three.

## Tier structure

Always classify all candidates into exactly three tiers:

| Tier | Color theme | Badge | Treatment | Typical N |
|------|------------|-------|-----------|-----------|
| 🟢 立即可建 (Buy now) | Green (`c-green`) — `#173404` dark, `#EAF3DE` fill | "立即可建" with green badge | Single hero card, 2px border, full metrics | 0-2 |
| 🟡 等回调 (Wait for pullback) | Amber (`c-amber`) — `#412402` dark, `#FAEEDA` fill | "等回调" with amber badge | Compact row cards, 1-line summary, target price | 2-6 |
| ⚫ 跳过 (Skip) | Gray neutral — `#2C2C2A` dark | "跳过" with dark badge | Dense ticker grid, no per-ticker detail | majority |

## Color and CSS variables (host-provided)

The host environment provides these variables — use them, do not hardcode:

```
--color-background-primary       White surface
--color-background-secondary     Muted surface
--color-background-info          Light blue alert background
--color-text-primary             Body text
--color-text-secondary           Muted text
--color-border-tertiary          0.5px default border
--border-radius-md               8px
--border-radius-lg               12px
```

Color ramps for tier semantics:
```
Green (立即可建):  #EAF3DE fill / #173404 text / #3B6D11 mid
Amber (等回调):   #FAEEDA fill / #412402 text / #BA7517 mid
Red   (警示/止损): #FCEBEB fill / #501313 text / #791F1F mid
Blue  (信息):     #E6F1FB fill / #042C53 text / #185FA5 mid
Gray  (跳过):     #F1EFE8 fill / #2C2C2A text
```

## Hero card template (Tier 1 — 立即可建)

Single highest-conviction pick gets the dominant visual:

```html
<div style="background: var(--color-background-primary); border: 2px solid #3B6D11; border-radius: var(--border-radius-lg); padding: 20px 22px; margin-bottom: 1.75rem;">

  <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 16px;">
    <div>
      <p style="font-size: 22px; font-weight: 500; margin: 0; letter-spacing: -0.5px;">{TICKER}</p>
      <p style="font-size: 12px; color: var(--color-text-secondary); margin: 4px 0 0;">{Company} · {Sector role}</p>
    </div>
    <div style="text-align: right;">
      <p style="font-size: 22px; font-weight: 500; margin: 0; letter-spacing: -0.5px;">${PRICE}</p>
      <p style="font-size: 11px; color: #173404; margin: 4px 0 0; font-weight: 500;">距 ATH {X}% · {timestamp}</p>
    </div>
  </div>

  <!-- Three metric blocks: 进场 / 仓位 / 止损 -->
  <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; margin-bottom: 16px;">
    <div style="background: #EAF3DE; padding: 10px 12px; border-radius: var(--border-radius-md);">
      <p style="font-size: 10px; color: #27500A; margin: 0 0 4px; text-transform: uppercase; letter-spacing: 0.5px;">进场</p>
      <p style="font-size: 16px; font-weight: 500; margin: 0; color: #173404;">${LOW}–{HIGH}</p>
    </div>
    <div style="background: var(--color-background-secondary); padding: 10px 12px; border-radius: var(--border-radius-md);">
      <p style="font-size: 10px; color: var(--color-text-secondary); margin: 0 0 4px; text-transform: uppercase; letter-spacing: 0.5px;">仓位</p>
      <p style="font-size: 16px; font-weight: 500; margin: 0;">{POSITION_SIZE}</p>
    </div>
    <div style="background: #FCEBEB; padding: 10px 12px; border-radius: var(--border-radius-md);">
      <p style="font-size: 10px; color: #791F1F; margin: 0 0 4px; text-transform: uppercase; letter-spacing: 0.5px;">止损</p>
      <p style="font-size: 16px; font-weight: 500; margin: 0; color: #501313;">&lt; ${STOP}</p>
    </div>
  </div>

  <!-- Detail rows -->
  <div style="border-top: 0.5px solid var(--color-border-tertiary); padding-top: 14px;">
    <table style="width: 100%; font-size: 12px;">
      <tr><td style="color: var(--color-text-secondary); padding: 4px 0; width: 90px;">核心叙事</td><td>{One-line thesis}</td></tr>
      <tr><td style="color: var(--color-text-secondary); padding: 4px 0;">关键节点</td><td>{Most recent Q earnings + status}</td></tr>
      <tr><td style="color: var(--color-text-secondary); padding: 4px 0;">催化</td><td>{Next 1-3 months specific catalysts with dates}</td></tr>
      <tr><td style="color: var(--color-text-secondary); padding: 4px 0;">分析师</td><td>{Top 2-3 analyst targets}</td></tr>
      <tr><td style="color: var(--color-text-secondary); padding: 4px 0;">资金</td><td>{Cash / burn / runway}</td></tr>
    </table>
  </div>
</div>
```

## Wait-card template (Tier 2 — 等回调)

Compact 1-line rows. Show current price, distance from ATH, and target pullback price.

```html
<div style="background: var(--color-background-primary); border: 0.5px solid var(--color-border-tertiary); border-radius: var(--border-radius-md); padding: 14px 16px;">
  <div style="display: grid; grid-template-columns: 70px 90px 90px 1fr; gap: 12px; align-items: center;">
    <div>
      <p style="font-size: 15px; font-weight: 500; margin: 0;">{TICKER}</p>
      <p style="font-size: 10px; color: var(--color-text-secondary); margin: 2px 0 0;">{role}</p>
    </div>
    <div style="text-align: right;">
      <p style="font-size: 14px; font-weight: 500; margin: 0;">${PRICE}</p>
      <p style="font-size: 10px; color: #BA7517; margin: 2px 0 0; font-weight: 500;">距 ATH -{X}%</p>
    </div>
    <div style="text-align: right;">
      <p style="font-size: 10px; color: var(--color-text-secondary); margin: 0 0 2px;">等回调</p>
      <p style="font-size: 14px; font-weight: 500; margin: 0; color: #BA7517;">&lt; ${TARGET}</p>
    </div>
    <p style="font-size: 11px; color: var(--color-text-secondary); margin: 0; line-height: 1.4;">{One-line reason + recent catalyst}</p>
  </div>
</div>
```

## Skip-grid template (Tier 3 — 跳过)

Dense grid, ticker names only. No price detail.

```html
<div style="background: var(--color-background-secondary); border-radius: var(--border-radius-md); padding: 14px 16px; margin-bottom: 1.75rem;">
  <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px 14px; font-size: 11px;">
    <span style="color: var(--color-text-secondary);">{TICKER1}</span>
    <span style="color: var(--color-text-secondary);">{TICKER2}</span>
    <!-- ... -->
  </div>
</div>
```

## Top counter row

Open the panel with a counter showing total candidates and the actionable count:

```html
<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 2rem;">
  <div style="background: var(--color-background-secondary); padding: 14px 16px; border-radius: var(--border-radius-md);">
    <p style="font-size: 11px; color: var(--color-text-secondary); margin: 0 0 4px;">可建仓</p>
    <p style="font-size: 28px; font-weight: 500; margin: 0; color: #173404;">{N1}<span style="font-size: 14px; color: var(--color-text-secondary); font-weight: 400; margin-left: 4px;">/ {TOTAL}</span></p>
  </div>
  <div style="background: var(--color-background-secondary); padding: 14px 16px; border-radius: var(--border-radius-md);">
    <p style="font-size: 11px; color: var(--color-text-secondary); margin: 0 0 4px;">等回调</p>
    <p style="font-size: 28px; font-weight: 500; margin: 0; color: #BA7517;">{N2}<span style="font-size: 14px; color: var(--color-text-secondary); font-weight: 400; margin-left: 4px;">/ {TOTAL}</span></p>
  </div>
</div>
```

## Tier badges

Place at the start of each tier section:

```html
<!-- Green: 立即可建 -->
<span style="background: #173404; color: #EAF3DE; font-size: 10px; font-weight: 500; padding: 3px 8px; border-radius: var(--border-radius-md); letter-spacing: 0.3px;">立即可建</span>

<!-- Amber: 等回调 -->
<span style="background: #412402; color: #FAEEDA; font-size: 10px; font-weight: 500; padding: 3px 8px; border-radius: var(--border-radius-md); letter-spacing: 0.3px;">等回调</span>

<!-- Dark: 跳过 -->
<span style="background: #2C2C2A; color: #F1EFE8; font-size: 10px; font-weight: 500; padding: 3px 8px; border-radius: var(--border-radius-md); letter-spacing: 0.3px;">跳过</span>
```

## Final "actionable summary" block

End the panel with a clear next-action block on info-blue background:

```html
<div style="background: var(--color-background-info); border-radius: var(--border-radius-md); padding: 14px 16px;">
  <p style="font-size: 13px; font-weight: 500; margin: 0 0 8px; color: #042C53;">现在做这件事</p>
  <p style="font-size: 12px; color: #042C53; margin: 0; line-height: 1.7;">
    {One concrete primary action} <br>
    {What NOT to do} · {What to wait for}
  </p>
</div>
```

## Followup buttons

Always include 3-5 followup `sendPrompt()` buttons. These appear after the panel and allow one-tap continuation:

```html
<div style="margin-top: 16px; display: flex; gap: 8px; flex-wrap: wrap;">
  <button onclick="sendPrompt('{specific followup 1}')" style="font-size: 12px;">{Label 1} ↗</button>
  <button onclick="sendPrompt('{specific followup 2}')" style="font-size: 12px;">{Label 2} ↗</button>
  <button onclick="sendPrompt('{specific followup 3}')" style="font-size: 12px;">{Label 3} ↗</button>
</div>
```

Common followup themes:
- "把 {TICKER} 加入观察池写入记忆 标注进场价 ${X-Y} 仓位 {N} 止损 ${Z}"
- "{TICKER_A} vs {TICKER_B} 深度对比 我应该选哪个建仓"
- "{TICKER} 加价格提醒到观察池"
- "{TICKER} {date} 财报情景演练"

## Pre-render checklist

Before calling `show_widget`, verify:
- [ ] Every Tier-1 ticker price has been web_searched within 6 hours
- [ ] 52w high + % distance from ATH labeled on every card
- [ ] Position size specified as fraction of user's core position (e.g. "MU × 1/5")
- [ ] Stop-loss specific (not "if it drops a lot")
- [ ] Followup buttons relevant and concrete (no generic "tell me more")
- [ ] No more than 2 candidates in 立即可建 tier (forces selectivity)
- [ ] If 0 candidates in 立即可建, the panel says so clearly and pivots to "watch list mode"

## What NOT to do

- Don't put all tickers at the same visual weight — that defeats the purpose
- Don't include scoring tables in the main panel (those go in step ③ communication, not the panel itself)
- Don't use more than 3 colors per panel (green / amber / blue plus neutral grays)
- Don't add box-shadows, gradients, or decorative effects
- Don't use emoji (the host design system prohibits them)
- Don't recommend entry zones for tickers at 52w high — switch to "等回调"
- Don't paste raw agent JSON or score tables in the panel — synthesize into prose + cards
