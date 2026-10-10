#!/bin/bash
# Clona AMGX, foam2csr e amgx4foam nos commits testados, aplica os patches
# deste repositório e compila tudo.
#
# Uso (a partir da raiz do OpenFOAM-14, já compilado):
#   bash cuda/scripts/build_all.sh 89
# O argumento é o compute capability da GPU sem o ponto
# (nvidia-smi --query-gpu=compute_cap --format=csv): 8.9 -> 89, 8.6 -> 86, 7.5 -> 75.
set -euo pipefail

ARCH="${1:?informe o compute capability sem ponto, ex.: 89}"
HERE="$(cd "$(dirname "$0")/.." && pwd)"
source "$HERE/scripts/env.sh"
mkdir -p "$CUDA_DEPS_DIR"

AMGX_COMMIT=91a8413ef267b1c32aff4014c02820e1c5897ac2
FOAM2CSR_COMMIT=eb21649ed8b10d438d047485c0dd62cce33d269f
AMGX4FOAM_COMMIT=52dee12055c10d25a37e76291485b8aeb1cd42cf

clone_at () {
  local url=$1 dir=$2 commit=$3
  [ -d "$dir/.git" ] || git clone "$url" "$dir"
  git -C "$dir" checkout -q "$commit"
  git -C "$dir" submodule update -q --init --recursive
}

apply_patch () {
  local dir=$1 patch=$2
  if git -C "$dir" apply --reverse --check "$patch" 2>/dev/null; then
    echo "  patch já aplicado: $(basename "$patch")"
  else
    git -C "$dir" apply "$patch"
    echo "  patch aplicado: $(basename "$patch")"
  fi
}

echo "== 1/4 AMGX (sm_$ARCH)"
clone_at https://github.com/NVIDIA/AMGX.git "$CUDA_DEPS_DIR/AMGX" $AMGX_COMMIT
mkdir -p "$CUDA_DEPS_DIR/AMGX/build"
( cd "$CUDA_DEPS_DIR/AMGX/build"
  cmake -DCMAKE_CUDA_COMPILER=/usr/local/cuda/bin/nvcc \
        -DCMAKE_CUDA_ARCHITECTURES="$ARCH" \
        -DCMAKE_BUILD_TYPE=Release .. > cmake.log
  make -j4 all > make.log )
test -f "$AMGX_LIB/libamgxsh.so"

echo "== 2/4 links de compatibilidade (nomes do empacotamento Debian)"
mkdir -p "$CUDA_DEPS_DIR/compat/lib"
ln -sf /usr/lib/petscdir/petsc3.15/x86_64-linux-gnu-real/lib/libpetsc_real.so "$CUDA_DEPS_DIR/compat/lib/libpetsc.so"
ln -sf /usr/lib/x86_64-linux-gnu/libtrilinos_zoltan.so "$CUDA_DEPS_DIR/compat/lib/libzoltan.so"

echo "== 3/4 foam2csr"
clone_at https://github.com/mattmartineau/foam2csr.git "$CUDA_DEPS_DIR/foam2csr" $FOAM2CSR_COMMIT
apply_patch "$CUDA_DEPS_DIR/foam2csr" "$HERE/patches/foam2csr.patch"
sed -i "s/^NVARCH = .*/NVARCH = $ARCH/" "$CUDA_DEPS_DIR/foam2csr/Make/nvcc"
( cd "$CUDA_DEPS_DIR/foam2csr" && ./Allwmake > log.Allwmake 2>&1 )
test -f "$FOAM_USER_LIBBIN/libfoam2csr.so"

echo "== 4/4 amgx4foam"
clone_at https://github.com/maorz1998/amgx4foam.git "$CUDA_DEPS_DIR/amgx4foam" $AMGX4FOAM_COMMIT
apply_patch "$CUDA_DEPS_DIR/amgx4foam" "$HERE/patches/amgx4foam.patch"
( cd "$CUDA_DEPS_DIR/amgx4foam" && ./Allwmake > log.Allwmake 2>&1 )
test -f "$FOAM_USER_LIBBIN/libamgxFoam.so"

if ldd "$FOAM_USER_LIBBIN/libamgxFoam.so" | grep -q "not found"; then
  echo "ERRO: dependências não resolvidas:"; ldd "$FOAM_USER_LIBBIN/libamgxFoam.so" | grep "not found"; exit 1
fi
echo "OK: libamgxFoam.so pronto em $FOAM_USER_LIBBIN"
