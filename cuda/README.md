# Solver de pressão na GPU (AMGX) para o OpenFOAM-14

Esta pasta acopla o [AMGX](https://github.com/NVIDIA/AMGX) da NVIDIA ao OpenFOAM-14
como um `lduMatrix::solver` chamado `amgx`, selecionado no `fvSolution`.
**Nenhum arquivo do OpenFOAM Foundation é alterado**: todas as mudanças estão em
dois projetos de terceiros, aplicadas como patches.

```
OpenFOAM-14  →  amgx4foam (libamgxFoam.so)  →  foam2csr (libfoam2csr.so)  →  AMGX (libamgxsh.so, GPU)
```

| Pasta | Conteúdo |
|---|---|
| `patches/` | correções para o foam2csr e o amgx4foam rodarem com OpenFOAM-14 e CUDA 13 |
| `scripts/env.sh` | variáveis de ambiente (source antes de compilar ou rodar) |
| `scripts/build_all.sh` | clona as três dependências nos commits testados, aplica os patches e compila |
| `config/amgxpOptions` | configuração da AMGX recomendada (FGMRES + AMG clássico PMIS) |
| `scripts/tune_amgx.py` | compara receitas da AMGX num caso seu e mostra a mais rápida |
| `scripts/render_*.py` | figuras do README no ParaView (motorBike, pluma, HVAC) |
| `benchmarks/` | resultados medidos: [cavity3D](benchmarks/cavity3D.md) (PISO, 1 e 3,4 M células) e [motorBike](benchmarks/motorBike.md) (SIMPLE, 3,2 M) |
| [`../tutorials/GPU/`](../tutorials/GPU/) | casos prontos em que a GPU ganha da CPU (`./Allrun gpu`) |
| `docs/` | tutorial passo a passo e relatório técnico em HTML (baixe e abra no navegador) |

## Início rápido

Requisitos: GPU NVIDIA com compute capability ≥ 7.0, WSL2 ou Linux com Ubuntu 22.04,
CUDA Toolkit em `/usr/local/cuda` (testado com 13.2), OpenFOAM-14 já compilado nesta árvore e
os pacotes `libpetsc-real-dev`, `libtrilinos-zoltan-dev`, `libscotch-dev`, `libptscotch-dev`.

```bash
cd ~/dev/OpenFOAM-14
nvidia-smi --query-gpu=compute_cap --format=csv   # ex.: 8.9
bash cuda/scripts/build_all.sh 89                 # 8.9 -> 89
```

Num caso, três arquivos:

```
system/controlDict   libs ("libamgxFoam.so");
system/fvSolution    p { solver amgx; amgx { dict p; } }
system/amgxpOptions  copie de cuda/config/amgxpOptions
```

Rode sempre decomposto e em paralelo (a AMGX exige MPI inicializado):

```bash
source cuda/scripts/env.sh
decomposePar && mpirun -np 4 foamRun -parallel     # procure linhas "AMGx:  Solving for p"
```

## Antes de concluir que a GPU não vale a pena

1. **O `tolerance`/`relTol` do `fvSolution` é ignorado.** O critério que vale é o `"tolerance"` do `amgxpOptions` (`RELATIVE_INI`). Iguale ao `relTol` do caso, ou a GPU fará muito mais trabalho que a CPU.
2. **Não use `caching { update periodic | adaptive | never; }`.** Nesses modos o amgx4foam deixa de atualizar a matriz, e o resultado fica fisicamente errado mesmo convergindo. Para economizar setup use `"structure_reuse_levels": -1`, que já está em `config/amgxpOptions`.
3. **Malha pequena favorece a CPU.** Use a cavity só para validar o resultado, não para medir velocidade.
   Na [cavity3D](benchmarks/cavity3D.md) o ganho vai de 1,03× com 0,5 M células a 2,09× com 3,4 M.
4. **2 a 4 processos por GPU.** Cada processo abre um contexto CUDA na mesma placa.
5. **Libere a GPU.** ParaView, jogos e o próprio desktop disputam a memória da placa; falta de memória aparece como `Cuda failure: 'unknown error'` / `Out of resource`.
6. **Em regime permanente (SIMPLE) a pressão costuma ser só ~10% da iteração.** O ganho aparece em casos transientes em que a pressão domina. Veja `benchmarks/motorBike.md`.
7. **A receita da AMGX importa.** Na cavity3D, a antiga `PCG_AGGREGATION_JACOBI` faz 4× mais iterações que a `FGMRES_CLASSICAL_AGGRESSIVE_PMIS` e deixa a GPU mais lenta que a CPU. Compare no seu caso com `scripts/tune_amgx.py`.

---
Fork comunitário, não oficial. OpenFOAM® é marca registrada da OpenFOAM Foundation.
AMGX (BSD-3), foam2csr e amgx4foam pertencem aos seus autores; este repositório
distribui apenas patches sobre eles.
