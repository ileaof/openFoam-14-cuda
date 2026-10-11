# OpenFOAM-14 em Apple Silicon (planejado)

> **Estado: plano, ainda não testado em Apple Silicon.** Os passos abaixo são o caminho
> previsto; serão validados e corrigidos quando a máquina de teste (M5, 64 GB) chegar.

## O que muda em relação ao Linux/WSL com NVIDIA

| Parte | Apple Silicon |
|---|---|
| OpenFOAM-14 na CPU | roda, compilado numa VM Linux ARM (aarch64) |
| Pressão na GPU (AMGX, pasta [`cuda/`](../cuda/)) | **não roda**: exige CUDA, que só existe em placas NVIDIA |
| Tutoriais de [`tutorials/GPU`](../tutorials/GPU/) | são pulados automaticamente (sem `libamgxFoam.so`) |
| ParaView | versão nativa para macOS |

## Caminho previsto

1. **VM Linux ARM.** Ubuntu 22.04 arm64 numa VM leve (OrbStack, Lima ou UTM). Imagens
   x86 via Docker também funcionam, mas emuladas pelo Rosetta, bem mais lentas.
2. **Dependências na VM**, as mesmas do Ubuntu x86:
   ```bash
   sudo apt install build-essential flex bison cmake zlib1g-dev libboost-system-dev \
       libboost-thread-dev libopenmpi-dev openmpi-bin libscotch-dev libptscotch-dev
   ```
3. **Compilar o fork** como em Linux (seções 2 e 3 do [README principal](../README.md)),
   sem a etapa da GPU.
4. **Validar** com cavity, motorBike e smallPoolFire3D, comparando com os resultados x86.

## A fazer quando a máquina chegar

- [ ] Confirmar se há pacotes prontos do OpenFOAM para arm64 ou se compilar é o caminho
- [ ] Compilar o fork em aarch64 e rodar a bateria de tutoriais
- [ ] `apple/scripts/setup_vm.sh`: criar a VM e instalar dependências (só depois de testado)
- [ ] Benchmark de CPU: cavity3D, motorBike, smallPoolFire3D com 4, 8 e todos os
      núcleos de performance, comparado com o notebook (CPU e RTX 4050)
- [ ] Levantar se existe caminho viável para o solver de pressão na GPU da Apple (Metal);
      hoje não há equivalente maduro à AMGX
