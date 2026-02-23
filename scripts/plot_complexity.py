#!/usr/bin/env python
"""
Plot number of Feynman diagrams and number of subprocesses
vs jet multiplicity for DY and TT processes (two separate plots).
Output: figures/number_of_feynman_diagrams.png/pdf
        figures/number_of_subprocesses.png/pdf
"""
import os
import json
import ROOT
import cmsstyle as CMS

ROOT.gROOT.SetBatch(True)
CMS.setCMSStyle()

# Load data
data_path = os.path.join(os.path.dirname(__file__), "..", "raw", "complexity.json")
with open(data_path) as f:
    data = json.load(f)

# Jet multiplicity bins: 0j through 4j
jet_labels = ["0j", "1j", "2j", "3j", "4j"]
n_bins = len(jet_labels)

# Colors from plotter/plotter.py PALETTE
PALETTE = [
    ROOT.TColor.GetColor("#5790fc"),
    ROOT.TColor.GetColor("#f89c20"),
    ROOT.TColor.GetColor("#e42536"),
    ROOT.TColor.GetColor("#964a8b"),
    ROOT.TColor.GetColor("#9c9ca1"),
    ROOT.TColor.GetColor("#7a21dd"),
]
dy_color = PALETTE[0]
tt_color = PALETTE[2]

def make_hist(name, title, values):
    h = ROOT.TH1F(name, title, n_bins, 0, n_bins)
    for i, label in enumerate(reversed(jet_labels)):  # bin 1 = 4j (bottom), bin 5 = 0j (top)
        if label in values:
            h.SetBinContent(i + 1, values[label])
    h.SetDirectory(0)
    h.SetStats(0)
    return h

def make_bar_canvas(canv_name, xmin, xmax, xtitle):
    """Create a CMS canvas with horizontal bars and categorical y-axis labels."""
    CMS.SetExtraText("Simulation Preliminary")
    CMS.SetEnergy(13.6)
    CMS.SetLumi(None, run="Run 3")
    canv = CMS.cmsCanvas(
        canv_name,
        xmin, xmax,   # x range: values (log scale)
        0, n_bins,    # y range: categories
        xtitle,
        "Number of additional jets",
        square=True, iPos=0, extraSpace=0.01,
    )
    canv.SetLogx()
    # Label y-axis at bin centers (half-integer), hide all y-axis ticks
    frame = CMS.GetCmsCanvasHist(canv)
    frame.GetYaxis().SetTickLength(0)
    frame.GetYaxis().SetNdivisions(2 * n_bins, False)
    reversed_labels = list(reversed(jet_labels))
    for i in range(2 * n_bins + 1):
        if i % 2 == 1:  # half-integer → bin center
            frame.GetYaxis().ChangeLabel(i + 1, -1, -1, -1, -1, -1, reversed_labels[i // 2])
        else:           # integer → hide
            frame.GetYaxis().ChangeLabel(i + 1, -1, 0, -1, -1, -1, "")
    return canv

out_dir = os.path.join(os.path.dirname(__file__), "..", "figures")
os.makedirs(out_dir, exist_ok=True)

# ── Plot 1: Number of Feynman diagrams ────────────────────────────────────────
h_dy = make_hist("h_dy", "DY", data["DY"]["number of Feynman diagrams"])
h_tt = make_hist("h_tt", "TT", data["TT"]["number of Feynman diagrams"])

for h, color in [(h_dy, dy_color), (h_tt, tt_color)]:
    h.SetFillColor(color)
    h.SetLineColor(color)
    h.SetLineWidth(1)
    h.SetBarWidth(0.4)

h_dy.SetBarOffset(0.51)  # DY on top
h_tt.SetBarOffset(0.1)   # TT on bottom

canv1 = make_bar_canvas("canv1", 0.5, 2e6, "Number of Feynman diagrams")
h_dy.Draw("HBAR SAME")
h_tt.Draw("HBAR SAME")
canv1.RedrawAxis()

leg1 = CMS.cmsLeg(0.75, 0.7, 0.90, 0.89, textSize=0.04)
CMS.addToLegend(leg1, (h_dy, "DY", "F"))
CMS.addToLegend(leg1, (h_tt, "TT", "F"))
leg1.Draw()

for ext in ("png", "pdf"):
    canv1.SaveAs(os.path.join(out_dir, f"number_of_feynman_diagrams.{ext}"))
    print(f"Saved: figures/number_of_feynman_diagrams.{ext}")

# ── Plot 2: Number of subprocesses ────────────────────────────────────────────
h_dy_sub = make_hist("h_dy_sub", "DY", data["DY"]["number of subprocesses"])
h_tt_sub = make_hist("h_tt_sub", "TT", data["TT"]["number of subprocesses"])

for h, color in [(h_dy_sub, dy_color), (h_tt_sub, tt_color)]:
    h.SetFillColor(color)
    h.SetLineColor(color)
    h.SetLineWidth(1)
    h.SetBarWidth(0.4)

h_dy_sub.SetBarOffset(0.51)  # DY on top
h_tt_sub.SetBarOffset(0.1)   # TT on bottom

canv2 = make_bar_canvas("canv2", 0.5, 5e3, "Number of subprocesses")
h_dy_sub.Draw("HBAR SAME")
h_tt_sub.Draw("HBAR SAME")
canv2.RedrawAxis()

leg2 = CMS.cmsLeg(0.75, 0.7, 0.90, 0.89, textSize=0.04)
CMS.addToLegend(leg2, (h_dy_sub, "DY", "F"))
CMS.addToLegend(leg2, (h_tt_sub, "TT", "F"))
leg2.Draw()

for ext in ("png", "pdf"):
    canv2.SaveAs(os.path.join(out_dir, f"number_of_subprocesses.{ext}"))
    print(f"Saved: figures/number_of_subprocesses.{ext}")
