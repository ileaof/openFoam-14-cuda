#!/bin/bash
# Malha de um angulo, com ate 5 tentativas (malha de fundo deslocada e snap explicito/implicito),
# seguida da correcao do selo das valvulas fechadas.  bash scripts/malha_angulo.sh <theta>
EX=$(cd "$(dirname "$0")/.." && pwd)
th=$1
if bash $EX/scripts/aceita.sh $th; then echo "$th: ja OK"; exit 0; fi
for tent in "0 explicito" "0.00031 explicito" "-0.00043 explicito" "0 implicito" "0.00031 implicito"; do
  set -- $tent
  t0=$(date +%s)
  bash $EX/scripts/malha.sh $th $1 $2 > /dev/null 2>&1 || true
  if bash $EX/scripts/aceita.sh $th; then
    # valvula fechada (lift 0 em info.txt): faces soltas no topo do selo -> patch do assento
    V=""
    awk '/^lift_iv/{exit !($2+0==0)}' $EX/geo/$th/info.txt && V="$V iv"
    awk '/^lift_ev/{exit !($2+0==0)}' $EX/geo/$th/info.txt && V="$V ev"
    bash $EX/scripts/conserta_selo.sh $EX/malhas/$th "$V" > $EX/malhas/$th/log.selo 2>&1 \
      || { echo "$th: falhou a correcao do selo (ver malhas/$th/log.selo)"; exit 1; }
    rm -rf $EX/malhas/$th/constant/polyMesh/sets
    echo "$th: OK (desloc $1, snap $2) $(grep -m1 -o 'cells: *[0-9]*' $EX/malhas/$th/log.checkMesh)" \
         "selo:${V:- nenhum} $(( $(date +%s) - t0 )) s"
    exit 0
  fi
  echo "$th: falhou (desloc $1, snap $2)"
done
echo "$th: REJEITADA (fica fora da lista de malhas)"
