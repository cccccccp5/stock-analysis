# DeepSeek Agent Setup

The scoring agent is a Python script that uses the DeepSeek API for 13-Master scoring and a price-data API for market context. This file documents the expected environment.

## Required environment variables

These should be in `~/.zshrc` (or equivalent shell rc file):

```bash
export DEEPSEEK_API_KEY="..."        # DeepSeek API for scoring agent
export POLYGON_API_KEY="..."         # Polygon.io or equivalent for price data
# Optional:
export NEWS_API_KEY="..."            # If agent supports news fetching
```

## Non-interactive shell key injection

The bash tool used by Claude (and similar runners) starts a non-interactive shell that does NOT source `~/.zshrc`. Inject keys via:

```bash
eval "$(grep '^export DEEPSEEK_API_KEY' ~/.zshrc)" && \
eval "$(grep '^export POLYGON_API_KEY' ~/.zshrc)" && \
cd "${AGENT_TOOLS_DIR}"
```

Always prepend this to any agent batch command. If the user's keys are elsewhere (e.g. `.bashrc` or a `.env` file), substitute the appropriate file:

```bash
# .env file pattern
set -a; source ~/.env; set +a
# .bashrc pattern
eval "$(grep '^export DEEPSEEK_API_KEY' ~/.bashrc)"
```

## Directory conventions

```
${HOME}/Developer/
├── agent_tools/
│   ├── agent_v4.py          # main scoring agent
│   ├── feedback_estimation_calibration.md  # calibration notes
│   └── logs/                # per-run logs
│       └── {ticker}_{timestamp}.log
└── agent_reports/
    └── {TICKER}_{YYYYMMDD}_{HHMMSS}_v4.md
```

Adapt paths to the user's actual setup if different.

## Invocation pattern

```bash
python3 agent_v4.py {TICKER} "$(cat /tmp/{ticker}_prompt.txt)" 2>&1 | tee logs/{ticker}_$(date +%Y%m%d_%H%M%S).log
```

The agent expects two CLI args:
1. Ticker symbol (uppercase)
2. The full prompt body (typically loaded from a file via `cat`)

Output Markdown is written to `${AGENT_REPORTS_DIR}/{TICKER}_{timestamp}_v4.md`.

## Cost expectations

| Quantity | DeepSeek API cost | Wall clock |
|----------|-------------------|------------|
| 1 prompt run | ~¥0.02 | 1-2 min |
| 14 prompts | ~¥0.28 | ~14 min |
| 28 prompts | ~¥0.56 | ~28 min |

Costs are approximate (DeepSeek pricing varies). Budget assumes typical prompt sizes of 500-1500 tokens.

## Background execution

For batches that exceed bash tool timeout (~10 min), invoke as background job:

```bash
# Save the master command to a script
cat > /tmp/run_batch.sh << 'EOF'
#!/usr/bin/env bash
{ paste the full eval + agent loop here }
EOF
chmod +x /tmp/run_batch.sh

# Run in background
nohup bash /tmp/run_batch.sh > /tmp/run_{theme}_master.log 2>&1 &
echo "Background PID: $!"

# Monitor
tail -f /tmp/run_{theme}_master.log
```

## Workflow constraint: cloud vs local

If the user maintains a cloud-hosted version of the agent (e.g. on a VPS), establish ONE source of truth:

- Source of truth: typically the cloud version (continuously updated)
- Local: may be outdated; never assume it's current
- Cross-environment workflow: discuss in web Claude → Claude Code generates instructions → apply to cloud via SSH → SSH read-back verification

Ask the user where their authoritative agent lives before issuing any modify-the-agent commands.

## Calibration file

The agent maintains a calibration file (e.g. `${HOME}/.claude/projects/.../memory/feedback_estimation_calibration.md`) that records observed biases. Reference it when interpreting scores and apply the rules in `13-master-framework.md`.

## Post-run protocol

After a batch completes:

1. List the report files: `ls -lt "${AGENT_REPORTS_DIR}" | head -30`
2. Extract scores: `grep -E "(V|M|H|R|I|G)=" "${AGENT_REPORTS_DIR}"/*_v4.md | tail -100`
3. **Re-pull all prices via web_search before producing decision panel** (agent timestamps are stale)
4. Apply calibration rules from `13-master-framework.md`
5. Generate decision panel per `decision-panel-design.md`

## Failure modes

| Symptom | Cause | Fix |
|---------|-------|-----|
| `KeyError: DEEPSEEK_API_KEY` | Non-interactive shell didn't source rc | Use `eval "$(grep ...)"` injection |
| 404 errors on price fetch | Stock listed on non-US exchange (TPE, TSE) | Note in report, do not use those prices for decisions |
| Empty score output | Agent rate-limited or API quota hit | Wait + retry; check API dashboard |
| Truncated reports | Prompt too long | Reduce per-ticker prompt to <2000 tokens |
| Same score for different tickers | Agent collapse pattern | Apply manual correction rule (see 13-master-framework.md) |

## Cloud-hosted variants

If the user has a cloud agent (e.g. via SSH to a VPS), use a unified format for instructions:

```bash
ssh user@host '
  cd /path/to/agent_tools && \
  eval "$(grep ^export DEEPSEEK_API_KEY ~/.zshrc)" && \
  python3 agent_v4.py {TICKER} "$(cat <<PROMPT
  {full prompt}
PROMPT
  )" 2>&1 | tee logs/{ticker}.log
'
```

Always read back the result via SSH after writing to verify the file landed correctly.
