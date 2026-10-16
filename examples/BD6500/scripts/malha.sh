#!/bin/bash
# Gera a malha 3D do motor num angulo a partir de geo/<theta>/{fluido.stl,info.txt}.
#   bash scripts/malha.sh <theta> [deslocamento] [explicito|implicito]
# Saida em malhas/<theta>. Requer o OpenFOAM-14 carregado (source etc/bashrc).
set -e
EX=$(cd "$(dirname "$0")/.." && pwd)
TH=$1
SHIFT=${2:-0}          # deslocamento da malha de fundo em x (nova tentativa se o checkMesh reprovar)
SNAP=${3:-explicito}   # explicito | implicito (snap as arestas; implicito e mais tolerante)
G=$EX/geo/$TH
D=$EX/malhas/$TH
[ -f $G/fluido.stl ] || { echo "falta $G/fluido.stl"; exit 1; }

zp=$(awk '/^pistao_z/{print $2}' $G/info.txt)
li=$(awk '/^lift_iv/{print $2}' $G/info.txt)
le=$(awk '/^lift_ev/{print $2}' $G/info.txt)
calc() { awk "BEGIN{printf \"%.6f\", $1}"; }
Z0=$(calc "$zp - 0.0015"); Z1=0.0515
NZ=$(awk -v a=$Z0 -v b=$Z1 'BEGIN{printf "%d", (b-a)/0.0015 + 0.5}')
LM=$(awk -v a=$li -v b=$le 'BEGIN{print (a>b?a:b)}')
SZ0=$(calc "-$LM - 0.004"); SZ1=0.0055
ZCIL=$(calc "$zp / 2")

rm -rf $D; mkdir -p $D/constant/geometry
cp -r $EX/malha/system $D/
cp $G/fluido.stl $D/constant/geometry/
X0=$(calc "-0.0465 + $SHIFT"); X1=$(calc "0.0465 + $SHIFT")
sed -i -e "s/Z0;/$Z0;/" -e "s/Z1;/$Z1;/" -e "s/NZ;/$NZ;/" -e "s/^x0 -0.0465; x1 0.0465;/x0 $X0; x1 $X1;/" $D/system/blockMeshDict
sed -i -e "s/IVX/-0.0200/g" -e "s/EVX/0.0220/g" -e "s/IVR/0.0230/" -e "s/EVR/0.0200/" \
       -e "s/SEDEZ0/$SZ0/g" -e "s/SEDEZ1/$SZ1/g" -e "s/ZCIL/$ZCIL/" \
       -e "s/IPX/-0.0100/" -e "s/EPX/0.0140/" $D/system/snappyHexMeshDict
if [ "$SNAP" = implicito ]; then
  sed -i -e "s/explicitFeatureSnap true;/explicitFeatureSnap false;/" \
         -e "s/implicitFeatureSnap false;/implicitFeatureSnap true;/" $D/system/snappyHexMeshDict
fi

cd $D
blockMesh > log.blockMesh 2>&1
surfaceFeatures > log.surfaceFeatures 2>&1
snappyHexMesh -overwrite > log.snappyHexMesh 2>&1
checkMesh > log.checkMesh 2>&1 || true
