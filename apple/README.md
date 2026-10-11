# OpenFOAM-14 on Apple Silicon (planned)

> **Status: plan, not yet tested on Apple Silicon.** The steps below are the intended path;
> they will be validated and corrected when the test machine (M5, 64 GB) arrives.

## What changes compared with Linux/WSL with NVIDIA

| Part | Apple Silicon |
|---|---|
| OpenFOAM-14 on the CPU | runs, built in an ARM Linux VM (aarch64) |
| Pressure on the GPU (AMGX, [`cuda/`](../cuda/) folder) | **does not run**: it needs CUDA, which only exists on NVIDIA cards |
| [`tutorials/GPU`](../tutorials/GPU/) tutorials | skipped automatically (no `libamgxFoam.so`) |
| ParaView | native macOS build |

## Intended path

1. **ARM Linux VM.** Ubuntu 22.04 arm64 in a light VM (OrbStack, Lima or UTM). x86 images
   through Docker also work, but emulated by Rosetta, much slower.
2. **Dependencies in the VM**, the same as on x86 Ubuntu:
   ```bash
   sudo apt install build-essential flex bison cmake zlib1g-dev libboost-system-dev \
       libboost-thread-dev libopenmpi-dev openmpi-bin libscotch-dev libptscotch-dev
   ```
3. **Build the fork** as on Linux (sections 2 and 3 of the [main README](../README.md)),
   without the GPU step.
4. **Validate** with cavity, motorBike and smallPoolFire3D, comparing with the x86 results.

## To do when the machine arrives

- [ ] Check whether there are ready-made OpenFOAM packages for arm64 or building is the way
- [ ] Build the fork on aarch64 and run the tutorial loop
- [ ] `apple/scripts/setup_vm.sh`: create the VM and install dependencies (only once tested)
- [ ] CPU benchmark: cavity3D, motorBike, smallPoolFire3D with 4, 8 and all performance
      cores, compared with the laptop (CPU and RTX 4050)
- [ ] Find out whether there is a viable path for the pressure solver on Apple's GPU (Metal);
      today there is no mature equivalent to AMGX
