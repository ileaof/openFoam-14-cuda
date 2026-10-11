# Benchmark: motorBike, CPU vs. GPU

Measured on 2026-10-10 on an RTX 4050 Laptop (6 GB, sm_89), WSL2 Ubuntu 22.04,
CUDA 13.2, OpenFOAM-14 built with GCC 11.4.

## Case

- Tutorial `incompressibleFluid/motorBike`, `snappyHexMesh` mesh: **3,215,800 cells**
- `foamRun` with `incompressibleFluid` (SIMPLE, steady state)
- 4 MPI ranks, `hierarchical (2 2 1)` decomposition
- Average time per iteration between iterations 10 and 100 (excludes mesh reading and the first setup)

## Result

| Configuration | s / iteration | p solver iterations | Cd (it. 100) |
|---|---|---|---|
| GPU, JSON tolerance (1e-6), 8 ranks¹ | 3.7 | 41 | — |
| CPU, GAMG (`relTol 0.1`) | 2.550 | 2.0 | 0.7210 |
| GPU, AMGX `tolerance 0.1` | 2.522 | 1.4 | 0.7214 |
| GPU, AMGX `tolerance 0.1` + `structure_reuse_levels -1` | **2.478** | 1.4 | 0.7200 |

¹ First attempt, before finding out that amgx4Foam ignores the `tolerance`/`relTol` in `fvSolution`.

## Reading

- With the stopping criterion matched, the GPU **ties** with the CPU and the physical result is the same.
- The AMGX pressure solve takes **0.26 s** of each 2.48 s iteration, about **10%**. The rest (velocity, turbulence, matrix assembly, post-processing) runs on the CPU. By Amdahl's law, the most one can gain by speeding up only the pressure is ~12%.
- Reusing the AMG structure cut the setup from 0.49 s to 0.15 s per solve.
- The GPU should pay off when the pressure dominates the iteration: transient flows (PISO/PIMPLE) with several correctors and `pFinal relTol 0`, on large meshes. That is what [cavity3D.md](cavity3D.md) shows.

## Reproduce

```bash
source cuda/scripts/env.sh
cp -r $FOAM_TUTORIALS/incompressibleFluid/motorBike/motorBike ~/runs/mb
# follow the tutorial's Allrun up to potentialFoam, with 4 subdomains
# GPU: copy cuda/config/amgxpOptions to system/ and switch the p solver (see cuda/README.md)
mpirun -np 4 foamRun -parallel
```
