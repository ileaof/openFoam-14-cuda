# Benchmark: 3D lid-driven cavity (transient PISO)

Case: [`tutorials/GPU/cavity3D`](../../tutorials/GPU/cavity3D/), `icoFoam`, Re = 1000,
PISO with 2 correctors, `p` with `relTol 0.05` and `pFinal` with `relTol 0.001`.
4 MPI ranks, 2 × 2 × 1 decomposition. Time per step measured after 5 warm-up steps.

**Environment:** RTX 4050 Laptop (6 GB) · WSL2 Ubuntu 22.04 · CUDA 13.2 · GCC 11.4 · OpenMPI 4.1.

## Scaling curve (2026-10-11)

| Mesh | CPU (GAMG) | GPU (AMGX) | Speed-up | p iterations, CPU / GPU |
|---|---:|---:|---:|---:|
| 80³ = 0.5 M cells | 0.204 s/step | 0.197 s/step | 1.03× | 3.9 / 5.3 |
| 100³ = 1.0 M | 0.570 | 0.403 | **1.42×** | 7.8 / 5.7 |
| 125³ = 2.0 M | 1.283 | 0.834 | **1.54×** | 8.7 / 5.7 |
| 140³ = 2.7 M | 1.932 | 1.192 | **1.62×** | 9.8 / 5.5 |
| 150³ = 3.4 M | 3.110 | 1.485 | **2.09×** | 14.6 / 5.6 |

25 steps per run, averaged after 5 warm-up steps, with the machine idle (browser and other
programs closed, WSL restarted). The repeated 2.7 M run gave 1.932 / 1.192 s/step versus
1.928 / 1.194 in the first run. An earlier 2 M run with other programs open gave 1.454 s/step
on the CPU, 13% slower: load on the machine inflates the CPU time and, with it, the apparent
speed-up. The 4.9 M mesh was not measured: the 8 GB of WSL RAM run out while creating the AMGX
instances on the 4 ranks. Data in [`cavity3D_scaling.csv`](cavity3D_scaling.csv);
chart made with [`../scripts/plot_scaling.py`](../scripts/plot_scaling.py).

## CPU vs. GPU (2026-10-10)

| Mesh | CPU, GAMG | GPU, AMGX (`FGMRES_CLASSICAL_AGGRESSIVE_PMIS`) | Speed-up |
|---|---|---|---:|
| 100³ = 1,000,000 cells | 0.575 s/step · 7.4 p it. | 0.417 s/step · 5.5 p it. | **1.38×** |
| 150³ = 3,375,000 cells | 3.577 s/step · 15.6 p it. | 1.577 s/step · 5.6 p it. | **2.27×** |

With `PCG_CLASSICAL_V_JACOBI`, the 3.4 M mesh gives 1.560 s/step (2.29×). These first
measurements were taken with other programs running; the 2026-10-11 curve above supersedes them.

## AMGX recipes (1 M mesh, 2026-10-10)

| Recipe | s/step | p iterations |
|---|---:|---:|
| `FGMRES_CLASSICAL_AGGRESSIVE_PMIS` | **0.417** | 5.5 |
| `PCG_CLASSICAL_V_JACOBI` | 0.448 | 8.7 |
| `PCG_CLASSICAL_F_JACOBI` | 0.641 | 3.5 |
| `agg_cheb4` | 0.663 | 7.5 |
| `PCG_AGGREGATION_JACOBI` | 0.766 | 22.8 |
| `FGMRES_AGGREGATION_DILU` | 0.942 | 7.7 |
| `AMG_CLASSICAL_AGGRESSIVE_CHEB_L1_TRUNC` | 1.011 | 27.1 |
| `AGGREGATION_DILU` | 3.049 | 55.6 |
| `AGGREGATION_GS` | 5.114 | 72.6 |

All recipes use the same stopping criterion (`RELATIVE_INI`, equal to `relTol`) and
`"structure_reuse_levels": -1`, and reach the same final Courant number. The difference is
only cost. `PCG_AGGREGATION_JACOBI`, this repository's old default, takes 4× more iterations
than PMIS and makes the GPU **slower than the CPU** (0.766 vs. 0.575). That is why
[`cuda/config/amgxpOptions`](../config/amgxpOptions) now uses PMIS.

Sweep made with [`cuda/scripts/tune_amgx.py`](../scripts/tune_amgx.py).

## Long run

The same 1 M mesh with the PMIS recipe up to t = 1 s (2000 steps): 0.423 s/step,
6.0 p iterations on average.
