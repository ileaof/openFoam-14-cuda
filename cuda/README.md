# GPU pressure solver (AMGX) for OpenFOAM-14

This folder couples NVIDIA's [AMGX](https://github.com/NVIDIA/AMGX) to OpenFOAM-14
as an `lduMatrix::solver` called `amgx`, selected in `fvSolution`.
**No OpenFOAM Foundation file is changed**: every change lives in two third-party
projects and is applied as patches.

```
OpenFOAM-14  →  amgx4foam (libamgxFoam.so)  →  foam2csr (libfoam2csr.so)  →  AMGX (libamgxsh.so, GPU)
```

| Folder | Contents |
|---|---|
| `patches/` | fixes so foam2csr and amgx4foam build and run with OpenFOAM-14 and CUDA 13 (to apply them by hand, or to remake them for new versions, see the [main README](../README.md#applying-the-patches-by-hand)) |
| `scripts/env.sh` | environment variables (source it before building or running) |
| `scripts/build_all.sh` | clones the three dependencies at the tested commits, applies the patches and builds |
| `config/amgxpOptions` | recommended AMGX configuration (FGMRES + classical AMG, PMIS) |
| `scripts/tune_amgx.py` | compares AMGX recipes on your own case and reports the fastest |
| `scripts/render_*.py`, `scripts/plot_scaling.py` | the README figures (ParaView) and the scaling chart |
| `benchmarks/` | measured results: [cavity3D](benchmarks/cavity3D.md) (PISO, 0.5 to 3.4 M cells) and [motorBike](benchmarks/motorBike.md) (SIMPLE, 3.2 M) |
| [`../tutorials/GPU/`](../tutorials/GPU/) | ready-to-run cases where the GPU beats the CPU (`./Allrun gpu`) |
| `docs/` | step-by-step tutorial and technical report in HTML (download and open in a browser) |

## Quick start

Requirements: NVIDIA GPU with compute capability ≥ 7.0, WSL2 or Linux with Ubuntu 22.04,
CUDA Toolkit in `/usr/local/cuda` (tested with 13.2), OpenFOAM-14 already built in this tree and
the packages `libpetsc-real-dev`, `libtrilinos-zoltan-dev`, `libscotch-dev`, `libptscotch-dev`.

```bash
cd ~/dev/OpenFOAM-14
nvidia-smi --query-gpu=compute_cap --format=csv   # e.g. 8.9
bash cuda/scripts/build_all.sh 89                 # 8.9 -> 89
```

In a case, three files:

```
system/controlDict   libs ("libamgxFoam.so");
system/fvSolution    p { solver amgx; amgx { dict p; } }
system/amgxpOptions  copy from cuda/config/amgxpOptions
```

Always run decomposed and in parallel (AMGX needs MPI to be initialized):

```bash
source cuda/scripts/env.sh
decomposePar && mpirun -np 4 foamRun -parallel     # look for "AMGx:  Solving for p" lines
```

## Before concluding that the GPU is not worth it

1. **The `tolerance`/`relTol` in `fvSolution` is ignored.** What counts is `"tolerance"` in `amgxpOptions` (`RELATIVE_INI`). Set it to the case's `relTol`, or the GPU will do much more work than the CPU.
2. **Do not use `caching { update periodic | adaptive | never; }`.** In these modes amgx4foam stops updating the matrix, and the result is physically wrong even though it converges. To save setup time use `"structure_reuse_levels": -1`, which is already in `config/amgxpOptions`.
3. **Small meshes favor the CPU.** Use the cavity only to validate the result, not to measure speed.
   On the [cavity3D](benchmarks/cavity3D.md) the speed-up goes from 1.03× at 0.5 M cells to 2.09× at 3.4 M.
4. **2 to 4 ranks per GPU.** Each rank opens a CUDA context on the same card, and also takes host RAM.
5. **Free the GPU.** ParaView, games and the desktop itself compete for the card's memory; running out shows up as `Cuda failure: 'unknown error'` / `Out of resource`.
6. **In steady state (SIMPLE) the pressure is often only ~10% of the iteration.** The gain shows up in transient cases where the pressure dominates. See `benchmarks/motorBike.md`.
7. **The AMGX recipe matters.** On the cavity3D, the old `PCG_AGGREGATION_JACOBI` takes 4× more iterations than `FGMRES_CLASSICAL_AGGRESSIVE_PMIS` and makes the GPU slower than the CPU. Compare on your own case with `scripts/tune_amgx.py`.

---
Community fork, not official. OpenFOAM® is a registered trademark of the OpenFOAM Foundation.
AMGX (BSD-3), foam2csr and amgx4foam belong to their authors; this repository
only distributes patches on top of them.
