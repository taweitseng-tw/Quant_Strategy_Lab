# SOUL.md — Quant Strategy Lab Project Soul

> This file is the project constitution.  
> Every coding agent must read this before modifying the repository.  
> If any task conflicts with this file, this file wins.

---

## 0. Project Identity

Project name:

```text
Quant Strategy Lab
```

Project type:

```text
Local-first desktop quant strategy generation, backtesting, validation, filtering, and reporting platform.
```

Primary user:

```text
A single advanced user / developer who wants a visual, disciplined, reproducible research tool for futures, index, ETF, and OHLCV-based strategy research.
```

Primary language for user-facing explanation:

```text
Traditional Chinese.
```

Primary engineering language:

```text
Python.
```

Primary GUI framework:

```text
PySide6.
```

---

## 1. The One-Sentence Mission

Build a local desktop research lab that can:

```text
Import market data
→ normalize and resample it
→ generate candidate strategies
→ backtest them realistically
→ attack them with OOS / stress tests / Monte Carlo / Walk-forward
→ kill weak curve-fit strategies
→ preserve only explainable, reproducible candidates
→ visualize and export the evidence.
```

---

## 2. The Soul of This Project

This project is not a "beautiful backtest generator".

This project is a:

```text
strategy foundry
+ backtest engine
+ anti-overfitting firewall
+ visual research cockpit
+ reproducible experiment archive
```

The core spirit is:

```text
Truth over curves.
Robustness over profit screenshots.
Reproducibility over speed.
Small verified steps over giant clever rewrites.
Readable systems over magical black boxes.
```

---

## 3. Non-Negotiable Principles

### 3.1 No Fake Alpha

Never design features that make strategies look better than they are.

Forbidden:

1. Hiding transaction costs.
2. Ignoring slippage.
3. Using future data.
4. Mixing IS and OOS accidentally.
5. Optimizing on OOS.
6. Reporting only the best run.
7. Dropping failed strategies silently.
8. Treating backtest profit as evidence of live-trading edge.
9. Generating strategies without storing the generation config and seed.
10. Presenting curve-fitted results as robust candidates.

If a result is uncertain, label it as uncertain.

---

### 3.2 Backtest Honesty Comes First

Backtest engine correctness is more important than speed.

Default assumptions should be conservative.

Examples:

```text
If stop-loss and take-profit are both touched inside the same bar, default to stop-loss first.
If execution order is unknown, choose the more pessimistic result.
If cost is uncertain, allow stress testing with higher cost.
If fill quality is uncertain, expose the assumption clearly.
```

---

### 3.3 OOS Is Sacred

Out-of-Sample data is not training data.

Rules:

1. Never use OOS to generate strategy logic.
2. Never use OOS to optimize parameters.
3. Never overwrite OOS results silently.
4. Always show IS / Validation / OOS separately.
5. Always make IS/OOS degradation visible.

The UI must make OOS failure obvious.

---

### 3.4 Every Strategy Must Have Provenance

Every saved strategy must be reproducible.

Required metadata:

1. Strategy JSON.
2. Build task config.
3. Random seed.
4. Dataset ID.
5. Dataset time range.
6. Instrument profile.
7. Session template.
8. Backtest assumptions.
9. Cost settings.
10. Validation split.
11. Stress test config.
12. Fitness score version.
13. Timestamp.
14. Software version.

If a strategy cannot be reproduced, it should not be trusted.

---

### 3.5 Engine and UI Must Stay Separate

The GUI must not contain core trading logic.

Allowed:

```text
UI → service / controller → engine → repository
```

Forbidden:

```text
UI widget directly calculates strategy signals.
UI widget directly runs backtest internals.
UI widget directly mutates SQLite tables without repository layer.
Backtest engine imports PySide6.
Strategy engine imports UI widgets.
```

The engine must be testable without launching the GUI.

---

### 3.6 Small Verified Steps

All agents must prefer:

```text
small diff
+ clear intent
+ testable output
+ changelog update
```

over:

```text
large rewrite
+ vague improvement
+ no tests
+ no explanation
```

A task is not complete until it can be verified.

---

### 3.7 No Premature Complexity

Do not implement advanced features before the foundation is stable.

Do not jump to:

1. Full Genetic Programming.
2. Walk-forward Matrix.
3. Live trading.
4. Broker API.
5. Distributed computing.
6. GPU acceleration.
7. Multi-user SaaS.
8. Complex portfolio-level allocation.
9. Full Python / NinjaTrader / EasyLanguage export.

unless the PRD milestone explicitly says so.

---

### 3.8 The Prototype Must Become Real

Prototype v0.0.1 is considered successful when it can:

1. Launch PySide6 main window.
2. Create or open a project folder.
3. Import OHLCV data.
4. Display data table.
5. Display candlestick chart.
6. Resample 1-minute data to 5-minute data.
7. Configure instrument profile.
8. Manually create one simple strategy.
9. Run event-driven backtest.
10. Show trade list.
11. Show equity curve.
12. Generate 10 random strategies.
13. Rank strategies.
14. Export simple Markdown or HTML report.

Anything outside this list must not block Prototype v0.0.1.

---

## 4. Karpathy-Style Coding Agent Discipline

This project follows a Karpathy-inspired agent discipline:

```text
Do less.
Read first.
Understand the local code.
Change only what is necessary.
Prefer boring correct code.
Verify before claiming success.
Do not invent architecture when architecture already exists.
Do not hide uncertainty.
Stop at natural checkpoints.
```

### 4.1 Read Before Editing

Before editing, agents must inspect the context level required by `AGENTS.md`.

Baseline for every task:

1. `SOUL.md`
2. `AGENTS.md`
3. `docs/context_brief.md` if present
4. The current task card or latest task-board section
5. Relevant source files

Full-detail review is still mandatory for architecture changes, product-scope
changes, engine logic, validation logic, backtest assumptions, strategy
generation, repository schema changes, release or milestone acceptance, and any
task whose risk is unclear.

For low-risk documentation, UI copy, small wiring, or formatting-safe fixes,
agents may read compact context plus the relevant file sections instead of
loading every long project document in full. If compact context conflicts with
the full documents, the full documents win.

Large append-only files such as `docs/changelog.md` should be read from the
latest relevant entries first. Agents should expand to full-file review only
when the task depends on older history.

If a file does not exist yet, create it only when the current task requires it.

---

### 4.2 Do Not Rewrite Without Permission

Do not rewrite an entire module unless:

1. The task explicitly asks for a rewrite.
2. The existing design is broken and documented.
3. The rewrite plan is written first.
4. The user or Codex approves the rewrite.

Prefer surgical changes.

---

### 4.3 Leave the Codebase More Legible

Every change should improve at least one of:

1. Correctness.
2. Testability.
3. Readability.
4. Reproducibility.
5. Separation of concerns.
6. User-visible reliability.

Do not add clever abstractions unless they remove real complexity.

---

### 4.4 Tests Are Not Decoration

Core engine changes require tests.

At minimum:

1. Data import tests.
2. Resample tests.
3. Strategy rule tests.
4. Backtest execution tests.
5. Cost / slippage tests.
6. Stop-loss / take-profit tests.
7. OOS split tests.
8. Stress test tests.
9. Report export smoke tests.

If tests cannot be run, say so clearly and explain why.

---

## 5. Product Truths

### 5.1 The User Needs Visual Feedback

The user has explicitly stated:

```text
I need visualization to feel the software is real and useful.
```

Therefore, the UI must not be delayed until the very end.

However:

```text
GUI must appear early,
but GUI must not own the engine.
```

---

### 5.2 The First Data Priority

The first serious data target is:

```text
MultiCharts / TradeStation-like exported OHLCV data.
```

Do not begin with broker API.

Do not begin with live data.

Do not begin with tick-level market replay.

---

### 5.3 The First Strategy Priority

The first strategy engine must use:

```text
Fixed four-block strategy template:
- Long Entry
- Long Exit
- Short Entry
- Short Exit
```

MVP may support:

1. Random parameters.
2. Random condition combinations.
3. AND / OR conditions.
4. Long / short mirror mode.
5. Long / short asymmetric mode.

GA comes later.

GP comes much later.

---

### 5.4 The First Backtest Priority

The first backtest engine must be:

```text
event-driven, bar-by-bar, single-instrument, single-position.
```

It must support:

1. Market entry.
2. Stop loss.
3. Take profit.
4. Holding N bars.
5. Session-end exit.
6. Commission.
7. Slippage.
8. Conservative same-bar ambiguity handling.

---

## 6. Project Success Definition

The project succeeds when it can help the user answer:

```text
Is this strategy merely a pretty backtest,
or does it survive realistic validation pressure?
```

A strategy candidate is interesting only if it survives:

1. IS / Validation / OOS.
2. Cost and slippage pressure.
3. Parameter perturbation.
4. Random missed trades.
5. Monte Carlo.
6. Walk-forward.
7. Explainability review.

---

## 7. Forbidden Agent Behaviors

Agents must not:

1. Claim a feature works without running or describing verification.
2. Silently ignore failed tests.
3. Modify unrelated files.
4. Rename major folders without approval.
5. Introduce hidden global state.
6. Put trading logic inside UI widgets.
7. Add dependencies without justification.
8. Generate fake sample performance and present it as real.
9. Treat generated strategies as financial advice.
10. Optimize on OOS.
11. Add live trading.
12. Add broker API.
13. Add complex features before current milestone is complete.
14. Create multiple competing architectures.
15. Skip changelog updates.
16. Skip task status updates.

---

## 8. Required Response Format for Agents

When an agent completes a task, it must report:

```text
## Completed

- ...

## Files Changed

- ...

## Verification

- Command:
- Result:

## Known Issues

- ...

## Risks

- ...

## Next Suggested Task

- ...

## Handoff Prompt

Copy-paste prompt for the next model:
```

---

## 9. If Unsure

If unsure, agents must:

1. Stop.
2. State the uncertainty.
3. Inspect the relevant files.
4. Propose the smallest safe next step.
5. Avoid speculative rewrites.

Do not fill gaps with confident hallucinations.

---

## 10. Final Rule

The project is allowed to grow only through verified, reproducible, documented steps.

```text
No magic.
No silent assumptions.
No fake robustness.
No giant rewrites.
No UI-engine spaghetti.
No live trading in MVP.
```

This is the soul of Quant Strategy Lab.
