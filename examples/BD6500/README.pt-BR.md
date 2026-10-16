# Motor diesel Branco BD-6500 — ciclo 3D com válvulas móveis

Caso de exemplo do OpenFOAM-14 (`foamRun -solver fluid`): admissão, compressão, combustão, expansão e escape de um motor monocilíndrico, com pistão e duas válvulas em movimento. A malha é trocada a cada 10–20° de virabrequim (`meshToMesh`), e a liberação de calor segue uma função de Wiebe de 2 estágios, ajustada ao ensaio.

*[English](README.md)*

![Pressão no cilindro (versão 1)](imagens/pressao_v1.png)

**Comparação com o modelo de Wiebe.** O gráfico sobrepõe o ensaio (pontos), o CFD do wiebepy
case_006 (laranja: a mesma liberação de calor Wiebe de 2 estágios num caso de válvulas fechadas) e
as duas rodadas 3D com válvulas móveis:

| Curva | p_max | Ângulo | vs. ensaio |
|---|---|---|---|
| Ensaio (carga 60 %) | 5,90 MPa | 10,0° | — |
| wiebepy CFD case_006, válvulas fechadas, Wiebe 2 estágios | acompanha o ensaio | | |
| 3D, trecho fechado (FA→AE) partindo da carga do ensaio em FA | 5,75 MPa | 10,5° | −2,5 % |
| 3D, ciclo completo, carga da troca de gases simulada | 5,59 MPa | 10,5° | −5,3 % |

Com a carga do ensaio em FA, o caso 3D com a liberação de calor Wiebe fica próximo do ensaio e do
case_006. As duas curvas 3D diferem só na carga aprisionada em FA; portanto, a queda adicional do
ciclo completo vem da troca de gases simulada, não do modelo de combustão.

[![Ciclo 3D, versão 1: velocidade (esquerda) e temperatura (direita)](imagens/motor3d_ciclo_v1.gif)](imagens/motor3d_ciclo_v1.mp4)

*Ciclo da versão 1, de −360° a +360°: módulo da velocidade (esquerda) e temperatura (direita) no
plano que passa pelas duas válvulas. Clique na imagem para o MP4 completo (1800×1000, 17 s).*

## Dados do motor

| | |
|---|---|
| Diâmetro × curso, biela | 86 × 70 mm, 117,5 mm |
| Taxa de compressão | 17 nominal; 15,14 efetiva (ajuste do wiebepy) |
| Ponto de operação | 3311 rpm, carga 60 % |
| Válvulas | FA 128° antes do PMS, AE 123° depois do PMS (ficha do motor); AA/FE 16° (estimados) |
| Lift máximo, pratos | 7,5 mm; 38 mm (adm.) e 32 mm (esc.) (estimados) |
| Calor liberado | 454 J/ciclo (1,158×10⁻⁵ kg de diesel × 39 191 kJ/kg) |
| Wiebe (2 estágios) | β 0,6456 / 0,3544; θ₀ −19,33° / 3,66°; Δθ 64,40° / 18,93°; m 2,555 / 0,368; a 6,908 |

Convenção: 0° é o PMS da combustão; o ciclo vai de −360° a +360°. O eixo z aponta para cima, com o cabeçote plano em z = 0, a admissão em x < 0 e o escape em x > 0.

## Requisitos

- OpenFOAM-14 compilado e carregado (`source <OpenFOAM-14>/etc/bashrc`).
- Python 3 com `scripts/requirements.txt` (`trimesh`, `manifold3d`, `numpy`, `scipy`, `matplotlib`). O ideal é um venv. No Ubuntu 22.04 sem venv, usando o scipy do sistema, instale `"numpy<2"`.
- 4 núcleos e cerca de 8 GB de RAM. Disco: cerca de 35 GB para os 3 ciclos com a gravação padrão.

## Como rodar

```bash
./Allmesh            # geometria + 62 malhas (NJOBS=3 em paralelo; cerca de 1 h)
./Allrun             # monta run/ e roda 3 ciclos (4 processos; cerca de 1,5 a 2 dias num i5-12450HX)
./Allrun -retoma     # continua do último tempo gravado, se a rodada for interrompida
./Allrun -monta      # só monta e decompõe o caso, sem rodar
./Allclean
```

No fim, `pressao_ciclos.png` compara a pressão média no cilindro de cada ciclo com o ensaio (`dados/ensaio_P_carga60.csv`).

## Como funciona

1. **Geometria** (`scripts/geometria.py <CA> <pasta>`): faz as operações booleanas de sólidos (manifold3d) do cilindro, dutos e válvulas na posição do pistão e com o lift daquele ângulo. Grava `fluido.stl`, com as regiões nomeadas a partir do id de origem de cada triângulo, e `info.txt`. O perfil de came é `L·sin(πf)^p`, com `p` escolhido para que o lift passe por 1,5 mm exatamente em FA e AE.
2. **Malha** (`scripts/malha.sh`): blockMesh de 1,5 mm, refinado nos pratos e nas sedes, seguido do snappyHexMesh. Se o checkMesh reprovar, há até 5 tentativas com a malha de fundo deslocada e snap explícito ou implícito (`scripts/malha_angulo.sh`). A malha é aceita com "Mesh OK" ou se a única reprovação for de skewness, com máximo menor que 10. Ângulos rejeitados ficam fora da lista.
3. **Caso** (`Allrun`): o `multiValveEngine` move o pistão e as válvulas entre as malhas, e o `meshToMesh` troca para a próxima malha nos tempos de `constant/meshTimes`, repetindo a cada 720°. O `heatSource` aplica `q''' = Q_Wiebe(CA)/V_cilindro(CA)` na zona `cilindro` (z < 0). A rodada é feita em trechos com passo próprio: maxCo 1 e passo máximo de 0,05° na combustão (−30° a +50°); passo de 0,05° na admissão e no escape.

## Detalhes importantes

- **Tempo do caso = CA + 360.** O `meshToMesh` do OpenFOAM-14 converte o tempo da malha em índice com `int64_t((t + Δ/2)/Δ)` (`src/fvMeshTopoChangers/meshToMesh/meshToMesh_fvMeshTopoChanger.C`, linhas 141 e 236). Esse cálculo trunca errado os tempos negativos, e as malhas de CA < 0 não seriam encontradas. Por isso o caso desloca o tempo em +360: o ciclo 1 vai de 0 a 720, o ciclo 2 de 720 a 1440 e o ciclo 3 de 1440 a 2160.
- **Válvula fechada.** O mover para a válvula em `minLift` = 1,5 mm. A geometria faz o mesmo: a válvula fechada fica em 1,5 mm, e um anel de selo, rente ao cabeçote, veda a fresta. Assim a posição da válvula fechada é a mesma na geometria e no mover.
- **Faces soltas no selo** (`scripts/conserta_selo.sh`). O snappyHexMesh deixa pedaços isolados de `ivHead`/`evHead` no topo do anel de selo. Se um pedaço desses não tiver correspondente na malha seguinte, o `meshToMesh` aborta com *"Un-mapped face … not connected to a mapped cell by the stabilisation wave"*. Por isso, em cada malha, as faces da válvula fechada no plano do selo passam para `ivSeat`/`evSeat`. As condições de contorno são as mesmas (T = 440 K, velocidade nula com a válvula parada), então a física não muda.
- **`q` em vez de `Q`** no `heatSource`. Com `Q` (total), o OF-14 divide pelo volume da zona calculado uma única vez, na leitura do caso. Perto do PMS, isso aplicava só cerca de 7 % do calor.
- **Decomposição `hierarchical (2 2 1)`.** Os planos x = 0 e y = 0 cortam cada válvula em metades contínuas. Com o scotch, sobravam fragmentos de superfície isolados num processo, o que quebrava o mapeamento.

## Resultados obtidos

| Caso | p_max | Ângulo |
|---|---|---|
| Ensaio (carga 60 %) | 5,90 MPa | 10,0° |
| Versão 1: um ciclo, carga da troca de gases simulada | 5,59 MPa | — |
| Trecho fechado (FA→AE) partindo da carga do ensaio em FA | 5,75 MPa | 10,5° |
| Versão 2 (este caso), ciclo 1 | 5,28 MPa | 10,9° |
| Versão 2, ciclo 3 | *(a preencher)* | |

O ciclo 1 parte de um estado inicial arbitrário (105 kPa, 750 K, com gás de escape nos dutos). Os ciclos 2 e 3 já partem da carga e do resíduo produzidos pela troca de gases simulada.

## Arquivos

```
Allmesh, Allrun, Allclean
angulos.txt              ângulos das malhas (CA)
malha/system/            modelo do blockMesh/snappyHexMesh (com placeholders preenchidos por malha.sh)
caso/0.orig, constant/, system/
scripts/                 geometria.py, malha.sh, malha_angulo.sh, aceita.sh, conserta_selo.sh,
                         gera_tabelas.py (lift), gera_wiebe_q.py (q'''), grafico_ciclos.py
dados/ensaio_P_carga60.csv   pressão medida (θ [rad], p [kPa])
imagens/                 resultados da versão 1 (gráfico de pressão, MP4 e prévia em GIF)
```
