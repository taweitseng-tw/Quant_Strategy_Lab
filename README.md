# Quant Strategy Lab

Quant Strategy Lab 是一套本地端桌面型量化交易策略生成、回測、驗證、篩選與報告平台。

## Required Reading

所有模型或開發者在修改專案前，必須依序閱讀：

1. `SOUL.md`
2. `AGENTS.md`
3. `docs/PRD.md`
4. `docs/architecture.md`
5. `docs/task_board.md`
6. `docs/changelog.md`

## Current Milestone

v0.2 Alpha — validation expansion release-ready

The v0.2 alpha validation expansion adds:

- **IS/OOS stability gates** — profit factor degradation, drawdown ratio, average trade degradation checks.
- **Remove-best-N trades stress test** — engine, pipeline, widget/report display, and UI controls.
- **Bootstrap Monte Carlo** — trade resampling with 95% confidence intervals, pipeline wiring, display surfaces, and UI controls.
- **Walk-forward per-window equity** — storage, widget summary, and markdown/HTML report tables.
- **Opt-in IS baseline quality precheck** — early-return gate with widget/report visibility.

All features are tested at engine, pipeline, display, and acceptance-smoke levels.

> This software is for research and backtesting purposes only. Backtested performance does not guarantee future results. Not financial advice. No live trading.

## Important Rule

不要一開始就做實盤下單、券商 API、完整 GA / GP、完整 Walk-forward Matrix。
