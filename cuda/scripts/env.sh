#!/bin/bash
# Ambiente para compilar e rodar o solver de pressão "amgx" (GPU) no OpenFOAM-14.
# Uso:  source cuda/scripts/env.sh        (a partir da raiz do OpenFOAM-14)
#
# CUDA_DEPS_DIR: onde ficam AMGX, foam2csr e amgx4foam (padrão: ~/dev)

_cuda_here="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
_foam_root="$(cd "$_cuda_here/.." && pwd)"
export CUDA_DEPS_DIR="${CUDA_DEPS_DIR:-$HOME/dev}"

# OpenFOAM-14 (GCC). Para Intel: source "$_foam_root/etc/bashrc" WM_COMPILER=Icx
source "$_foam_root/etc/bashrc"

# CUDA na frente do PATH (evita o nvcc antigo do pacote nvidia-cuda-toolkit do Ubuntu)
export PATH=/usr/local/cuda/bin:$PATH

# AMGX
export AMGX_INC=$CUDA_DEPS_DIR/AMGX/include
export AMGX_LIB=$CUDA_DEPS_DIR/AMGX/build

# foam2csr precisa do CUB. No CUDA 13 ele fica em include/cccl/; em versões anteriores, em include/
if [ -d /usr/local/cuda/targets/x86_64-linux/include/cccl/cub ]; then
  export CUBROOT=/usr/local/cuda/targets/x86_64-linux/include/cccl
else
  export CUBROOT=/usr/local/cuda/include
fi
export FOAM2CSR_INC=$CUDA_DEPS_DIR/foam2csr/src
export FOAM2CSR_LIB=$FOAM_USER_LIBBIN

# PETSc do Ubuntu 22.04 (libpetsc-real-dev). Ajuste se a sua distro instalar em outro lugar.
export PETSC_INC=/usr/lib/petscdir/petsc3.15/x86_64-linux-gnu-real/include
export PETSC_LIB_DIR=$CUDA_DEPS_DIR/compat/lib

# Zoltan do Trilinos (decomposição opcional do OpenFOAM)
export ZOLTAN_INCLUDE_DIR=/usr/include/trilinos
export ZOLTAN_LIB_DIR=$CUDA_DEPS_DIR/compat/lib

export LD_LIBRARY_PATH=$AMGX_LIB:$CUDA_DEPS_DIR/compat/lib:/usr/local/cuda/lib64:$LD_LIBRARY_PATH

unset _cuda_here _foam_root
