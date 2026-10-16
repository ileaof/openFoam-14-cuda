#!/bin/bash
# Criterio de aceitacao de uma malha: bash scripts/aceita.sh <theta>  (status 0 = aceita)
# "Mesh OK" do checkMesh, ou reprovacao SO por assimetria (skewness) com maximo < 10
# (nenhuma piramide invertida, volume negativo etc.).
EX=$(cd "$(dirname "$0")/.." && pwd)
L=$EX/malhas/$1/log.checkMesh
[ -f "$L" ] || exit 1
grep -q "Mesh OK" -- "$L" && exit 0
outros=$(grep -E "\*\*\*" -- "$L" | grep -v -i "skew" | wc -l)
sk=$(grep -o -E "Max skewness = [0-9.]+" -- "$L" | head -1 | awk '{print $4}')
[ "$outros" -eq 0 ] && [ -n "$sk" ] && awk -v s="$sk" 'BEGIN{exit !(s < 10)}'
