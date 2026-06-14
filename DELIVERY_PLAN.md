# 个人股票投资系统 · 完整方案与交付步骤

> 适用环境：Windows + Cursor + 盈立（无 Open API）+ 飞书 + Hermes  
> 执行原则：研究决策自动化、实盘下单手动、三源验价（盈立截图/报价为第三源）、每笔可追溯、复盘驱动规则进化

---

## 目录

1. [系统总览](#1-系统总览)
2. [交付阶段一览](#2-交付阶段一览)
3. [阶段 0：环境与目录初始化](#阶段-0环境与目录初始化)
4. [阶段 1：Skill 与配置文件](#阶段-1skill-与配置文件)
5. [阶段 2：交易日志与复盘基础](#阶段-2交易日志与复盘基础)
6. [阶段 3：盈立手动执行流程固化](#阶段-3盈立手动执行流程固化)
7. [阶段 4：飞书 + Hermes 对话入口](#阶段-4飞书--hermes-对话入口)
8. [阶段 5：持续记忆与自学习闭环](#阶段-5持续记忆与自学习闭环)
9. [阶段 6：验收与日常 SOP](#阶段-6验收与日常-sop)
10. [附录 A：飞书指令表](#附录-a飞书指令表)
11. [附录 B：盈立执行手册摘要](#附录-b盈立执行手册摘要)
12. [附录 C：三源验价操作细则](#附录-c三源验价操作细则)
13. [附录 D：Hermes 定位与边界](#附录-dhermes-定位与边界)

---

## 1. 系统总览

### 1.1 架构

```
飞书对话（Hermes）          Cursor 桌面（深度研究）
        │                           │
        └──────────┬────────────────┘
                   ▼
        ┌──────────────────────┐
        │  Skill 三件套         │
        │  · 13-Master 研究     │
        │  · 盈立执行 Playbook  │
        │  · 交易日志与复盘     │
        └──────────┬───────────┘
                   ▼
        ┌──────────────────────┐
        │  SQLite + Markdown   │  ← 每笔决策/成交/复盘
        │  + 飞书多维表格       │
        └──────────┬───────────┘
                   ▼
              盈立 App/PC 客户端
              （手动挂 GTC，截图验价）
```

### 1.2 组件分工

| 组件 | 做什么 | 不做什么 |
|------|--------|----------|
| **Cursor** | 批量研究、改 Skill、Canvas 决策面板 | 7×24 飞书值守 |
| **Hermes + 飞书** | 手机发指令、收清单、Cron 周报 | 直连盈立下单 |
| **13-Master Skill** | 六派系研究、验价、决策三档 | 自动交易 |
| **盈立 Playbook Skill** | 算价 → 输出挂单清单 | 代替你点下单 |
| **交易日志 Skill** | 记录 fill、周复盘、写 lessons | 自动改止损比例 |
| **盈立客户端/App** | 第三源验价、手挂 GTC | 被 AI 直接操控（无 API 阶段） |

### 1.3 核心纪律（全程有效）

1. **三源验价**：Web A + Web B + 盈立截图/报现价；缺第三源不出挂单清单  
2. **事前定规则**：进场、仓位、止损、止盈档位入场前写死  
3. **确认才执行**：飞书/Hermes 出清单 → 你确认 → 盈立手挂  
4. **fill 必记录**：成交后 30 分钟内回报，写入 SQLite + Markdown  
5. **规则人工合并**：复盘教训写入 `lessons/`，人工审核后才进 Skill  

---

## 2. 交付阶段一览

| 阶段 | 名称 | 完成标志 |
|------|------|----------|
| **0** | 环境与目录初始化 | 目录齐全，Git 可提交 |
| **1** | Skill 与配置文件 | 三个 Skill 可被 Cursor/Hermes 加载 |
| **2** | 交易日志与复盘基础 | 能手动 log 一笔 fill 并出周报 |
| **3** | 盈立手动执行流程 | 走完一次「研究→验价→清单→手挂→记录」 |
| **4** | 飞书 + Hermes | 飞书发指令能收到清单/复盘 |
| **5** | 记忆与自学习 | lessons 机制 + Cron 周报运行 |
| **6** | 验收与日常 SOP | 按附录日常 checklist 可独立运转 |

---

## 阶段 0：环境与目录初始化

### 步骤 0.1 创建项目根目录

**怎么做：**

1. 确认根路径存在：`d:\个人项目\股票分析\stock-system\`
2. 在 PowerShell 中执行：

```powershell
cd "d:\个人项目\股票分析"
mkdir stock-system\skills, stock-system\config, stock-system\data, stock-system\data\snapshots, stock-system\journal, stock-system\journal\research, stock-system\journal\approvals, stock-system\journal\fills, stock-system\journal\reviews, stock-system\journal\lessons, stock-system\scripts, stock-system\hermes, stock-system\templates -Force
```

**验收：** 上述文件夹均存在。

---

### 步骤 0.2 复制已有 Skill

**怎么做：**

1. 复制 13-Master Skill：

```powershell
Copy-Item -Recurse "d:\个人项目\股票分析\13master-stock-research\13master-stock-research" "d:\个人项目\股票分析\stock-system\skills\13master-stock-research"
```

2. 复制 IBKR Skill 作策略参考（只读，不用于下单）：

```powershell
Copy-Item -Recurse "d:\个人项目\股票分析\heng3.0\ibkr_trading_skill_v2" "d:\个人项目\股票分析\stock-system\skills\ibkr-strategies-reference"
```

3. 在 `skills\ibkr-strategies-reference\` 根目录新建 `README_LOCAL.md`，写一行说明：

```markdown
本目录仅作策略数学参考（strategies.md / grid_strategy.md）。
执行一律走 usmart-trading-playbook，禁止调用 place_bracket.py 等 IBKR 脚本。
```

**验收：** `skills\13master-stock-research\SKILL.md` 存在且可读。

---

### 步骤 0.3 初始化 Git 私有仓库

**怎么做：**

1. 在 `stock-system\` 下创建 `.gitignore`：

```gitignore
data/trade_journal.db
data/*.db-journal
config/feishu.yaml
config/secrets.*
hermes/config.yaml
__pycache__/
*.pyc
.env
```

2. 初始化并首次提交：

```powershell
cd "d:\个人项目\股票分析\stock-system"
git init
git add .
git commit -m "init stock-system delivery scaffold"
```

3. 推送到你的私有远程（GitHub/Gitee 等），按平台页面创建空仓库后：

```powershell
git remote add origin <你的私有仓库URL>
git branch -M main
git push -u origin main
```

**验收：** 远程可见目录结构；密钥文件未被提交。

---

### 步骤 0.4 安装 Python 依赖

**怎么做：**

1. 确认 Python 可用（Windows 应用商店版或官方安装版均可）：

```powershell
python --version
```

2. 创建虚拟环境并安装依赖：

```powershell
cd "d:\个人项目\股票分析\stock-system"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install pyyaml requests
```

3. 创建 `requirements.txt`：

```
pyyaml>=6.0
requests>=2.28
```

**验收：** `pip list` 可见 pyyaml、requests。

---

## 阶段 1：Skill 与配置文件

### 步骤 1.1 创建盈立执行 Playbook Skill

**怎么做：**

1. 确认文件已存在：`skills\usmart-trading-playbook\SKILL.md`（本交付包已生成骨架）
2. 在 Cursor 中打开该文件，确认 frontmatter 的 `description` 含触发词：`建仓`、`网格`、`挂单清单`、`盈立`
3. 将 Skill 安装到 Cursor：
   - **项目级**：已在 `stock-system/skills/` 下，Cursor 打开 `stock-system` 项目即可
   - **个人级（可选）**：复制到 `C:\Users\<用户名>\.cursor\skills\usmart-trading-playbook\`

**验收：** 在 Cursor 对话中说「网格 IREN $10000」，AI 应输出盈立挂单清单格式，而非 Python `place_bracket` 命令。

---

### 步骤 1.2 创建交易日志与复盘 Skill

**怎么做：**

1. 确认文件存在：`skills\trading-journal\SKILL.md`
2. 确认触发词：`fill`、`复盘`、`记录`、`纠错`
3. 同上安装到 Cursor skills 路径

**验收：** 说「IREN fill 180股 @55.60」，AI 应给出 `log_fill` 命令或等价 JSON 结构，并提示更新持仓。

---

### 步骤 1.3 编写 holdings.yaml

**怎么做：**

1. 复制模板：

```powershell
Copy-Item "d:\个人项目\股票分析\stock-system\config\holdings.yaml.example" "d:\个人项目\股票分析\stock-system\config\holdings.yaml"
```

2. 用编辑器打开 `config\holdings.yaml`，按真实持仓填写：
   - `core_positions`：核心持仓 ticker、数量、成本、策略名
   - `watchlist`：观察池 ticker、进场触发价、主题
   - `preferences`：确认 `default_broker: usmart`、`price_source_c: manual_screenshot`

3. 保存后提交（holdings.yaml 不含密钥，可入库）：

```powershell
git add config/holdings.yaml
git commit -m "add personal holdings config"
```

**验收：** AI 问「持仓」时能读出 yaml 内容。

---

### 步骤 1.4 编写 categories.yaml

**怎么做：**

1. 复制模板：

```powershell
Copy-Item "d:\个人项目\股票分析\stock-system\config\categories.yaml.example" "d:\个人项目\股票分析\stock-system\config\categories.yaml"
```

2. 对照 `skills\ibkr-strategies-reference\references\strategies.md` 中的策略表，确认默认映射合理（如 `high_growth_small_cap → B7`）
3. 可按个人偏好修改，保存并 commit

**验收：** 说「建仓 XXX」，AI 能根据 categories 推断默认策略。

---

### 步骤 1.5 在 Cursor 中加载 Skill

**怎么做：**

1. 用 Cursor 打开文件夹 `d:\个人项目\股票分析\stock-system`
2. 新建对话，首条消息发送：

```
请加载 stock-system/skills 下的三个 Skill：
13master-stock-research、usmart-trading-playbook、trading-journal。
后续股票研究走 13-Master 四步；执行走盈立 Playbook；成交记录走 trading-journal。
```

3. 可选：在 Cursor Rules（`.cursor/rules/stock-system.mdc`）写入同样说明，使每会话自动生效

**验收：** 任意新对话中研究/执行/记录三类指令行为一致。

---

## 阶段 2：交易日志与复盘基础

### 步骤 2.1 初始化 SQLite 数据库

**怎么做：**

1. 激活虚拟环境：

```powershell
cd "d:\个人项目\股票分析\stock-system"
.\.venv\Scripts\Activate.ps1
```

2. 执行初始化脚本：

```powershell
python scripts\init_db.py
```

3. 确认生成 `data\trade_journal.db`

**验收：**

```powershell
python -c "import sqlite3; c=sqlite3.connect('data/trade_journal.db'); print(c.execute('SELECT name FROM sqlite_master WHERE type=\"table\"').fetchall())"
```

应输出：`research_logs`, `decisions`, `fills`, `position_snapshots`, `reviews`, `lessons` 等表名。

---

### 步骤 2.2 试跑 trade_logger

**怎么做：**

1. 记录一笔模拟研究：

```powershell
python scripts\trade_logger.py research --ticker IREN --tier wait --scores "{\"V\":2,\"M\":6,\"H\":7,\"R\":3,\"I\":8,\"G\":4}" --note "AI_infra theme"
```

2. 记录一笔模拟决策：

```powershell
python scripts\trade_logger.py decision --ticker IREN --action grid --strategy G_grid --budget 10000 --status pending
```

3. 记录一笔模拟成交：

```powershell
python scripts\trade_logger.py fill --ticker IREN --side BUY --qty 180 --price 55.60 --note "manual test"
```

4. 查询最近记录：

```powershell
python scripts\trade_logger.py list --limit 5
```

**验收：** 三条命令均无报错；`list` 可见记录。

---

### 步骤 2.3 建立 Markdown 双写习惯

**怎么做：**

1. 每次 `log_fill` 后，脚本会自动在 `journal/fills/` 生成同名 `.md`（若脚本已实现）；若未自动生成，手动复制模板：

```powershell
Copy-Item "templates\fill_record.md" "journal\fills\IREN_20250613_test.md"
```

2. 填写：ticker、方向、数量、成交价、三源验价表、关联 decision_id

**验收：** `journal/fills/` 下至少有一份完整 fill 记录。

---

### 步骤 2.4 试跑周复盘脚本

**怎么做：**

```powershell
python scripts\review_weekly.py --output journal\reviews\latest_weekly.md
```

打开生成的 Markdown，确认包含：
- 本周成交笔数
- 盈亏汇总（若有 sell 记录）
- 错误标签统计
- 待写入 lessons 的建议

**验收：** `journal/reviews/latest_weekly.md` 内容非空、格式可读。

---

## 阶段 3：盈立手动执行流程固化

### 步骤 3.1 走完一次完整模拟（不下真单）

**怎么做：**

1. 在 Cursor 发送：

```
深度研究 IREN，AI 基础设施主题。不要跳过验真步骤。
```

2. 等待 AI 完成研究后，发送：

```
网格 IREN $10000
```

3. AI 会先查 Web 源 A、B，然后要求盈立第三源。此时：
   - 打开盈立 PC 客户端或 App
   - 找到 IREN 报价页
   - 截图或打字：`盈立 IREN $XX.XX，USD，盘中/收盘`

4. AI 输出【盈立挂单清单】后，**不要真下单**，回复：

```
模拟确认，不实际下单。请生成 fill 记录模板。
```

5. 用 trade_logger 写入模拟 decision + fill

**验收：** 全流程有 research → decision → approval md → fill 记录链。

---

### 步骤 3.2 走完一次真实小额单（可选但强烈建议）

**怎么做：**

1. 选一只你已研究透彻、仓位允许的小额标的
2. 重复步骤 3.1，但在清单确认后：
   - 打开盈立客户端 → 交易 → 限价单 GTC
   - 严格按清单价格与数量挂单
3. 成交后 30 分钟内，在 Cursor 或（后续）飞书发送：

```
<TICKER> fill <数量>股 @<成交价>
```

4. 执行：

```powershell
python scripts\trade_logger.py fill --ticker <TICKER> --side BUY --qty <N> --price <P>
```

5. 若策略需要挂卖单，再让 AI 出 SELL 清单，在盈立手挂

**验收：** 真实 fill 已入库；journal/fills/ 有对应 md。

---

### 步骤 3.3 设置盈立到价提醒

**怎么做：**

1. 对 G_grid 标的，按 AI 给的指标卡，在盈立 App 设 4 个提醒（能设几个设几个）：
   - ≥ P_BUY：查是否成交
   - ≤ 下一层 BUY：准备加仓
   - ≤ 软警报：暂停
   - ≤ 硬止损：先平仓再复盘
2. 提醒触发后，按 Playbook 在飞书/Cursor 发对应指令

**验收：** 至少一个观察池标的已设提醒。

---

## 阶段 4：飞书 + Hermes 对话入口

### 步骤 4.1 安装 WSL2（Windows 上跑 Hermes 推荐）

**怎么做：**

1. 管理员 PowerShell：

```powershell
wsl --install
```

2. 重启后进入 Ubuntu，更新系统：

```bash
sudo apt update && sudo apt upgrade -y
```

**验收：** `wsl --list` 显示 Ubuntu 已安装。

---

### 步骤 4.2 在 WSL2 安装 Hermes Agent

**怎么做：**

1. 在 WSL Ubuntu 中执行官方安装（以官网为准）：

```bash
curl -fsSL https://hermes-agent.org/install.sh | bash
```

2. 运行配置向导：

```bash
hermes setup
```

3. 选择 LLM Provider（OpenRouter / DeepSeek / Anthropic 等），填入 API Key

**验收：** `hermes --version` 或等价命令可运行。

---

### 步骤 4.3 配置 Hermes 读取本仓库 Skill

**怎么做：**

1. 在 WSL 中让 Hermes 能访问 Windows 目录，例如：

```bash
ln -s /mnt/d/个人项目/股票分析/stock-system ~/stock-system
```

2. 在 Hermes 配置中设置 skills 路径指向 `~/stock-system/skills`（具体键名见 Hermes 文档 `hermes setup` 或 `config.yaml`）
3. 确认三个 Skill 被加载

**验收：** Hermes CLI 中 `/skills` 或等价命令列出三个 Skill。

---

### 步骤 4.4 创建飞书自建应用

**怎么做：**

1. 打开 [飞书开放平台](https://open.feishu.cn/) → 创建企业自建应用
2. 记录 **App ID**、**App Secret**
3. 权限管理 → 开通：
   - 接收消息
   - 发送消息
   - （可选）多维表格读写
4. 事件订阅 → 选择「长连接」或「Webhook」（按 Hermes 文档推荐方式）
5. 运行 Hermes 网关配置：

```bash
hermes gateway setup
```

6. 选择 **Feishu/Lark**，填入 App ID、App Secret
7. 启动网关：

```bash
hermes gateway start
```

8. 安装为后台服务（可选）：

```bash
hermes gateway install
```

**验收：** 飞书群 @机器人 发「帮助」，有回复。

---

### 步骤 4.5 公网可达（Webhook 场景）

**怎么做：**

若 Hermes 使用 Webhook 而非长连接：

1. **方案 A**：轻量 VPS 部署 Hermes（推荐长期）
2. **方案 B**：本机 frp/ngrok 映射端口（临时调试）

调试阶段可用 ngrok：

```bash
ngrok http <hermes_gateway_port>
```

将 URL 填入飞书事件订阅。

**验收：** 飞书消息能触发 Hermes 且日志无 403/timeout。

---

### 步骤 4.6 飞书群指令联调

**怎么做：**

在飞书群依次发送并验证：

| 指令 | 期望结果 |
|------|----------|
| `研究 NVDA` | 返回研究摘要或提示在 Cursor 做深度批量 |
| `网格 IREN $10000` | 查 Web 两源 + **要求盈立截图** |
| （发盈立截图） | 返回挂单清单卡片 |
| `确认` | 标记 approved，提醒去盈立手挂 |
| `IREN fill 180 @55.60` | 确认已记录 / 给 SELL 清单 |
| `复盘 本周` | 返回周报摘要 |
| `持仓` | 读 holdings.yaml 摘要 |

**验收：** 上表全部通过。

---

### 步骤 4.7 配置 Hermes 定时复盘（可选）

**怎么做：**

1. 在 Hermes 配置 Cron（语法见 Hermes 文档），示例任务：

```
每周日 20:00：运行 python ~/stock-system/scripts/review_weekly.py 并将结果发到飞书 home 频道
```

2. 或在 Windows 任务计划程序调用 WSL 命令作为备选

**验收：** 手动触发 Cron 一次，飞书收到周报。

---

## 阶段 5：持续记忆与自学习闭环

### 步骤 5.1 建立 lessons 写入规则

**怎么做：**

1. 每次犯错的同一轮对话内，要求 AI：
   - 写 `journal/lessons/LESSON_<序号>_<简述>.md`
   - 更新 SQLite `lessons` 表：

```powershell
python scripts\trade_logger.py lesson --title "验价必须盈立第三源" --tags "验价缺失" --body "Web双源一致仍滞后，必须以盈立为准"
```

2. 在 `journal/lessons/README.md` 维护 lessons 索引表

**验收：** 至少 1 条真实 lesson 入库。

---

### 步骤 5.2 人工合并 lesson 进 Skill

**怎么做：**

1. 每周复盘后，打开 `journal/lessons/`
2. 挑选 **已验证** 的教训（重复出现 ≥2 次或造成实质损失）
3. 编辑对应 Skill 文件，例如：
   - 验价类 → `usmart-trading-playbook/SKILL.md` 的 Phase A
   - 研究校准类 → `13master-stock-research/references/13-master-framework.md`
4. Git commit 并 push
5. Hermes 侧重载 Skill：`/reload` 或重启 gateway

**验收：** 新 lesson 出现在 Skill 正文中；下次同类请求 AI 主动提及。

---

### 步骤 5.3 飞书多维表格（可选）

**怎么做：**

1. 飞书 → 新建多维表格「股票交易日志」
2. 建 5 张表：观察池、交易流水、持仓、复盘库、规则库（字段见方案文档）
3. 复制 `config/feishu.yaml.example` 为 `feishu.yaml`，填入 `app_token`、`table_id`
4. 试跑同步：

```powershell
python scripts\sync_bitable.py --dry-run
python scripts\sync_bitable.py
```

**验收：** 飞书表中出现与 SQLite 一致的 fill 记录。

---

### 步骤 5.4 Hermes Self-Evolution（可选，后期）

**怎么做：**

1. 至少积累 **20 笔** 有完整 trace 的实盘记录后再考虑
2. 仅优化：复盘话术、检查清单表述、飞书回复格式
3. **禁止** Evolution 自动修改：止损比例、仓位上限、策略 multiplier
4. 所有 Evolution 产出必须经 Git PR + 人工 merge

**验收：** 无自动合并未审核的 Skill 变更。

---

## 阶段 6：验收与日常 SOP

### 步骤 6.1 端到端验收清单

**逐项打勾：**

- [ ] 目录与 Git 就绪
- [ ] 三个 Skill 在 Cursor 可用
- [ ] holdings.yaml / categories.yaml 已填
- [ ] SQLite 初始化，trade_logger 可用
- [ ] 完成至少 1 次完整模拟流程（研究→验价→清单→记录）
- [ ] （可选）完成 1 笔真实小额单并记录
- [ ] Hermes + 飞书可对话
- [ ] 飞书验价流程：AI 会主动要盈立截图
- [ ] 周复盘脚本可运行
- [ ] lessons 机制已试跑

---

### 步骤 6.2 日常 SOP（每个交易日）

**研究/new idea：**

```
Cursor 或 飞书：「深度研究 <TICKER>」
→ 决策面板三档
→ 立即可建/等回调 写入观察池（更新 holdings.yaml 或 log research）
```

**下单前：**

```
「建仓/网格 <TICKER> ...」
→ AI 查 Web A + B
→ 你发盈立截图或「盈立 <TICKER> $XX.XX」
→ 收到挂单清单
→ 飞书回复「确认」
→ 盈立客户端手挂 GTC
```

**成交后：**

```
30 分钟内：「<TICKER> fill <N>股 @<价格>」
→ log_fill
→ 若要挂卖单：「出 TP 方案」→ 盈立手挂
```

**每周：**

```
「复盘 本周」或等 Cron 推送
→ 审阅 lessons
→ 人工 merge 进 Skill（如有）
```

---

## 附录 A：飞书指令表

| 指令 | 作用 |
|------|------|
| `研究 <TICKER>` | 13-Master 研究摘要 |
| `深度研究 <TICKER>` | 完整四步（Cursor 更适合） |
| `对比 A vs B` | 双标的对比 |
| `网格 <TICKER> $<预算>` | G_grid 挂单清单 |
| `建仓 <TICKER> <N>股` | A+ Bracket 挂单清单 |
| `出 TP 方案` | 基于 fill 的卖单清单 |
| `确认` / `/approve` | 认可方案（不等于已下单） |
| `<TICKER> fill <N> @<价>` | 记录成交 |
| `持仓` | 当前持仓摘要 |
| `观察池` | watchlist |
| `复盘 本周` | 周报 |
| `纠错 <内容>` | 写 lesson |

---

## 附录 B：盈立执行手册摘要

### 策略选择

| 标的类型 | 策略 | 盈立操作 |
|----------|------|----------|
| 大盘成长 | B 1.5/2/3× | 3 笔 GTC 限价卖 |
| 高波小盘/事件 | B7 1.35/1.70/2.05 | 50/30/20 分批卖 |
| 新 IPO | B2 1.2/1.4/1.8 | 早兑现 |
| 高波长期看多 | G_grid | 循环 BUY→SELL |
| ETF/信仰 | E_buy_hold | 仅止损提醒 |
| 杠杆 ETF | 禁止死拿 | B7 或 A_+100 |

### 挂单清单必含字段

- 三源验价表（含盈立第三源）
- 每笔：方向、数量、限价、GTC、说明
- 软/硬止损提醒价
- 成交后下一步（挂哪些 SELL）

### 禁止事项

- 无盈立第三源 → 不出具带美元价格的清单
- 清单外价格 → 不挂
- 跳过 fill 记录 → 不允许

---

## 附录 C：三源验价操作细则

### 源 A、B（AI 自动）

- 不同网站：如 Yahoo + Investing
- 记录：价格、时间、货币

### 源 C（你手动，无 API 阶段）

1. 打开盈立 PC 客户端或 App
2. 进入标的行情页
3. **截图** 或 **打字**：`盈立 IREN $58.06 USD 收盘`
4. 发给 Cursor / 飞书

### 判定

| 情况 | 处理 |
|------|------|
| A、B、C 差异 ≤0.5% | 通过，以盈立 C 为锚 |
| A、B 一致，C 差 >2% | 停，以盈立为准重算 |
| A、B 差 >2% | 停，查清市场/货币 |
| 无 C | 不出清单 |

### 合格截图要素

- 股票代码
- 现价
- USD/HKD
- 盘前/盘中/盘后/收盘状态

---

## 附录 D：Hermes 定位与边界

### Hermes 负责

- 飞书 7×24 入口
- 加载 Skill、持久记忆
- Cron 周报
- `/approve` 审批流
- 从任务 trace 沉淀 Skill（人工审核后）

### Hermes 不负责

- 直连盈立（无 API 阶段）
- 跳过验价出清单
- 自动修改止损/仓位数字

### 与 Cursor 分工

| 场景 | 工具 |
|------|------|
| 手机快捷指令、fill 回报 | Hermes + 飞书 |
| 14 只批量研究、改 Skill | Cursor |
| Self-Evolution PR 审查 | Cursor + Git |

---

## 文件清单（交付物）

本交付包应包含：

```
stock-system/
├── DELIVERY_PLAN.md              ← 本文件
├── requirements.txt
├── config/
│   ├── holdings.yaml.example
│   └── categories.yaml.example
├── skills/
│   ├── 13master-stock-research/  ← 步骤 0.2 复制
│   ├── ibkr-strategies-reference/← 步骤 0.2 复制
│   ├── usmart-trading-playbook/
│   │   └── SKILL.md
│   └── trading-journal/
│       └── SKILL.md
├── scripts/
│   ├── init_db.py
│   ├── trade_logger.py
│   ├── review_weekly.py
│   └── sync_bitable.py           ← 可选，阶段 5.3
├── templates/
│   ├── fill_record.md
│   ├── approval_record.md
│   └── weekly_review.md
└── journal/
    └── lessons/
        └── README.md
```

---

*文档版本：无 API 盈立手动版 · 与 Cursor + Hermes + 飞书方案一致*
