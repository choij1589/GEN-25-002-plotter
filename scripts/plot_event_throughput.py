#!/usr/bin/env python
"""
Plot event throughput (LHE+GEN) with std dev error bars for DY and TT.
TT values scaled x10 for visibility on the same axis.
Output: figures/event_throughput.png/pdf
"""
import os
import json
import array
import ROOT
import cmsstyle as CMS

ROOT.gROOT.SetBatch(True)
CMS.setCMSStyle()

# Load data
data_path = os.path.join(os.path.dirname(__file__), "..", "raw", "event_throughput.json")
with open(data_path) as f:
    data = json.load(f)

# Colors from PALETTE
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

# Configurations and display labels
configs = ["MG362 UPSTREAM", "CPP-NONE", "CPP-AVX2", "CPP-AVX512", "CUDA"]
display_labels = {
    "MG362 UPSTREAM": "UPSTREAM",
    "CPP-NONE":       "CPP-NONE",
    "CPP-AVX2":       "CPP-AVX2",
    "CPP-AVX512":     "CPP-AVX512",
    "CUDA":           "CUDA",
}
n_configs = len(configs)
TT_SCALE = 10.0

def make_graph(process_data, name, scale=1.0):
    """Build a TGraphErrors at bin-center x positions (0.5, 1.5, ...)."""
    xs  = array.array('d')
    ys  = array.array('d')
    exs = array.array('d')
    eys = array.array('d')
    for i, cfg in enumerate(configs):
        if cfg in process_data:
            entry = process_data[cfg]
            xs.append(i + 0.5)
            ys.append(entry["throughput (evt/s)"] * scale)
            exs.append(0.0)
            eys.append(entry["standard deviation (evt/s)"] * scale)
    return ROOT.TGraphErrors(len(xs), xs, ys, exs, eys)

# Build graphs
g_dy = make_graph(data["DY"], "g_dy")
g_tt = make_graph(data["TT"], "g_tt", scale=TT_SCALE)

for g, color in [(g_dy, dy_color), (g_tt, tt_color)]:
    g.SetLineColor(color)
    g.SetMarkerColor(color)
    g.SetFillColorAlpha(color, 0.3)
    g.SetLineWidth(3)
    g.SetMarkerStyle(20)
    g.SetMarkerSize(1.5)

# Canvas
CMS.SetExtraText("Simulation Preliminary")
CMS.SetEnergy(13.6)
CMS.SetLumi(None, run="Run 3")
canv = CMS.cmsCanvas(
    "canv_throughput",
    0, n_configs,
    0, 25,
    "",
    "Event throughput (evts/s)",
    square=False, iPos=0, extraSpace=0.01,
)

# Categorical x-axis labels at bin centers
frame = CMS.GetCmsCanvasHist(canv)
frame.GetXaxis().SetTickLength(0)
frame.GetXaxis().SetNdivisions(2 * n_configs, False)
frame.GetXaxis().SetLabelSize(0.032)
for i in range(2 * n_configs + 1):
    if i % 2 == 1:  # half-integer → bin center
        frame.GetXaxis().ChangeLabel(i + 1, -1, -1, -1, -1, -1, display_labels[configs[i // 2]])
    else:           # integer → hide
        frame.GetXaxis().ChangeLabel(i + 1, -1, 0, -1, -1, -1, "")

g_dy.Draw("LP SAME")
g_tt.Draw("LP SAME")
canv.RedrawAxis()

leg = CMS.cmsLeg(0.18, 0.72, 0.50, 0.89, textSize=0.04)
CMS.addToLegend(leg, (g_dy, "DY",        "LEP"))
CMS.addToLegend(leg, (g_tt, "TT (#times10)", "LEP"))
leg.Draw()
CMS.drawText("LHE+GEN", 0.20, 0.65, 62, 11, 0.05)

out_dir = os.path.join(os.path.dirname(__file__), "..", "figures")
os.makedirs(out_dir, exist_ok=True)
for ext in ("png", "pdf"):
    canv.SaveAs(os.path.join(out_dir, f"event_throughput.{ext}"))
    print(f"Saved: figures/event_throughput.{ext}")
