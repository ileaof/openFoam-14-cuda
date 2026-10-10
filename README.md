# openFoam-14-cuda

Fork não-oficial do [OpenFOAM-14](https://github.com/OpenFOAM/OpenFOAM-14) (OpenFOAM Foundation), com o objetivo de adicionar:

- Suporte a compiladores **Intel oneAPI** (`icx`/`icpx`/`ifx`)
- Aceleração **GPU/CUDA** do solver linear via [amgx4Foam](https://github.com/Simulation-and-Software-Technology/amgx4Foam) (NVIDIA AmgX), permitindo paralelizar o solve de pressão/momentum em GPU

**Este projeto não é afiliado, endossado ou mantido pela OpenFOAM Foundation ou pela ESI/OpenCFD.** "OpenFOAM" é uma marca registrada da OpenFOAM Foundation. Este é um fork comunitário independente.

Licenciado sob GPL-3.0, como o projeto original — veja [COPYING](COPYING). O histórico de commits e tags do upstream foi preservado integralmente.

## Status

🚧 Em desenvolvimento. Ver [upstream README](README.org) para a documentação original do OpenFOAM.

## Roteiro

- [x] Importar histórico completo do OpenFOAM-14
- [ ] Build baseline com GCC (validação)
- [ ] Build com Intel oneAPI
- [ ] Integração amgx4Foam (CUDA)
- [ ] Benchmarks CPU vs GPU
