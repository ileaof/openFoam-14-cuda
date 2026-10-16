#!/usr/bin/env python3
"""Tabelas de lift (grau a grau, -360..360) para o dynamicMeshDict, com a mesma funcao da geometria.
   python gera_tabelas.py <pasta constant do caso>   -> ivLift, evLift
Cada arquivo tem so os pares (angulo lift), para ser incluido dentro de 'values ( ... )'."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import geometria as g

pasta = sys.argv[1]
DESL = float(sys.argv[2]) if len(sys.argv) > 2 else 360.0   # tempo do caso = CA + DESL (meshToMesh nao aceita tempos negativos)
for nome in ("iv", "ev"):
    with open(os.path.join(pasta, nome + "Lift"), "w") as f:
        f.write(f"// lift da valvula {nome} [m] x angulo [graus]; gerado por gera_tabelas.py\n")
        for th in range(-360, 361):
            f.write(f"({th + DESL:g} {g.lift(nome, th):.8f})\n")
print("ok tabelas em", pasta)
