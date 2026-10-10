# Benchmark: motorBike, CPU × GPU

Medido em 10/10/2026 numa RTX 4050 Laptop (6 GB, sm_89), WSL2 Ubuntu 22.04,
CUDA 13.2, OpenFOAM-14 compilado com GCC 11.4.

## Caso

- Tutorial `incompressibleFluid/motorBike`, malha do `snappyHexMesh`: **3.215.800 células**
- `foamRun` com `incompressibleFluid` (SIMPLE, regime permanente)
- 4 processos MPI, decomposição `hierarchical (2 2 1)`
- Tempo médio por iteração entre as iterações 10 e 100 (exclui leitura da malha e o primeiro setup)

## Resultado

| Configuração | s / iteração | Iterações do solver de p | Cd (it. 100) |
|---|---|---|---|
| GPU, tolerância do JSON (1e-6), 8 processos¹ | 3,7 | 41 | — |
| CPU, GAMG (`relTol 0.1`) | 2,550 | 2,0 | 0,7210 |
| GPU, AMGX `tolerance 0.1` | 2,522 | 1,4 | 0,7214 |
| GPU, AMGX `tolerance 0.1` + `structure_reuse_levels -1` | **2,478** | 1,4 | 0,7200 |

¹ Primeira tentativa, antes de descobrir que o amgx4Foam ignora `tolerance`/`relTol` do `fvSolution`.

## Leitura

- Com o critério de parada igualado, a GPU **empata** com a CPU e o resultado físico é o mesmo.
- O solve de pressão na AMGX leva **0,26 s** de cada iteração de 2,48 s, cerca de **10%**. O restante (velocidade, turbulência, montagem das matrizes, pós-processamento) roda na CPU. Pela lei de Amdahl, o ganho máximo possível acelerando só a pressão é de uns 12%.
- O reaproveitamento da estrutura do AMG reduziu o setup de 0,49 s para 0,15 s por solve.
- A GPU deve compensar quando a pressão domina a iteração: escoamentos transientes (PISO/PIMPLE) com vários correctores e `pFinal relTol 0`, em malhas grandes.

## Reproduzir

```bash
source cuda/scripts/env.sh
cp -r $FOAM_TUTORIALS/incompressibleFluid/motorBike/motorBike ~/runs/mb
# siga o Allrun do tutorial até o potentialFoam, com 4 subdomínios
# GPU: copie cuda/config/amgxpOptions para system/ e troque o solver de p (ver cuda/README.md)
mpirun -np 4 foamRun -parallel
```
