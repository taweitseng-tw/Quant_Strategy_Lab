# Packaging Path Spike - Tasks 307-312

> Decision spike. No packaging implementation was created in this task.
> Generated: 2026-06-10

## Goal

Choose the smallest practical packaging path for the first formal Windows
desktop release of Quant Strategy Lab.

The first release should reduce user friction compared with a source checkout
and virtual environment. This spike compares three paths and recommends one
follow-up implementation task.

## Options

| Option | Fit for first release | Strengths | Main risks |
|---|---|---|---|
| PyInstaller executable | Recommended | Fast iteration, common PySide6 support, no C compiler, simple Windows artifact. | Large binary, Qt plugin collection must be verified, resource paths need explicit handling. |
| Nuitka executable | Not first choice | Potentially smaller/faster executable after tuning. | Requires compiler toolchain, slower builds, more setup burden for local and CI builds. |
| pip-installable entrypoint | Developer convenience only | Simple Python packaging path, no bundled Qt plugin collection. | Still requires Python, venv/pip knowledge, and dependency installation. Does not solve the first-release user friction. |

## Recommendation

Use PyInstaller for the first formal desktop packaging implementation.

Recommended first implementation shape:

```powershell
python -m pip install pyinstaller
python -m PyInstaller --onedir --windowed --name QuantStrategyLab --add-data "sample_data;sample_data" app/main.py
```

`--onedir` is recommended for the first verified build instead of `--onefile`.
It is easier to inspect missing DLLs, Qt plugins, and bundled data. A later task
can evaluate `--onefile` after the first `--onedir` package launches reliably.

## Why PyInstaller First

1. `app/main.py` already has a normal `main()` entrypoint and can be used as an
   entry script.
2. PyInstaller is the fastest path to a Windows desktop artifact without adding
   compiler setup.
3. Qt/PySide packaging issues are easier to inspect in a directory build.
4. The current product needs release-path confidence more than binary-size
   optimization.

## Risks to Verify in the Implementation Task

| Risk | Verification need |
|---|---|
| Qt platform plugins | Confirm the packaged app launches without missing `platforms` plugin errors. |
| Sample data path | Confirm bundled `sample_data/sample_ohlcv.csv` is discoverable or document that users import it from the source tree. |
| Project folder behavior | Confirm packaged app can create/open a project folder outside the build directory. |
| Startup smoke | Add a packaged-exe smoke command using `QSL_EXIT_AFTER_MS` if the executable can be built locally. |
| Build size | Record output folder size, but do not optimize size in the first implementation. |
| Antivirus false positives | Note as a release risk; do not solve in the first packaging task. |

## Why Not Nuitka First

Nuitka may be useful later, but it adds compiler setup and slower feedback loops.
For this project stage, the risk is not runtime speed; the risk is whether a
new evaluator can launch the desktop app without source setup.

## Why Not pip Entry Point First

A pip entrypoint is useful for developers and CI, but it still requires Python
and dependency installation. It should be considered after the executable path,
or as a secondary developer install path.

## Next Implementation Task

Tasks 313-318 - PyInstaller Onedir Build Spike

Do:

1. Add a minimal build document or script for the PyInstaller `--onedir` build.
2. Keep PyInstaller as a dev/build dependency, not a runtime dependency, unless
   the project explicitly accepts a packaging dependency change.
3. Build locally and record whether `dist/QuantStrategyLab/QuantStrategyLab.exe`
   exists.
4. Run the packaged executable with `QSL_EXIT_AFTER_MS` if possible.
5. Update docs with exact results and known packaging gaps.

Do not:

1. Add installer generation.
2. Add release publishing.
3. Add `--onefile` until `--onedir` launch is verified.
4. Change application architecture for packaging without a concrete failure.
