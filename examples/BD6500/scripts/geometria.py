#!/usr/bin/env python3
"""Geometria 3D do Branco BD-6500 (86 x 70 mm) com 2 valvulas verticais, para o snappyHexMesh.

  python geometria.py <angulo_CA> <pasta_saida>   -> fluido.stl (regioes nomeadas) + info.txt
  python geometria.py --tabela                    -> posicao do pistao e lifts no ciclo

Convencao: 0 grau = PMS da combustao; ciclo de -360 (PMS da troca de gases) a +360.
Eixos: z para cima (cabecote plano em z = 0, pistao abaixo); admissao em x < 0, escape em x > 0.
Unidades: metros. Valores (confirmados pelo usuario em 14/10/2026; * = estimado):
  FA 128 antes do PMS, AE 123 depois do PMS (ficha do motor); AA 16 antes e FE 16 depois do PMS de troca*;
  lift max 7,5 mm*; pratos 38 mm (adm.) e 32 mm (esc.)*; Rc 15,14 (ajuste wiebepy), pistao e cabecote planos.
Valvula: prato com sede conica de 45 graus no cabecote; fechada fica parada em LIFT_MIN (como no mover),
com um anel de selo rente ao cabecote vedando a fresta. Lift h abre uma fresta de h*sin(45).
Os nomes das superficies vem do manifold3d (id de origem de cada triangulo), nao de testes geometricos.
"""
import math, os, sys
import numpy as np
from manifold3d import Manifold

# ------------------------------------------------------------------ dados do motor
B, S, L = 0.086, 0.070, 0.1175           # diametro, curso, biela
R_CIL = B / 2
VD = math.pi * R_CIL**2 * S
RC = 15.1365
VC = VD / (RC - 1)
AA, FA = -360 - 16, -128                 # admissao: abre / fecha  [graus]
AE, FE = 123, 360 + 16                   # escape:   abre / fecha
LIFT_MAX = 0.0075
VAL = {  # nome: (x do centro, raio do prato, raio do duto, abre, fecha)
    "iv": (-0.0200, 0.0190, 0.0160, AA, FA),
    "ev": (+0.0220, 0.0160, 0.0135, AE, FE),
}
H_DISCO = 0.0           # prato so conico (rente ao cabecote quando fechado)
R_HASTE = 0.0035
L_DUTO = 0.050
SEG = 96
LIFT_MIN = 1.5e-3          # abaixo disso a valvula e considerada fechada (minLift do mover); versao leve
Z_SELO = 0.6e-3            # valvula fechada: fica em LIFT_MIN (onde o mover a para) e um anel de selo
                           # de 0,6 mm junto a borda da sede veda a fresta (o anel faz parte da sede)

# Altura livre no PMS: com as valvulas fechadas (em LIFT_MIN) os pratos entram LIFT_MIN abaixo do
# cabecote; compensa esse volume para manter Vc (e Rc = 15,14).
V_PRATOS = sum(math.pi * LIFT_MIN / 3 * (rv**2 + rv * (rv - LIFT_MIN) + (rv - LIFT_MIN)**2)
               for (_, rv, _, _, _) in VAL.values())
H_PMS = (VC + V_PRATOS) / (math.pi * R_CIL**2)


def pistao_z(theta):
    """Cota do topo do pistao [m] (negativa); theta em graus, 0 = PMS."""
    t = math.radians(theta)
    r = S / 2
    x = r * math.cos(t) + math.sqrt(L**2 - (r * math.sin(t))**2)
    return -(H_PMS + (r + L - x))


PERFIL = "sen"   # "sen": tempos da ficha no limiar LIFT_MIN (versao 2); "cos": perfil 1-cos original
RAMPA = 16.0     # graus entre o lift zero e o limiar LIFT_MIN, em cada lado


def _p_sen(nome):
    """Expoente p de L*sin(pi f)^p para que o lift passe por LIFT_MIN nos tempos da ficha."""
    _, _, _, a, f = VAL[nome]
    D = (f - a) + 2 * RAMPA
    ft = RAMPA / D
    return math.log(LIFT_MIN / LIFT_MAX) / math.log(math.sin(math.pi * ft))


def lift(nome, theta):
    """Levantamento [m] (periodo 720).
    'sen': L*sin(pi f)^p de (abre - RAMPA) a (fecha + RAMPA): a valvula passa por LIFT_MIN (o limiar
           'aberta/fechada' do mover) exatamente nos tempos da ficha (FA -128, AE 123), entao a janela
           fechada efetiva da simulacao e a do motor.
    'cos': perfil 1 - cos entre abre e fecha (1a versao; a janela efetiva ficava 36-39 graus maior)."""
    _, _, _, a, f = VAL[nome]
    if PERFIL == "sen":
        a0, a1 = a - RAMPA, f + RAMPA
        p = _p_sen(nome)
        for k in (-720, 0, 720):
            if a0 <= theta + k <= a1:
                fase = (theta + k - a0) / (a1 - a0)
                return LIFT_MAX * max(math.sin(math.pi * fase), 0.0) ** p
        return 0.0
    for k in (-720, 0, 720):
        if a <= theta + k <= f:
            fase = (theta + k - a) / (f - a)
            return LIFT_MAX * 0.5 * (1 - math.cos(2 * math.pi * fase))
    return 0.0


def cil(r0, z0, z1, x=0.0, r1=None):
    """Cilindro (ou tronco de cone, se r1) de z0 a z1 centrado em (x, 0)."""
    m = Manifold.cylinder(z1 - z0, r0, r0 if r1 is None else r1, SEG)
    return m.translate((x, 0.0, z0))


def fluido(theta):
    zp = pistao_z(theta)
    rotulos = {}                  # id de origem -> nome base

    def marca(m, nome):
        m = m.as_original()
        rotulos[m.original_id()] = nome
        return m

    sol = marca(cil(R_CIL, zp, 0.0), "cilindro")
    lifts = {}
    for nome, (x, rv, rd, a, f) in VAL.items():
        porta = "intakePort" if nome == "iv" else "exhaustPort"
        sede = marca(cil(rv, -1e-4, rv - rd, x, r1=rd), nome + "Seat")  # cone 45 graus: rv em z=0 -> rd em z=rv-rd
        duto = marca(cil(rd, rv - rd - 1e-4, L_DUTO, x), porta)
        sol = sol + sede + duto
    for nome, (x, rv, rd, a, f) in VAL.items():
        h = lift(nome, theta)
        fechada = h < LIFT_MIN
        h = max(h, LIFT_MIN)                     # fechada: parada em LIFT_MIN, como no mover
        lifts[nome] = 0.0 if fechada else h
        zb = -h                                                         # base do cone do prato
        prato = marca(cil(rv, zb, zb + (rv - rd), x, r1=rd), nome + "Head")
        haste = marca(cil(R_HASTE, zb + (rv - rd) - 1e-4, L_DUTO + 0.01, x), nome + "Stem")
        sol = sol - prato - haste
        if fechada:
            # selo: preenche a fresta inteira entre o cone da sede (r = rv - z) e o do prato
            # (r = rv - h - z), de z = 0 ate o topo do cone do prato (zs = rv - rd - h).
            # Um anel fino (0,6 mm, < 2 celulas) deixava ilhas de faces da valvula que quebravam o
            # mapeamento entre malhas. Sobrepoe 0,1 mm nos lados para nao haver faces coincidentes.
            # v2: o selo comeca em z = 0 (rente ao cabecote) e sobrepoe 0,5 mm so para dentro do metal;
            # antes ele comecava em z = -0,1 mm e deixava um degrau de 0,1 x 0,1 mm em volta da sede,
            # onde o snap criava "ilhas" de faces do cabecote que quebravam o mapeamento entre malhas.
            # Por dentro, o tronco de cone so cobre o volume da valvula, que ja foi subtraido.
            zs = (rv - rd) - h
            sol = sol - marca(cil(rv + 5e-4, 0.0, zs, x, r1=rv - zs + 5e-4), nome + "Seat")
    return sol, zp, lifts, rotulos


def nomeia(mesh, rotulos, zp):
    """Nome de cada triangulo a partir do id de origem; separa as faces do cilindro e dos dutos."""
    v = np.asarray(mesh.vert_properties)[:, :3]
    tri = np.asarray(mesh.tri_verts)
    run_idx = np.asarray(mesh.run_index)
    run_id = np.asarray(mesh.run_original_id)
    origem = np.empty(len(tri), dtype=np.int64)
    for k in range(len(run_id)):
        origem[run_idx[k] // 3: run_idx[k + 1] // 3] = run_id[k]
    p = v[tri]
    c = p.mean(axis=1)
    n = np.cross(p[:, 1] - p[:, 0], p[:, 2] - p[:, 0])
    n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-300
    nomes = []
    for o, ci, ni in zip(origem, c, n):
        base = rotulos.get(int(o), "head")
        if base == "cilindro":
            if ni[2] < -0.9:
                base = "piston"
            elif ni[2] > 0.9:
                base = "head"
            else:
                base = "liner"
        elif base in ("intakePort", "exhaustPort") and ni[2] > 0.9 and ci[2] > L_DUTO - 1e-4:
            base = "inlet" if base == "intakePort" else "outlet"
        nomes.append(base)
    return v, tri, np.array(nomes), n


def escreve(theta, pasta):
    sol, zp, lifts, rotulos = fluido(theta)
    mesh = sol.to_mesh()
    v, tri, nomes, n = nomeia(mesh, rotulos, zp)
    os.makedirs(pasta, exist_ok=True)
    with open(os.path.join(pasta, "fluido.stl"), "w") as f:
        for reg in sorted(set(nomes)):
            f.write(f"solid {reg}\n")
            for t, nn in zip(tri[nomes == reg], n[nomes == reg]):
                f.write(f" facet normal {nn[0]:.6e} {nn[1]:.6e} {nn[2]:.6e}\n  outer loop\n")
                for q in v[t]:
                    f.write(f"   vertex {q[0]:.7f} {q[1]:.7f} {q[2]:.7f}\n")
                f.write("  endloop\n endfacet\n")
            f.write(f"endsolid {reg}\n")
    partes = sol.decompose()
    vol = sol.volume()
    cont = {r: int((nomes == r).sum()) for r in sorted(set(nomes))}
    info = (f"theta {theta}\npistao_z {zp:.7f}\nlift_iv {lifts['iv']:.7f}\nlift_ev {lifts['ev']:.7f}\n"
            f"volume_fluido_cm3 {vol*1e6:.4f}\ncorpos {len(partes)}\n"
            f"volumes_corpos_cm3 {[round(p.volume()*1e6, 3) for p in partes]}\nregioes {cont}\n")
    open(os.path.join(pasta, "info.txt"), "w").write(info)
    return info


if __name__ == "__main__":
    if sys.argv[1] == "--tabela":
        print(f"H_PMS = {H_PMS*1000:.2f} mm, Vd = {VD*1e6:.1f} cm3, Vc = {VC*1e6:.2f} cm3, Rc = {RC}")
        for th in range(-360, 361, 20):
            print(f"{th:5d}  pistao {pistao_z(th)*1000:7.2f} mm  iv {lift('iv', th)*1000:5.2f}  ev {lift('ev', th)*1000:5.2f} mm")
        sys.exit()
    print(escreve(float(sys.argv[1]), sys.argv[2]))
