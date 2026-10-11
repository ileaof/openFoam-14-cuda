# Benchmark: cavity 3D com tampa móvel (PISO transiente)

Caso: [`tutorials/GPU/cavity3D`](../../tutorials/GPU/cavity3D/), `icoFoam`, Re = 1000,
PISO com 2 correctores, `p` com `relTol 0.05` e `pFinal` com `relTol 0.001`.
4 processos MPI, decomposição 2 × 2 × 1. Tempo por passo medido depois de 5 passos
de aquecimento (30 passos na malha de 1 M, 20 na de 3,4 M).

**Ambiente:** RTX 4050 Laptop (6 GB) · WSL2 Ubuntu 22.04 · CUDA 13.2 · GCC 11.4 · OpenMPI 4.1.

## Curva de escala (11/10/2026)

| Malha | CPU (GAMG) | GPU (AMGX) | Ganho | Iterações de p, CPU / GPU |
|---|---:|---:|---:|---:|
| 80³ = 0,5 M células | 0,204 s/passo | 0,197 s/passo | 1,03× | 3,9 / 5,3 |
| 100³ = 1,0 M | 0,570 | 0,403 | **1,42×** | 7,8 / 5,7 |
| 125³ = 2,0 M | 1,283 | 0,834 | **1,54×** | 8,7 / 5,7 |
| 140³ = 2,7 M | 1,932 | 1,192 | **1,62×** | 9,8 / 5,5 |
| 150³ = 3,4 M | 3,110 | 1,485 | **2,09×** | 14,6 / 5,6 |

25 passos por rodada, média depois de 5 de aquecimento, com a máquina livre (navegador e
outros programas fechados, WSL reiniciado). A 2,7 M repetida deu 1,932 / 1,192 s/passo
contra 1,928 / 1,194 na primeira rodada. Uma rodada anterior de 2 M com outros programas
abertos deu 1,454 s/passo na CPU, 13% mais lenta: carga na máquina infla o tempo da CPU e,
com ele, o ganho aparente. A malha de 4,9 M não foi medida: os 8 GB de RAM do WSL acabam ao
criar as instâncias da AMGX nos 4 processos. Dados em [`cavity3D_scaling.csv`](cavity3D_scaling.csv);
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
