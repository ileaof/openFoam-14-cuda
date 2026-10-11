#!/bin/bash
# Environment to build and run the "amgx" (GPU) pressure solver in OpenFOAM-14.
# Usage:  source cuda/scripts/env.sh      (from the OpenFOAM-14 root)
#
# CUDA_DEPS_DIR: where AMGX, foam2csr and amgx4foam live (default: ~/dev)

_cuda_here="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
_foam_root="$(cd "$_cuda_here/.." && pwd)"
export CUDA_DEPS_DIR="${CUDA_DEPS_DIR:-$HOME/dev}"

# OpenFOAM-14 (GCC). For Intel: source "$_foam_root/etc/bashrc" WM_COMPILER=Icx
source "$_foam_root/etc/bashrc"

# CUDA first in the PATH (avoids the old nvcc from Ubuntu's nvidia-cuda-toolkit package)
export PATH=/usr/local/cuda/bin:$PATH

# AMGX
export AMGX_INC=$CUDA_DEPS_DIR/AMGX/include
export AMGX_LIB=$CUDA_DEPS_DIR/AMGX/build

# foam2csr needs CUB. In CUDA 13 it lives in include/cccl/; in older versions, in include/
if [ -d /usr/local/cuda/targets/x86_64-linux/include/cccl/cub ]; then
  export CUBROOT=/usr/local/cuda/targets/x86_64-linux/include/cccl
else
  export CUBROOT=/usr/local/cuda/include
fi
export FOAM2CSR_INC=$CUDA_DEPS_DIR/foam2csr/src
export FOAM2CSR_LIB=$FOAM_USER_LIBBIN

# Ubuntu 22.04's PETSc (libpetsc-real-dev). Adjust if your distro installs it elsewhere.
export PETSC_INC=/usr/lib/petscdir/petsc3.15/x86_64-linux-gnu-real/include
export PETSC_LIB_DIR=$CUDA_DEPS_DIR/compat/lib

# Trilinos' Zoltan (optional OpenFOAM decomposition)
export ZOLTAN_INCLUDE_DIR=/usr/include/trilinos
export ZOLTAN_LIB_DIR=$CUDA_DEPS_DIR/compat/lib

export LD_LIBRARY_PATH=$AMGX_LIB:$CUDA_DEPS_DIR/compat/lib:/usr/local/cuda/lib64:$LD_LIBRARY_PATH

unset _cuda_here _foam_root
