# Benchmark: cavity 3D com tampa móvel (PISO transiente)

Caso: [`tutorials/GPU/cavity3D`](../../tutorials/GPU/cavity3D/), `icoFoam`, Re = 1000,
PISO com 2 correctores, `p` com `relTol 0.05` e `pFinal` com `relTol 0.001`.
4 processos MPI, decomposição 2 × 2 × 1. Tempo por passo medido depois de 5 passos
de aquecimento (30 passos na malha de 1 M, 20 na de 3,4 M).

**Ambiente:** RTX 4050 Laptop (6 GB) · WSL2 Ubuntu 22.04 · CUDA 13.2 · GCC 11.4 · OpenMPI 4.1.

## Curva de escala (11/10/2026)

| Malha | CPU (GAMG) | GPU (AMGX) | Ganho | Iterações de p, CPU / GPU |
|---|---:|---:|---:|---:|
| 80³ = 0,5 M células | 0,208 s/passo | 0,201 s/passo | 1,03× | 3,9 / 5,3 |
| 100³ = 1,0 M | 0,583 | 0,411 | **1,42×** | 7,8 / 5,7 |
| 125³ = 2,0 M | 1,454 | 0,852 | **1,71×** | 8,7 / 5,7 |
| 150³ = 3,4 M | 3,577 | 1,577 | **2,27×** | 15,6 / 5,6 |

0,5, 1 e 2 M medidos em 11/10/2026 (25 passos, média após 5 de aquecimento); 3,4 M medido
em 10/10/2026 com o mesmo caso, a mesma receita e o mesmo critério. Na repetição de 3,4 M
em 11/10 a CPU deu 3,349 s/passo, mas a GPU não completou: o Linux matou os processos por
falta de RAM (8 GB no WSL) ao criar a segunda instância da AMGX (`pFinal`). Pela mesma
razão a malha de 4,9 M não foi medida. Dados em [`cavity3D_scaling.csv`](cavity3D_scaling.csv);
gráfico gerado com [`../scripts/plot_scaling.py`](../scripts/plot_scaling.py).

## CPU × GPU (10/10/2026)

| Malha | CPU, GAMG | GPU, AMGX (`FGMRES_CLASSICAL_AGGRESSIVE_PMIS`) | Ganho |
|---|---|---|---:|
| 100³ = 1.000.000 células | 0,575 s/passo · 7,4 it. de p | 0,417 s/passo · 5,5 it. de p | **1,38×** |
| 150³ = 3.375.000 células | 3,577 s/passo · 15,6 it. de p | 1,577 s/passo · 5,6 it. de p | **2,27×** |

Com `PCG_CLASSICAL_V_JACOBI`, a malha de 3,4 M dá 1,560 s/passo (2,29×).

O ganho cresce com a malha porque as iterações do GAMG crescem (7,4 → 15,6),
enquanto as da AMGX ficam constantes (~5,5).

## Receitas da AMGX (malha de 1 M)

| Receita | s/passo | Iterações de p |
|---|---:|---:|
| `FGMRES_CLASSICAL_AGGRESSIVE_PMIS` | **0,417** | 5,5 |
| `PCG_CLASSICAL_V_JACOBI` | 0,448 | 8,7 |
| `PCG_CLASSICAL_F_JACOBI` | 0,641 | 3,5 |
| `agg_cheb4` | 0,663 | 7,5 |
| `PCG_AGGREGATION_JACOBI` | 0,766 | 22,8 |
| `FGMRES_AGGREGATION_DILU` | 0,942 | 7,7 |
| `AMG_CLASSICAL_AGGRESSIVE_CHEB_L1_TRUNC` | 1,011 | 27,1 |
| `AGGREGATION_DILU` | 3,049 | 55,6 |
| `AGGREGATION_GS` | 5,114 | 72,6 |

Todas as receitas usam o mesmo critério de parada (`RELATIVE_INI`, igual ao `relTol`)
e `"structure_reuse_levels": -1`, e chegam ao mesmo número de Courant no fim.
A diferença é só de custo. O `PCG_AGGREGATION_JACOBI`, padrão antigo deste repositório,
faz 4× mais iterações que o PMIS e deixa a GPU **mais lenta que a CPU** (0,766 × 0,575).
Por isso o [`cuda/config/amgxpOptions`](../config/amgxpOptions) passou a usar o PMIS.

Varredura gerada com [`cuda/scripts/tune_amgx.py`](../scripts/tune_amgx.py).

## Rodada longa

A mesma malha de 1 M com a receita PMIS até t = 1 s (2000 passos): 0,423 s/passo,
6,0 iterações de p em média.
