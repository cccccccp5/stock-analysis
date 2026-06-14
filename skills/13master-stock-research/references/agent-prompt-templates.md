# Agent Prompt Templates — Single-Block Bash Format

The DeepSeek-based scoring agent (`agent_v4.py`) is invoked via single-block bash commands. The user requires single copy-paste blocks — never split across multiple code blocks.

## Setup conventions

Adjust these paths to match the user's environment. Common defaults:

```bash
AGENT_TOOLS_DIR="${HOME}/Developer/agent_tools"     # location of agent_v4.py
AGENT_REPORTS_DIR="${HOME}/Developer/agent_reports" # output reports
PROMPT_TMP="/tmp"                                    # prompt staging
```

API keys are typically in `~/.zshrc` as exports. Inject them into non-interactive shells via:

```bash
eval "$(grep '^export DEEPSEEK_API_KEY' ~/.zshrc)" && \
eval "$(grep '^export POLYGON_API_KEY' ~/.zshrc)" && \
cd "${AGENT_TOOLS_DIR}"
```

## Template A: Single ticker deep dive

```bash
cat > /tmp/{TICKER_LOWER}_prompt.txt << 'PROMPT_EOF'
{COMPANY_NAME} ({EXCHANGE}:{TICKER}) 深度研究【{ONE_LINE_THESIS}】。

#### 必读事件上下文 ####
{THEME_EVENT_PARAGRAPH — paste the sector valuation anchor + recent catalyst, e.g. "5/20 SpaceX S-1 披露 Anthropic 付 $1.25B/月..."}

#### 公司基本面 ####
{Q1/Q2 财报、营收、毛利率、关键合同、产能、客户集中度等 — facts only}

#### 研究要求 A-I ####
A 业务结构
B 最新季财务 (营收/毛利/EPS/backlog)
C 客户与合同结构 (集中度、tenor、定价反推 vs 估值锚)
D 估值 (P/S、P/E、EV/Sales、横向 vs 同业)
E Catalyst (未来 3-6 个月)
F 风险 (财务、执行、政策、客户)
G 分析师覆盖与目标价
H 13-Master 六派系评分 (V/M/H/R/I/G,0-10) + 横向对比 {EXISTING_HOLDINGS_TICKER_LIST}
I 信号 (建仓/观察/跳过)

要求 facts only,每条数据必标 5/{TODAY} 源+时效,不确定明说"不确定"不编造。
PROMPT_EOF

eval "$(grep '^export DEEPSEEK_API_KEY' ~/.zshrc)" && \
eval "$(grep '^export POLYGON_API_KEY' ~/.zshrc)" && \
cd "${AGENT_TOOLS_DIR}" && \
python3 agent_v4.py {TICKER} "$(cat /tmp/{TICKER_LOWER}_prompt.txt)" 2>&1 | tee logs/{TICKER_LOWER}_$(date +%Y%m%d_%H%M%S).log
```

## Template B: Batch run (N tickers)

For N tickers, use this pattern. Each prompt file is created independently, then a single `&& \` chain runs them serially. This pattern is friendly to background execution.

```bash
# ============================================================
# {THEME_NAME} {N} 家深度研究
# 主题事件: {EVENT_DESCRIPTION}
# 严格执行 4 步工作流的步骤 ①②③④
# 预算估算 ~¥(N*0.02), 时间 ~(N*1) 分钟
# ============================================================

# ===== 共同主题上下文 (所有 prompt 引用) =====
cat > /tmp/{theme_short}_event_context.txt << 'EVENT_EOF'
【主题事件上下文 · {DATE} 整理】
{KEY_FACTS_BLOCK — paste verified facts about the inflection event,
including unit economics, partnerships, and dates}

【估值锚】
{ANCHOR_VALUE — e.g. "$50M/MW/年 = GPU-cloud 模式"}

【核心模式判断】
{1-3 sentences on how this event reshapes the sector}
EVENT_EOF


# ===== 类别 1: {CATEGORY_NAME} ({N1} 家) =====
cat > /tmp/{ticker1}_prompt.txt << 'P_EOF'
{TICKER1} ({EXCHANGE}:{TICKER1}) 深度研究【{ROLE}】。
公司角色: {ROLE_DESCRIPTION}.
近期事件自拉 (Q1 财报/合同/收购/管理层动作).
重点判断:
1. {SPECIFIC_THESIS_QUESTION_1}
2. {SPECIFIC_THESIS_QUESTION_2}
3. 与现有持仓 {EXISTING_HOLDINGS} 横向对比.
研究要求 A-I 标准 13-Master.
执行价格验真规则: 价格双源对照+5 日内+30 天事件 web_search.
不假设不编造,不确定明说"不确定".
P_EOF

# {repeat for ticker2, ticker3, ...}


# ===== 串行运行 (注入 API key) =====
eval "$(grep '^export DEEPSEEK_API_KEY' ~/.zshrc)" && \
eval "$(grep '^export POLYGON_API_KEY' ~/.zshrc)" && \
cd "${AGENT_TOOLS_DIR}" && \
echo "===== 阶段 1: {CATEGORY_1} ({N1} 家) =====" && \
  echo "[1/{N}] {TICKER1}" && python3 agent_v4.py {TICKER1} "$(cat /tmp/{ticker1}_prompt.txt)" 2>&1 | tee logs/{ticker1}_$(date +%Y%m%d_%H%M%S).log && \
  echo "[2/{N}] {TICKER2}" && python3 agent_v4.py {TICKER2} "$(cat /tmp/{ticker2}_prompt.txt)" 2>&1 | tee logs/{ticker2}_$(date +%Y%m%d_%H%M%S).log && \
  ... && \
echo "===== {N} 家全部完成 ====="
```

## Background execution pattern (for batches >10 tickers)

When a batch exceeds the bash tool timeout (~10 min), run as background job:

```bash
nohup bash /tmp/run_batch.sh > /tmp/run_{theme}_master.log 2>&1 &
echo "PID: $!"
```

Then monitor via:
```bash
tail -f /tmp/run_{theme}_master.log
```

## Prompt skeleton best practices

Each per-ticker prompt should follow this structure:

```
{Company} ({Exchange}:{TICKER}) 深度研究【{role one-liner}】。

#### 必读事件上下文 ####
{Inject the shared theme event paragraph here verbatim}

#### 公司基本面 ####
{1-2 sentences capturing the public role + sector position}
{Recent quarter financial highlights from your web_search}

#### 研究要求 A-I ####
A 业务结构
B 最新季财务
C 客户/合同结构
D 估值
E Catalyst
F 风险
G 分析师覆盖
H 13-Master 评分 + 横向对比 (existing holdings list)
I 信号

#### 个性化重点 ####
1. {Hypothesis the agent should explicitly test}
2. {Risk the agent should explicitly check}
3. {Comparison the agent should explicitly make}

要求 facts only, 每条数据标 5/{DATE} 源+时效, 不确定明说不编造.
应用价格验真规则 + 30 天关键事件 web_search.
```

## Cost and timing estimates

| Batch size | DeepSeek API cost | Wall clock |
|-----------|-------------------|------------|
| 1 ticker | ~¥0.02 | 1-2 min |
| 5 tickers | ~¥0.10 | 5-7 min |
| 14 tickers | ~¥0.28 | 14-18 min |
| 28 tickers | ~¥0.56 | 28-35 min |

Batches >10 should run as background jobs.

## Output convention

Agent writes Markdown reports to `${AGENT_REPORTS_DIR}/{TICKER}_{YYYYMMDD}_{HHMMSS}_v4.md`.
Logs go to `${AGENT_TOOLS_DIR}/logs/{ticker}_{YYYYMMDD}_{HHMMSS}.log`.

After the batch completes, the user can paste a results summary in this format for step ③:

```
[ticker] V=X.X M=X.X H=X.X R=X.X I=X.X G=X.X | avg=X.XX
Consensus: XXX
Key thesis: (one sentence)
Key risk: (one sentence)
Report path: {AGENT_REPORTS_DIR}/{ticker}_*.md
```
