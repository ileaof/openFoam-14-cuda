"""CPU x GPU scaling chart (cavity3D) for the README.

  python plot_scale.py scale.csv <saida_dir>
Gera gpu_scaling_light.png e gpu_scaling_dark.png.
"""
import csv, sys
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

DEC_FMT = FuncFormatter(lambda v, _: f"{v:g}")

THEMES = {
    "light": dict(surface="#fcfcfb", ink="#0b0b0b", ink2="#52514e", muted="#898781",
                  grid="#e1e0d9", axis="#c3c2b7", gpu="#2a78d6", cpu="#eb6834"),
    "dark":  dict(surface="#1a1a19", ink="#f0efec", ink2="#c3c2b7", muted="#898781",
                  grid="#2c2c2a", axis="#383835", gpu="#3987e5", cpu="#d95926"),
}


def read_points(path):
    d = {}
    for r in csv.DictReader(open(path)):
        if r["rc"] != "0" or r["s_per_step"] == "nan":
            continue
        d.setdefault(int(r["cells"]), {})[r["mode"]] = float(r["s_per_step"])
    points = sorted((c, v["cpu"], v["gpu"]) for c, v in d.items() if "cpu" in v and "gpu" in v)
    return points


def fmt(x, nd=1):
    return f"{x:.{nd}f}"


def chart(points, theme, out):
    t = THEMES[theme]
    plt.rcParams.update({"font.family": ["Segoe UI", "DejaVu Sans"], "font.size": 11})
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 4.2), dpi=150,
                                 gridspec_kw=dict(width_ratios=[1.25, 1], wspace=0.28))
    fig.patch.set_facecolor(t["surface"])
    M = [c / 1e6 for c, _, _ in points]
    cpu = [p[1] for p in points]
    gpu = [p[2] for p in points]
    speedup = [c / g for c, g in zip(cpu, gpu)]

    for ax in (a1, a2):
        ax.set_facecolor(t["surface"])
        ax.grid(axis="y", color=t["grid"], linewidth=1)
        ax.set_axisbelow(True)
        for s in ("top", "right", "left"):
            ax.spines[s].set_visible(False)
        ax.spines["bottom"].set_color(t["axis"])
        ax.tick_params(colors=t["muted"], length=0, labelsize=10)
        ax.set_xlabel("million cells", color=t["ink2"], fontsize=10)
        ax.yaxis.set_major_formatter(DEC_FMT)
    a1.xaxis.set_major_formatter(DEC_FMT)

    # --- time per step (two series, legend + end label)
    for y, color, label in ((cpu, t["cpu"], "CPU (GAMG)"), (gpu, t["gpu"], "GPU (AMGX)")):
        a1.plot(M, y, color=color, linewidth=2, marker="o", markersize=8,
                markeredgecolor=t["surface"], markeredgewidth=2, label=label, zorder=3)
        a1.annotate(label, (M[-1], y[-1]), xytext=(8, 0), textcoords="offset points",
                    va="center", color=t["ink2"], fontsize=10)
    a1.set_ylim(0, max(cpu) * 1.12)
    a1.set_xlim(0, max(M) * 1.28)
    a1.set_title("Time per step (s)", loc="left", color=t["ink"], fontsize=12, pad=22)
    a1.text(0, 1.02, "lower is better", transform=a1.transAxes,
            color=t["muted"], fontsize=9, va="bottom")
    leg = a1.legend(loc="upper left", frameon=False, fontsize=10)
    for txt in leg.get_texts():
        txt.set_color(t["ink2"])

    # --- GPU speed-up (one series; break-even at 1x)
    xs = list(range(len(M)))
    a2.bar(xs, speedup, width=0.62, color=t["gpu"], zorder=2,
           edgecolor=t["surface"], linewidth=2)
    a2.axhline(1.0, color=t["axis"], linewidth=1, zorder=3)
    for x, g in zip(xs, speedup):
        a2.annotate(f"{fmt(g, 2)}×", (x, g), xytext=(0, 4), textcoords="offset points",
                    ha="center", color=t["ink"], fontsize=10)
    a2.set_xticks(xs, [f"{fmt(m, 1)} M" for m in M])
    a2.set_ylim(0, max(speedup) * 1.2)
    a2.set_xlim(-0.6, len(M) - 0.4)
    a2.set_title("GPU speed-up (CPU ÷ GPU)", loc="left", color=t["ink"], fontsize=12, pad=22)
    a2.text(0, 1.02, "gray line: break-even (1×)", transform=a2.transAxes,
            color=t["muted"], fontsize=9, va="bottom")

    fig.text(0.01, 0.005,
             "cavity3D, icoFoam PISO, 4 MPI ranks · RTX 4050 Laptop (6 GB) vs. the same laptop's CPU · "
             "average after 5 warm-up steps",
             color=t["muted"], fontsize=8.5)
    fig.subplots_adjust(left=0.05, right=0.98, top=0.86, bottom=0.2)
    fig.savefig(out, facecolor=t["surface"])
    plt.close(fig)
    print("ok", out)


if __name__ == "__main__":
    points = read_points(sys.argv[1])
    for c, a, b in points:
        print(f"{c/1e6:5.2f} M  cpu {a:.3f}  gpu {b:.3f}  speed-up {a/b:.2f}")
    o = Path(sys.argv[2])
    for theme in ("light", "dark"):
        chart(points, theme, o / f"gpu_scaling_{theme}.png")
