# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Environment Setup

Always source `setup.sh` before running any scripts:
```bash
source setup.sh
```
This activates the `Nano` micromamba environment which provides ROOT, cmsstyle, and other dependencies.

## Running Scripts

```bash
python scripts/plot_complexity.py
python scripts/plot_gridpack_production.py
python scripts/plot_event_throughput.py
```

Outputs are saved to `figures/` as both `.png` and `.pdf`.

## Architecture

This repository produces CMS-style publication plots from raw JSON data.

- `raw/*.json` — input data (complexity, gridpack production times, event throughput)
- `scripts/plot_*.py` — standalone plotting scripts (one script per figure)
- `figures/` — output plots (generated, not committed)
- `examples/` — reference images showing the target appearance
- `plotter/` — shared analysis utilities (HistoUtils.py, plotter.py); **do not import `plotter.py` directly** — it loads `Luminosity.json` at module level and will raise `FileNotFoundError`

## Plotting Conventions

All plots use ROOT + `cmsstyle` (not matplotlib). Key patterns used throughout:

**CMS header** (set before `cmsCanvas`):
```python
CMS.SetExtraText("Simulation Preliminary")
CMS.SetEnergy(13.6)
CMS.SetLumi(None, run="Run 3")
canv = CMS.cmsCanvas(..., iPos=0, square=False, extraSpace=0.XX)
```

**Categorical axis labels** — ROOT axes are continuous; use this trick:
```python
frame.GetXaxis().SetNdivisions(2 * n_bins, False)
for i in range(2 * n_bins + 1):
    if i % 2 == 1:   # half-integer → bin center → show label
        frame.GetXaxis().ChangeLabel(i + 1, -1, -1, -1, -1, -1, label)
    else:            # integer → hide
        frame.GetXaxis().ChangeLabel(i + 1, -1, 0, -1, -1, -1, "")
```

**Color palette** — defined inline in each script (cannot import from `plotter.py`):
```python
PALETTE       = ["#5790fc", "#f89c20", "#e42536", "#964a8b", "#9c9ca1", "#7a21dd"]
PALETTE_LIGHT = ["#a8c4fd", "#fcd48a", "#f09aa0", "#cba5d4", "#cdcdd0", "#c3a5ee"]
```

**Stacked horizontal bars** — draw `h_total` (light, me+others) first, then `h_me` (dark) on top with identical `SetBarWidth`/`SetBarOffset`. Do **not** use `THStack` for HBAR — it applies bar settings independently per histogram causing unequal bar heights.

**Left margin for long y-axis labels** — use `extraSpace` parameter in `cmsCanvas`, never call `canv.SetLeftMargin()` after canvas creation (misaligns frame).

**Additional styled text** — use `CMS.drawText(text, x, y, font, align, size)` where font `42`=regular, `62`=bold, `52`=italic.
