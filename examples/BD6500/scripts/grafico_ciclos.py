#!/usr/bin/env python3
"""Pressao media no cilindro por ciclo (CFD) x ensaio.
   python3 scripts/grafico_ciclos.py <caso> <ensaio.csv> <saida.png>
   FIG_LANG=en python3 scripts/grafico_ciclos.py ...   -> textos em ingles (padrao: portugues)
<caso>/postProcessing/cilindro/*/volFieldValue.dat: tempo (= CA + 360 + 720*(ciclo-1)), p, T.
ensaio.csv: theta [rad], P [kPa]."""
import glob, math, os, sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

TXT = {
    "pt": dict(ensaio="ensaio (carga 60 %)", cfd="CFD 3D, ciclo {}", x="ângulo do virabrequim [° CA]",
               y="pressão média no cilindro [kPa]", t1="Ciclo completo", t2="Combustão (zoom)",
               pe="ensaio: {:.2f} MPa a {:.1f}°", pc="ciclo {}: {:.2f} MPa a {:.1f}°",
               sup="Branco BD-6500, 3311 rpm, carga 60 % — Wiebe 2 estágios (454 J/ciclo)"),
    "en": dict(ensaio="engine test (60 % load)", cfd="3D CFD, cycle {}", x="crank angle [° CA]",
               y="mean cylinder pressure [kPa]", t1="Full cycle", t2="Combustion (zoom)",
               pe="engine test: {:.2f} MPa at {:.1f}°", pc="cycle {}: {:.2f} MPa at {:.1f}°",
               sup="Branco BD-6500, 3311 rpm, 60 % load — 2-stage Wiebe (454 J/cycle)"),
}
L = TXT[os.environ.get("FIG_LANG", "pt")]

caso, ensaio, saida = sys.argv[1:4]
d = {}
for a in sorted(glob.glob(caso + "/postProcessing/cilindro/*/volFieldValue.dat")):
    for linha in open(a):
        if linha.startswith("#") or not linha.strip():
            continue
        c = linha.split()
        d[float(c[0])] = float(c[1])
ciclos = {}
for t in sorted(d):
    k = max(int((t - 1e-9) // 720), 0)   # t = 720k fecha o ciclo k (CA +360)
    ciclos.setdefault(k, ([], []))
    ciclos[k][0].append(t - 720 * k - 360)
    ciclos[k][1].append(d[t] / 1e3)

ex_ca, ex_p = [], []
for linha in open(ensaio):
    if linha.startswith("#") or not linha.strip():
        continue
    a, p = linha.split(",")
    ex_ca.append(math.degrees(float(a))); ex_p.append(float(p))

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6), gridspec_kw={"width_ratios": [1.6, 1]})
cores = ["#c9d8ea", "#9bb7d9", "#5f8bc4", "#1f4e8c", "#0b2a55"]
for ax in (ax1, ax2):
    ax.plot(ex_ca, ex_p, "o", ms=2.5, color="#444444", label=L["ensaio"])
    for k, (ca, p) in sorted(ciclos.items()):
        ax.plot(ca, p, "-", lw=1.2 + 0.4 * k, color=cores[min(k, 4)], label=L["cfd"].format(k + 1))
    ax.set_xlabel(L["x"])
    ax.set_ylabel(L["y"])
    ax.grid(alpha=0.3)
ax1.set_xlim(-360, 360); ax1.set_title(L["t1"])
ax2.set_xlim(-40, 60); ax2.set_title(L["t2"])
im = max(range(len(ex_p)), key=lambda i: ex_p[i])
txt = [L["pe"].format(ex_p[im] / 1e3, ex_ca[im])]
for k, (ca, p) in sorted(ciclos.items()):
    m = max(range(len(p)), key=lambda i: p[i])
    txt.append(L["pc"].format(k + 1, p[m] / 1e3, ca[m]))
ax2.text(0.03, 0.97, "\n".join(txt), transform=ax2.transAxes, va="top", fontsize=9)
h, l = ax1.get_legend_handles_labels()
fig.legend(h, l, loc="lower center", ncol=5, fontsize=9, frameon=False)
fig.suptitle(L["sup"], fontsize=12)
fig.tight_layout(rect=(0, 0.07, 1, 1))
fig.savefig(saida, dpi=130)
print("ok", saida, " | ".join(txt))
