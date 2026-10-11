# Benchmark: cavity 3D com tampa móvel (PISO transiente)

Caso: [`tutorials/GPU/cavity3D`](../../tutorials/GPU/cavity3D/), `icoFoam`, Re = 1000,
PISO com 2 correctores, `p` com `relTol 0.05` e `pFinal` com `relTol 0.001`.
4 processos MPI, decomposição 2 × 2 × 1. Tempo por passo medido depois de 5 passos
de aquecimento (30 passos na malha de 1 M, 20 na de 3,4 M).

**Ambiente:** RTX 4050 Laptop (6 GB) · WSL2 Ubuntu 22.04 · CUDA 13.2 · GCC 11.4 · OpenMPI 4.1.

## CPU × GPU

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
