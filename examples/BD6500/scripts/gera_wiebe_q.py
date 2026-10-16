#!/usr/bin/env python3
"""Tabela q'''(CA) = Q_dot(CA) / V_cilindro(CA) [W/m3] para o heatSource (zona 'cilindro').
   python gera_wiebe_q.py <arquivo de saida>
Usa 'q' (por volume) e nao 'Q' (total): com Q, o heatSource do OF14 divide pelo volume da zona
calculado uma vez na leitura (volume no inicio da rodada), e no PMS o calor aplicado cai a ~7 %.
Com q = Q/V(CA), sum(q*V_i) = Q em cada instante (como no wiebepy).
V_cilindro: com as duas valvulas fechadas (toda a combustao), pi*R^2*(altura) - volume dos pratos."""
import math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import geometria as g

Q_TOTAL, RPM, DESL = 454.0, 3311.0, 360.0
ESTAGIOS = [(0.645569, -19.3271, 64.3982, 2.55489, 6.908),
            (0.354431, 3.66349, 18.9253, 0.367868, 6.908)]


def dxdth(th):
    s = 0.0
    for b, t0, dt, m, a in ESTAGIOS:
        z = (th - t0) / dt
        if z > 0:
            s += b * a * (m + 1) / dt * z**m * math.exp(-a * z**(m + 1))
    return s


def vcil(th):
    return math.pi * g.R_CIL**2 * (-g.pistao_z(th)) - g.V_PRATOS


angs = [x / 1.0 for x in range(-360, -40)] + [x / 10 for x in range(-400, 1200)] + \
       [x / 1.0 for x in range(120, 361)]
dthdt = 6.0 * RPM
linhas, E, prev = [], 0.0, None
for th in angs:
    Q = Q_TOTAL * dxdth(th) * dthdt
    q = Q / vcil(th)
    if prev is not None:
        E += 0.5 * (Q + prev) * 0.1 / dthdt if -40 <= th < 120 else 0.5 * (Q + prev) * 1.0 / dthdt
    prev = Q
    linhas.append(f"({th + DESL:.1f} {q:.6e})")
open(sys.argv[1], "w").write("// q''' [W/m3] x (CA + 360); Q_wiebe/V_cilindro; gerado por gera_wiebe_q.py\n"
                              + "\n".join(linhas) + "\n")
print(f"energia ~ {E:.1f} J; V no PMS = {vcil(0)*1e6:.2f} cm3; q max = {max(Q_TOTAL*dxdth(t)*dthdt/vcil(t) for t in angs):.3e} W/m3")
