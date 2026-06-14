---
name: usmart-trading-playbook
description: 盈立证券手动执行 Playbook。触发于「建仓」「网格」「G_grid」「挂单清单」「Bracket」「出 TP」「盈立挂单」。将 IBKR 策略数学转为盈立 App/PC 客户端 GTC 限价单清单。不调用 place_bracket.py 等 IBKR 脚本。无 Open API 阶段，第三源验价为盈立截图或用户报现价。
---

# 盈立执行 Playbook

## 触发

- `建仓 X N股` / `place bracket X`
- `网格 X $Y` / `G_grid X $Y`
- `出 TP 方案` / `挂止盈`
- `X fill N股 @价格`（后续卖单）

## 铁律

1. **三源验价未完成 → 禁止输出带美元价格的挂单清单**
2. 源 A + 源 B：不同财经网站（AI web_search）
3. 源 C：**盈立 PC 客户端或 App 截图 / 用户打字报价**（本阶段无 API）
4. A/B 一致但 C 差 >2% → STOP，以盈立 C 为锚重算
5. 输出的是【盈立挂单清单】，不是 Python 下单命令
6. 用户「确认」≠ 已下单；以盈立实际成交为准
7. fill 后 30 分钟内必须引导用户记录到 trading-journal

## 策略参考

策略数学与决策树见同目录上级：
`skills/ibkr-strategies-reference/references/strategies.md`
`skills/ibkr-strategies-reference/references/grid_strategy.md`

标的默认策略见 `config/categories.yaml`。

## 流程 A：A+ Bracket（单次建仓）

### Phase A 三源验价

1. web_search 源 A（Yahoo / Morningstar 等）
2. web_search 源 B（Investing / TradingView 等，须与 A 不同站）
3. **向用户索取源 C**：

```
请提供盈立第三源验价（任选其一）：
· 盈立 App/PC 客户端 IREN 报价截图
· 或打字：盈立 <TICKER> $<价格> <USD/HKD> <盘中/收盘>
无第三源我将停止，不输出挂单清单。
```

4. 输出验价快照表，判定通过/停止

### Phase B–D 算价

- 读 `config/categories.yaml` 定默认策略（可 override）
- 按 strategies.md 算 BUY / TP1-3 / STP
- SELL 限价尾数优先 .40 / .90（可选，提高成交率习惯）

### Phase E 输出挂单清单

```markdown
# 盈立挂单清单 · {TICKER} · {策略} · {timestamp}

## 验价快照
| 源 | 价格 | 时间 | 备注 |
| 源A | | | |
| 源B | | | |
| 盈立C | | | 截图/用户报价 |

## 订单
| # | 方向 | 数量 | 限价 | 类型 | 说明 |
| 1 | BUY | | | GTC | 进场 |
| 2 | SELL | | | GTC | TP1 |
...

## 止损提醒
硬止损 < $X → 盈立市价平仓或条件单

## 成交后
fill 后发送：{TICKER} fill {N}股 @{价格}
```

## 流程 B：G_grid 网格

严格参照 `grid_strategy.md` Phase A–H 的**数学与纪律**，执行改为手动：

### Phase A（不可跳过）

- 三源验价（同上，必须盈立 C）
- 52w high、5d range、30d 事件、Beta/HV
- 定 Vol Tier → 网格宽度、3:2 保留

### Phase B–F

- 算 P_BUY、P_SELL、N、M、保留成本、软/硬止损
- 输出完整 G_grid 审批表 + 盈立挂单清单

### Phase G（手动）

- 首层：BUY N @ P_BUY GTC
- fill 后：SELL M @ P_SELL GTC
- 保留 (N-M) 股不设卖单

### Phase H 指标卡

输出 4 个盈立到价提醒及触发动作表（见 grid_strategy.md Phase H）。

## 禁止

- ❌ 输出 place_bracket.py / place_list.py 命令
- ❌ 无盈立第三源时给具体 $ 价格
- ❌ 假设 fill 价格 = BUY 限价（成交后按实际均价重算 TP）
