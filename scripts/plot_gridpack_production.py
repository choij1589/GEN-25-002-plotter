#!/usr/bin/env python
"""
Plot gridpack production time (ME stacked with Others) for DY and TT.
Output: figures/gridpack_production_dy.png/pdf
        figures/gridpack_production_tt.png/pdf
"""
import os
import json
import ROOT
import cmsstyle as CMS

ROOT.gROOT.SetBatch(True)
CMS.setCMSStyle()

# Load data
data_path = os.path.join(os.path.dirname(__file__), "..", "raw", "gridpack_production.json")
with open(data_path) as f:
    data = json.load(f)

# Colors from plotter/plotter.py PALETTE
PALETTE = [
    ROOT.TColor.GetColor("#5790fc"),
    ROOT.TColor.GetColor("#f89c20"),
    ROOT.TColor.GetColor("#e42536"),
    ROOT.TColor.GetColor("#964a8b"),
    ROOT.TColor.GetColor("#9c9ca1"),
    ROOT.TColor.GetColor("#7a21dd"),
]
PALETTE_LIGHT = [
    ROOT.TColor.GetColor("#a8c4fd"),
    ROOT.TColor.GetColor("#fcd48a"),
    ROOT.TColor.GetColor("#f09aa0"),
    ROOT.TColor.GetColor("#cba5d4"),
    ROOT.TColor.GetColor("#cdcdd0"),
    ROOT.TColor.GetColor("#c3a5ee"),
]

# Configurations (top → bottom in the plot); JSON keys → display labels
configs = ["MG362 UPSTREAM", "CPP-NONE", "CPP-AVX2", "CPP-AVX512", "CUDA"]
display_labels = {
    "MG362 UPSTREAM": "UPSTREAM",
    "CPP-NONE":       "CPP-NONE",
    "CPP-AVX2":       "CPP-AVX2",
    "CPP-AVX512":     "CPP-AVX512",
    "CUDA":           "CUDA",
}
n_bins = len(configs)

def get_val(entry, key):
    """Handle both 'ME' and 'ME (h)' key styles in the JSON."""
    return entry.get(key, entry.get(f"{key} (h)", 0.0))

def make_hists(process_data, name_prefix):
    """Create total and ME histograms for overlaid horizontal bars.
    h_total (ME+Others, light) is drawn first; h_me (dark) overlaid on top.
    Bins are filled in reverse so the first config appears at the top."""
    h_total = ROOT.TH1F(f"{name_prefix}_total", "Others", n_bins, 0, n_bins)
    h_me    = ROOT.TH1F(f"{name_prefix}_me",    "ME",     n_bins, 0, n_bins)
    for i, cfg in enumerate(reversed(configs)):
        if cfg in process_data:
            entry  = process_data[cfg]
            me     = get_val(entry, "ME")
            others = get_val(entry, "others")
            h_total.SetBinContent(i + 1, me + others)
            h_me.SetBinContent(i + 1, me)
    for h in (h_total, h_me):
        h.SetDirectory(0)
        h.SetStats(0)
        h.SetBarWidth(0.6)
        h.SetBarOffset(0.2)
    return h_total, h_me

def make_canvas(canv_name, xmax, xtitle):
    """Create a CMS canvas with categorical y-axis labels."""
    CMS.SetExtraText("Simulation Preliminary")
    CMS.SetEnergy(13.6)
    CMS.SetLumi(None, run="Run 3")
    canv = CMS.cmsCanvas(
        canv_name,
        0, xmax,
        0, n_bins,
        xtitle,
        "",
        square=False, iPos=0, extraSpace=0.18,
    )
    frame = CMS.GetCmsCanvasHist(canv)
    frame.GetYaxis().SetTickLength(0)
    frame.GetYaxis().SetNdivisions(2 * n_bins, False)
    reversed_configs = list(reversed(configs))
    for i in range(2 * n_bins + 1):
        if i % 2 == 1:
            label = display_labels[reversed_configs[i // 2]]
            frame.GetYaxis().ChangeLabel(i + 1, -1, -1, -1, -1, -1, label)
        else:
            frame.GetYaxis().ChangeLabel(i + 1, -1, 0, -1, -1, -1, "")
    return canv

out_dir = os.path.join(os.path.dirname(__file__), "..", "figures")
os.makedirs(out_dir, exist_ok=True)

# ── DY plot ────────────────────────────────────────────────────────────────────
h_dy_total, h_dy_me = make_hists(data["DY"], "dy")
h_dy_total.SetFillColor(PALETTE_LIGHT[0])
h_dy_total.SetLineColor(PALETTE_LIGHT[0])
h_dy_me.SetFillColor(PALETTE[0])
h_dy_me.SetLineColor(PALETTE[0])

canv_dy = make_canvas("canv_dy", 250, "Gridpack production time (h)")
h_dy_total.Draw("HBAR SAME")
h_dy_me.Draw("HBAR SAME")
canv_dy.RedrawAxis()

leg_dy = CMS.cmsLeg(0.70, 0.30, 0.92, 0.44, textSize=0.04)
CMS.addToLegend(leg_dy, (h_dy_me,    "ME",     "F"))
CMS.addToLegend(leg_dy, (h_dy_total, "Others", "F"))
leg_dy.Draw()

for ext in ("png", "pdf"):
    canv_dy.SaveAs(os.path.join(out_dir, f"gridpack_production_dy.{ext}"))
    print(f"Saved: figures/gridpack_production_dy.{ext}")

# ── TT plot ────────────────────────────────────────────────────────────────────
h_tt_total, h_tt_me = make_hists(data["TT"], "tt")
h_tt_total.SetFillColor(PALETTE_LIGHT[2])
h_tt_total.SetLineColor(PALETTE_LIGHT[2])
h_tt_me.SetFillColor(PALETTE[2])
h_tt_me.SetLineColor(PALETTE[2])

canv_tt = make_canvas("canv_tt", 12, "Gridpack production time (h)")
h_tt_total.Draw("HBAR SAME")
h_tt_me.Draw("HBAR SAME")
canv_tt.RedrawAxis()

leg_tt = CMS.cmsLeg(0.70, 0.30, 0.92, 0.44, textSize=0.04)
CMS.addToLegend(leg_tt, (h_tt_me,    "ME",     "F"))
CMS.addToLegend(leg_tt, (h_tt_total, "Others", "F"))
leg_tt.Draw()

for ext in ("png", "pdf"):
    canv_tt.SaveAs(os.path.join(out_dir, f"gridpack_production_tt.{ext}"))
    print(f"Saved: figures/gridpack_production_tt.{ext}")
