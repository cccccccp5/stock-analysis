---
name: trading-journal
description: 交易日志与复盘 Skill。触发于「fill」「成交」「复盘」「记录」「纠错」「lesson」。管理 SQLite trade_journal、Markdown 审计、lessons 自学习。每笔实盘必须可追溯。
---

# 交易日志与复盘

## 触发

- `{TICKER} fill {N}股 @{价格}`
- `复盘 本周` / `复盘 本月`
- `纠错 ...` / `写 lesson`
- `持仓` / `最近成交`

## 数据位置

- SQLite：`data/trade_journal.db`
- Markdown：`journal/research|approvals|fills|reviews|lessons/`
- 配置：`config/holdings.yaml`

## fill 记录流程

1. 向用户确认：ticker、side、qty、avg_price、关联策略、是否按 playbook 执行
2. 运行或给出命令：

```powershell
cd d:\个人项目\股票分析\stock-system
.\.venv\Scripts\Activate.ps1
python scripts\trade_logger.py fill --ticker {T} --side {BUY|SELL} --qty {N} --price {P} --strategy {name}
```

3. 在 `journal/fills/` 生成/更新 Markdown（用 templates/fill_record.md）
4. 若为 BUY 且策略含 TP，提示下一步：`出 TP 方案`
5. 更新 `config/holdings.yaml` 中对应持仓（或提示用户更新）

## 复盘流程

```powershell
python scripts\review_weekly.py --output journal\reviews\latest_weekly.md
```

报告须含：
- 成交笔数、买卖汇总
- 计划价 vs 成交价滑点
- 错误标签 Top3（验价缺失/追顶/策略错配/未挂TP/未记录fill）
- 建议写入 lessons 的条目

## 纠错 / lesson

同一轮内必须：
1. 写 `journal/lessons/LESSON_{序号}_{简述}.md`
2. 执行 `python scripts/trade_logger.py lesson --title "..." --tags "..." --body "..."`
3. 告知用户：「已记录 lesson #N，待 weekly 复盘后人工合并进 Skill」

## 错误标签

| 标签 | 含义 |
|------|------|
| 验价缺失 | 未提供盈立第三源仍出清单 |
| 追顶 | ATH 附近仍推荐进场 |
| 策略错配 | 高波小盘用 B 默认等 |
| 滑点过大 | fill 价偏离计划 >2% |
| 未挂TP | fill 后未挂卖单 |
| 未记录fill | 成交超 30 分钟未 log |

## 禁止

- ❌ 说「我会记住」但不写文件/数据库
- ❌ 手改 JSON/SQLite 绕过 trade_logger
- ❌ 自动 merge lesson 进 Skill（必须人工审核）
