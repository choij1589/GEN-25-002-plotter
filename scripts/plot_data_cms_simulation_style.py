#!/usr/bin/env python3
# python3 plot_dat_cms_simulation_style.py Z_mass.dat Z_pT_peak.dat jet_multi_exclusive.dat
import argparse, os, re, math, glob
import numpy as np
import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt

COLOR_MAP = {
    'red': '#EE3311',
    'blue': '#3366FF',
    'green': '#109618',
    'orange': '#FF9900',
    'black': 'black',
    'purple': '#990099',
}
STYLE_MAP = {
    'solid': '-',
    'dashed': '--',
    'dashdotted': '-.',
    'dotted': ':',
}

# Plot-specific adjustments requested by the user
PLOT_OVERRIDES = {
    'Z_mass.dat': {
        'ratio_ylim': (0.7, 1.3),
        'legend': {'x': 0.33, 'y': -0.03, 'loc': 'lower left'},
        'hide_ratio_top_label': False,
    },
    'Z_pT_peak.dat': {
        'ratio_ylim': (0.7, 1.3),
        'legend': {'x': 0.31, 'y': 1.00, 'loc': 'upper left'},
        'hide_ratio_top_label': True,   # hide 1.3
    },
    'jet_multi_exclusive.dat': {
        'ratio_ylim': (0.8, 1.2),
        'legend': {'x': 0.08, 'y': 0.03, 'loc': 'lower left'},
        'hide_ratio_top_label': True,   # hide 1.2
    },
}


def parse_dat(path):
    plot = {}
    histos = []
    state = None
    current = None
    for raw in open(path):
        line = raw.rstrip('\n')
        if line.startswith('# BEGIN PLOT'):
            state = 'plot'
            continue
        if line.startswith('# END PLOT'):
            state = None
            continue
        if line.startswith('# BEGIN HISTO1D'):
            state = 'histo'
            current = {'data': []}
            continue
        if line.startswith('# END HISTO1D'):
            histos.append(current)
            current = None
            state = None
            continue
        if state == 'plot':
            if '=' in line:
                k, v = line.split('=', 1)
                plot[k.strip()] = v.strip()
        elif state == 'histo':
            if not line or line.startswith('# xlow'):
                continue
            if '=' in line and not re.match(r'^[-+0-9.eE]+\s', line):
                k, v = line.split('=', 1)
                current[k.strip()] = v.strip()
            elif not line.startswith('#'):
                parts = line.split()
                if len(parts) >= 5:
                    current['data'].append(tuple(map(float, parts[:5])))
    return plot, histos


def rebin_histo(h, factor):
    if factor <= 1:
        return h
    data = h['data']
    new = []
    for i in range(0, len(data), factor):
        chunk = data[i:i + factor]
        if not chunk:
            continue
        xlow = chunk[0][0]
        xhigh = chunk[-1][1]
        widths = np.array([c[1] - c[0] for c in chunk], float)
        vals = np.array([c[2] for c in chunk], float)
        em = np.array([c[3] for c in chunk], float)
        ep = np.array([c[4] for c in chunk], float)
        totw = widths.sum()
        val = float(np.sum(vals * widths) / totw)
        errm = float(np.sqrt(np.sum((em * widths) ** 2)) / totw)
        errp = float(np.sqrt(np.sum((ep * widths) ** 2)) / totw)
        new.append((xlow, xhigh, val, errm, errp))
    h = dict(h)
    h['data'] = new
    return h


def clean_math_text(s):
    s = s.replace('Primodial', 'Primordial')
    if '$k_T^{\\mathrm{prim}} = 2.48$' in s and not s.endswith(')'):
        s = s + ')'
    return s


def format_log_major(val, pos=None):
    if val <= 0:
        return ''
    e = np.log10(val)
    if abs(e - round(e)) > 1e-10:
        return ''
    n = int(round(e))
    if n == 0:
        return '1'
    if n == 1:
        return '10'
    return rf'$10^{{{n}}}$'


def expand_inputs(inputs):
    paths = []
    for item in inputs:
        matches = sorted(glob.glob(item))
        if matches:
            paths.extend(matches)
        elif os.path.exists(item):
            paths.append(item)
        else:
            raise FileNotFoundError(f'No such file or pattern match: {item}')
    # preserve order while deduplicating
    out = []
    seen = set()
    for p in paths:
        ap = os.path.abspath(p)
        if ap not in seen:
            out.append(ap)
            seen.add(ap)
    return out


def draw_plot(datfile, outdir='.', suffix=''):
    plot, histos = parse_dat(datfile)
    if not histos:
        raise RuntimeError(f'No histograms found in {datfile}')
    basename = os.path.basename(datfile)
    overrides = PLOT_OVERRIDES.get(basename, {})

    rebin = int(plot.get('Rebin', '1'))
    histos = [rebin_histo(h, rebin) for h in histos]
    refpath = plot.get('RatioPlotReference', histos[0].get('Path', ''))
    ref = next((h for h in histos if h.get('Path', '') == refpath), histos[0])

    plt.rcParams['text.usetex'] = False
    plt.rc('font', family='DejaVu Sans')
    mpl.rcParams.update({
        'figure.figsize': (7.18, 6.37),
        'axes.linewidth': 1.0,
        'xtick.direction': 'in', 'ytick.direction': 'in',
        'xtick.top': True, 'ytick.right': True,
        'xtick.minor.visible': True, 'ytick.minor.visible': True,
        'xtick.major.size': 7, 'xtick.minor.size': 3.5,
        'ytick.major.size': 7, 'ytick.minor.size': 3.5,
        'legend.frameon': False,
        'errorbar.capsize': 0,
        'axes.unicode_minus': False,
    })

    fig, (ax, rax) = plt.subplots(
        2, 1, sharex=True, figsize=(7.18, 6.37),
        gridspec_kw={'height_ratios': (6, 4), 'hspace': 0.035}
    )
    fig.subplots_adjust(left=0.145, right=0.972, top=0.958, bottom=0.118)

    legend_handles, legend_labels = [], []
    for i, h in enumerate(histos):
        arr = np.array(h['data'], float)
        xlow, xhigh, y, em, ep = arr[:, 0], arr[:, 1], arr[:, 2], arr[:, 3], arr[:, 4]
        x = 0.5 * (xlow + xhigh)
        edges = np.r_[xlow[0], xhigh]
        ystep = np.r_[y[0], y]

        color = COLOR_MAP.get(h.get('LineColor', 'black').lower(), h.get('LineColor', 'black'))
        ls = STYLE_MAP.get(h.get('LineStyle', 'solid').lower(), '-')
        lw = 1.6 if color == '#FF9900' else 1.4

        line, = ax.plot(edges, ystep, drawstyle='steps-pre', color=color, linestyle=ls, linewidth=lw)
        ax.errorbar(x, y, yerr=np.vstack([em, ep]), fmt='none', ecolor=color, elinewidth=0.8, alpha=0.9)
        legend_handles.append(line)
        legend_labels.append(clean_math_text(h.get('Title', f'Sample {i + 1}')))

        ref_arr = np.array(ref['data'], float)
        if len(ref_arr) != len(arr):
            raise RuntimeError(f'Binning mismatch in {datfile}')
        refy = ref_arr[:, 2]
        ratio = np.divide(y, refy, out=np.full_like(y, np.nan), where=refy != 0)
        rem = np.divide(em, refy, out=np.zeros_like(em), where=refy != 0)
        rep = np.divide(ep, refy, out=np.zeros_like(ep), where=refy != 0)
        rstep = np.r_[ratio[0], ratio]
        rax.plot(edges, rstep, drawstyle='steps-pre', color=color, linestyle=ls, linewidth=lw)
        rax.errorbar(x, ratio, yerr=np.vstack([rem, rep]), fmt='none', ecolor=color, elinewidth=0.8, alpha=0.9)

    # axis labels; upper y title top-aligned as requested
    font_size = 22
    ax.set_ylabel(plot.get('YLabel', ''), fontsize=font_size, ha='center')
    rax.set_ylabel(plot.get('RatioPlotYLabel', 'Ratio'), fontsize=font_size)
    rax.set_xlabel(plot.get('XLabel', ''), fontsize=font_size, ha='right')
    ax.yaxis.set_label_coords(-0.085, 0.59) # Z_mass
    #ax.yaxis.set_label_coords(-0.085, 0.535) # Z_pT_peak
    #ax.yaxis.set_label_coords(-0.085, 0.745) # jet_multi_exclusive
    rax.yaxis.set_label_coords(-0.085, 0.5)
    rax.xaxis.set_label_coords(1.0, -0.145)

    ax.text(0.0, 1.012, 'CMS', transform=ax.transAxes, ha='left', va='bottom', fontsize=24, fontweight='bold')
    ax.text(0.155, 1.012, 'Simulation', transform=ax.transAxes, ha='left', va='bottom', fontsize=20, fontstyle='italic')
    ax.text(0.435, 1.012, 'Preliminary', transform=ax.transAxes, ha='left', va='bottom', fontsize=20, fontstyle='italic')

    # scales and limits
    if plot.get('LogY', '0') == '1':
        ax.set_yscale('log')
        ax.yaxis.set_major_locator(mpl.ticker.LogLocator(base=10.0, subs=(1.0,), numticks=100))
        ax.yaxis.set_minor_locator(mpl.ticker.LogLocator(base=10.0, subs=np.arange(2, 10) * 0.1, numticks=100))
        ax.yaxis.set_major_formatter(mpl.ticker.FuncFormatter(format_log_major))
        ax.yaxis.set_minor_formatter(mpl.ticker.NullFormatter())
    xmins = [h['data'][0][0] for h in histos]
    xmaxs = [h['data'][-1][1] for h in histos]
    xmin = min(xmins)
    xmax = float(plot.get('XMax', max(xmaxs)))
    ax.set_xlim(xmin, xmax)

    all_y = np.concatenate([np.array([r[2] for r in h['data']], float) for h in histos])
    positive = all_y[all_y > 0]
    if plot.get('LogY', '0') == '1':
        ymin = positive.min() / 1.8
        ymax = positive.max() * 1.8
    else:
        ymin = 0.0
        ymax = positive.max() * 1.18
    ax.set_ylim(ymin, ymax)

    # ratio y-range and ticks
    if 'ratio_ylim' in overrides:
        rmin, rmax = overrides['ratio_ylim']
    else:
        rmin = float(plot.get('RatioPlotYMin', '0.8'))
        rmax = float(plot.get('RatioPlotYMax', '1.2'))
    rax.axhline(1.0, color='black', linewidth=1.0)
    rax.set_ylim(rmin, rmax)
    major_ticks = np.arange(rmin, rmax + 0.001, 0.1)
    minor_ticks = np.arange(rmin, rmax + 0.001, 0.05)
    rax.yaxis.set_major_locator(mpl.ticker.FixedLocator(major_ticks))
    rax.yaxis.set_minor_locator(mpl.ticker.FixedLocator(minor_ticks))

    hide_top = overrides.get('hide_ratio_top_label', False)
    def ratio_formatter(val, pos=None):
        if hide_top and abs(val - rmax) < 1e-10:
            return ''
        return f'{val:.1f}'
    rax.yaxis.set_major_formatter(mpl.ticker.FuncFormatter(ratio_formatter))

    xlabel = plot.get('XLabel', '')
    if 'N_{\\mathrm{jet}}' in xlabel or 'N_{\\mathrm{jet}}' in xlabel.replace(' ', ''):
        ticks = np.arange(max(0, math.ceil(xmin)), math.floor(xmax) + 1)
        rax.set_xticks(ticks)
        rax.set_xticklabels([str(int(t)) for t in ticks])
        rax.xaxis.set_minor_locator(mpl.ticker.NullLocator())

    for axis in (ax, rax):
        axis.tick_params(which='both', direction='in', top=True, right=True, labelsize=16)
        for s in axis.spines.values():
            s.set_linewidth(1.0)

    # legend placement after limits
    if plot.get('Legend', '0') == '1':
        lcfg = overrides.get('legend', None)
        if lcfg is None:
            lx = float(plot.get('LegendXPos', '0.55'))
            ly = float(plot.get('LegendYPos', '0.88'))
            loc = 'lower left' if ly < 0.5 else 'upper left'
        else:
            lx, ly, loc = lcfg['x'], lcfg['y'], lcfg['loc']
        ax.legend(legend_handles, legend_labels, loc=loc, bbox_to_anchor=(lx, ly), fontsize=15, handlelength=2.8)

    # check panel-boundary overlap; hide lowest upper y major label if needed
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    top_labels = [lab for lab in ax.get_yticklabels() if lab.get_text() and lab.get_visible()]
    low_labels = [lab for lab in rax.get_yticklabels() if lab.get_text() and lab.get_visible()]
    if top_labels and low_labels:
        top_lowest = min(top_labels, key=lambda l: l.get_window_extent(renderer).y0)
        low_highest = max(low_labels, key=lambda l: l.get_window_extent(renderer).y1)
        if top_lowest.get_window_extent(renderer).overlaps(low_highest.get_window_extent(renderer)):
            top_lowest.set_visible(False)

    outbase = os.path.splitext(os.path.basename(datfile))[0] + suffix
    pdf = os.path.join(outdir, outbase + '.pdf')
    fig.savefig(pdf, format='pdf', bbox_inches='tight', pad_inches=0.02)
    plt.close(fig)
    return pdf


def main():
    ap = argparse.ArgumentParser(description='Batch-process .dat plots with CMS Simulation style.')
    ap.add_argument('inputs', nargs='+', help='One or more .dat files or glob patterns, e.g. *.dat')
    ap.add_argument('--outdir', default='.', help='Output directory')
    ap.add_argument('--suffix', default='', help='Suffix appended to output base names')
    args = ap.parse_args()

    files = expand_inputs(args.inputs)
    for f in files:
        pdf = draw_plot(f, outdir=args.outdir, suffix=args.suffix)
        print(pdf)

if __name__ == '__main__':
    main()
