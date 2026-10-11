# Tutoriais com a pressão na GPU

Casos prontos para rodar com o solver `amgx` (AMGX da NVIDIA, via `libamgxFoam.so`).
Só entram aqui casos em que **medimos ganho** da GPU sobre a CPU nesta árvore; os
números estão em [`cuda/benchmarks/`](../../cuda/benchmarks/).

Antes, compile a parte GPU ([`cuda/README.md`](../../cuda/README.md)) e, em todo
terminal novo:

```bash
source ~/dev/OpenFOAM-14/cuda/scripts/env.sh
```

| Caso | Solver | Malha | Ganho medido (GPU × CPU, 4 processos) |
|---|---|---|---|
| [`cavity3D`](cavity3D/) | `icoFoam`, PISO transiente | 80³ = 0,5 M células | 1,03× (empate) |
| | | 100³ = 1 M células | 1,42× (0,403 × 0,570 s/passo) |
| | | 125³ = 2 M células | 1,54× (0,834 × 1,283 s/passo) |
| | | 140³ = 2,7 M células | 1,62× (1,192 × 1,932 s/passo) |
| | | 150³ = 3,4 M células | 2,09× (1,485 × 3,110 s/passo) |

```bash
cd tutorials/GPU/cavity3D
./Allrun gpu            # pressão na GPU
./Allrun cpu            # a mesma coisa com GAMG, para comparar
N=150 ./Allrun gpu      # malha maior: é onde a GPU se destaca
```

`./Allrun` nesta pasta roda todos os casos em modo `gpu`. Sem a `libamgxFoam.so`
ele não faz nada, para não interromper a bateria de tutoriais do OpenFOAM em
máquinas sem GPU.

## Por que outros casos não estão aqui

A GPU acelera só o solve de pressão. Se a pressão é uma parte pequena do passo,
o ganho total some (lei de Amdahl), mesmo com a GPU funcionando bem.

| Caso | O que medimos |
|---|---|
| `incompressibleFluid/motorBike` (3,2 M células, SIMPLE) | empate: 2,48 × 2,55 s/iteração; a pressão é ~10% da iteração |
| `multicomponentFluid/smallPoolFire3D` (216 mil células) | na CPU, 0,28 s/passo com só 3,7 iterações de GAMG por solve de `p_rgh`; o tempo vai para radiação (`fvDOM`) e química |

Regra prática: no log da CPU, se o `GAMG` faz só 1 a 3 iterações por solve de
pressão, a GPU tem pouco a ganhar. Se as iterações crescem com a malha, como na
cavity3D (7,4 → 15,6 de 1 M para 3,4 M células, enquanto a AMGX fica em ~5,5), é aí
que ela compensa.

## Ajustar a receita da AMGX ao seu caso

A configuração faz muita diferença. Na cavity3D com 1 M células:

| Receita AMGX | s/passo | Iterações de p |
|---|---:|---:|
| `FGMRES_CLASSICAL_AGGRESSIVE_PMIS` (padrão deste repositório) | **0,417** | 5,5 |
| `PCG_CLASSICAL_V_JACOBI` | 0,448 | 8,7 |
| `PCG_CLASSICAL_F_JACOBI` | 0,641 | 3,5 |
| `agg_cheb4` | 0,663 | 7,5 |
| `PCG_AGGREGATION_JACOBI` (padrão antigo) | 0,766 | 22,8 |
| `FGMRES_AGGREGATION_DILU` | 0,942 | 7,7 |

Para comparar receitas no seu caso (já decomposto, com `endTime` curto):

```bash
python3 cuda/scripts/tune_amgx.py --case <caso> --solver foamRun --np 4 \
    --dict p=0.05 --dict pFinal=0.001       # use o relTol de cada dicionário
```
