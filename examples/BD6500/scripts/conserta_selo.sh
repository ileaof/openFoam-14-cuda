#!/bin/bash
# Passa para o patch do assento (ivSeat/evSeat) as faces de ivHead/evHead que o snappyHexMesh deixa
# soltas no topo do anel de selo (z = zs) de uma valvula fechada. Sem isso, essas "ilhas" de patch
# podem nao ter correspondente na malha seguinte e o meshToMesh aborta
# ("Un-mapped face ... was not connected to a mapped cell by the stabilisation wave").
# Valvula e assento tem as mesmas condicoes de contorno com a valvula parada, entao a fisica nao muda.
#   bash scripts/conserta_selo.sh <caso> "<iv ev>" [opcoes do topoSet/createPatch, ex.: -parallel]
#   (em paralelo: MPI="mpirun -np 4" bash scripts/conserta_selo.sh ...)
# zs = (raio do prato - raio do duto) - LIFT_MIN: 1,0 mm no escape e 1,5 mm na admissao.
C=$1; V=$2; shift 2
[ -z "$V" ] && exit 0
mkdir -p $C/system
{
  echo 'FoamFile { format ascii; class dictionary; object topoSetDict; }'
  echo 'actions ('
  for v in $V; do
    [ $v = ev ] && z0=0.00099 z1=0.00101 || z0=0.00149 z1=0.00151
    echo "  { name ${v}Frag; type faceSet; action new; source patchToFace; patch ${v}Head; }"
    echo "  { name ${v}Frag; type faceSet; action subset; source boxToFace; box (-1 -1 $z0) (1 1 $z1); }"
  done
  echo ');'
} > $C/system/topoSetDict.selo
{
  echo 'FoamFile { format ascii; class dictionary; object createPatchDict; }'
  echo 'patches ('
  for v in $V; do
    echo "  { name ${v}Seat; patchInfo { type wall; } constructFrom set; set ${v}Frag; }"
  done
  echo ');'
} > $C/system/createPatchDict.selo
$MPI topoSet -case $C -dict system/topoSetDict.selo "$@" && \
$MPI createPatch -case $C -dict system/createPatchDict.selo "$@"
