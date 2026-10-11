# Tutorials with the pressure on the GPU

Ready-to-run cases with the `amgx` solver (NVIDIA AMGX, through `libamgxFoam.so`).
Only cases where we **measured a gain** of the GPU over the CPU in this tree are included;
the numbers are in [`cuda/benchmarks/`](../../cuda/benchmarks/).

First build the GPU part ([`cuda/README.md`](../../cuda/README.md)) and, in every new
terminal:

```bash
source ~/dev/OpenFOAM-14/cuda/scripts/env.sh
```

| Case | Solver | Mesh | Measured speed-up (GPU vs. CPU, 4 ranks) |
|---|---|---|---|
| [`cavity3D`](cavity3D/) | `icoFoam`, transient PISO | 80³ = 0.5 M cells | 1.03× (tie) |
| | | 100³ = 1 M cells | 1.42× (0.403 vs. 0.570 s/step) |
| | | 125³ = 2 M cells | 1.54× (0.834 vs. 1.283 s/step) |
| | | 140³ = 2.7 M cells | 1.62× (1.192 vs. 1.932 s/step) |
| | | 150³ = 3.4 M cells | 2.09× (1.485 vs. 3.110 s/step) |

```bash
cd tutorials/GPU/cavity3D
./Allrun gpu            # pressure on the GPU
./Allrun cpu            # the same with GAMG, for comparison
N=150 ./Allrun gpu      # bigger mesh: this is where the GPU stands out
```

`./Allrun` in this folder runs every case in `gpu` mode. Without `libamgxFoam.so`
it does nothing, so it does not break the OpenFOAM tutorial loop on machines
without a GPU.

## Why other cases are not here

The GPU only speeds up the pressure solve. If the pressure is a small part of the step,
the overall gain vanishes (Amdahl's law), even with the GPU working well.

| Case | What we measured |
|---|---|
| `incompressibleFluid/motorBike` (3.2 M cells, SIMPLE) | tie: 2.48 vs. 2.55 s/iteration; the pressure is ~10% of the iteration |
| `multicomponentFluid/smallPoolFire3D` (216 k cells) | on the CPU, 0.28 s/step with only 3.7 GAMG iterations per `p_rgh` solve; the time goes to radiation (`fvDOM`) and chemistry |

Rule of thumb: in the CPU log, if `GAMG` takes only 1 to 3 iterations per pressure
solve, the GPU has little to gain. If the iterations grow with the mesh, as on the
cavity3D (3.9 → 14.6 from 0.5 M to 3.4 M cells, while AMGX stays at ~5.5), that is
where it pays off.

## Tune the AMGX recipe to your case

The configuration makes a big difference. On the cavity3D with 1 M cells (2026-10-10):

| AMGX recipe | s/step | p iterations |
|---|---:|---:|
| `FGMRES_CLASSICAL_AGGRESSIVE_PMIS` (this repository's default) | **0.417** | 5.5 |
| `PCG_CLASSICAL_V_JACOBI` | 0.448 | 8.7 |
| `PCG_CLASSICAL_F_JACOBI` | 0.641 | 3.5 |
| `agg_cheb4` | 0.663 | 7.5 |
| `PCG_AGGREGATION_JACOBI` (old default) | 0.766 | 22.8 |
| `FGMRES_AGGREGATION_DILU` | 0.942 | 7.7 |

To compare recipes on your own case (already decomposed, with a short `endTime`):

```bash
python3 cuda/scripts/tune_amgx.py --case <case> --solver foamRun --np 4 \
    --dict p=0.05 --dict pFinal=0.001       # use each dictionary's relTol
```
