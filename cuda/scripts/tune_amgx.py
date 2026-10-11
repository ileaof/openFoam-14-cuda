#!/usr/bin/env python3
"""Tries AMGX recipes on a decomposed case and reports which one is fastest.

Each recipe is a configuration that ships with AMGX (~/dev/AMGX/src/configs).
The script adds what OpenFOAM needs (relative criterion, residual history,
AMG structure reuse), runs the whole case with each recipe and compares the
time per step after the warm-up.

Usage (with cuda/scripts/env.sh sourced, case already decomposed, short endTime):
  python3 cuda/scripts/tune_amgx.py --case ~/runs/meuCaso --solver icoFoam \
      --np 4 --dict p=0.05 --dict pFinal=0.001

  --dict name=tol   one per "amgx { dict name; }" dictionary in fvSolution;
                    tol is the RELATIVE tolerance (use the case's relTol).
  --recipes ...     recipes to try (default: the ones that worked well for pressure)
"""
import argparse, json, os, subprocess, sys

DEFAULT_RECIPES = [
    "FGMRES_CLASSICAL_AGGRESSIVE_PMIS",
    "PCG_CLASSICAL_V_JACOBI",
    "PCG_CLASSICAL_F_JACOBI",
    "agg_cheb4",
    "PCG_AGGREGATION_JACOBI",
]


def make_cfg(cfgdir, name, tol):
    d = json.load(open(os.path.join(cfgdir, f"{name}.json")))
    s = d["solver"]
    s.update({"convergence": "RELATIVE_INI", "tolerance": tol, "max_iters": 200,
              "monitor_residual": 1, "store_res_history": 1, "obtain_timings": 1,
              "print_solve_stats": 1, "norm": "L2"})
    pc = s.get("preconditioner")
    amg = pc if isinstance(pc, dict) and pc.get("solver") == "AMG" else (s if s.get("solver") == "AMG" else None)
    if amg is not None:
        amg["structure_reuse_levels"] = -1
    return d


def parse(log, warmup):
    et, step, amgx, co, iters = {}, 0, 0.0, None, {}
    for line in open(log, errors="replace"):
        if line.startswith("Time = "):
            step += 1
        elif line.startswith("ExecutionTime"):
            et[step] = float(line.split()[2])
        elif line.startswith("AMGx:  Solving for") and step > warmup:
            field = line.split()[3].rstrip(",")
            iters.setdefault(field, []).append(int(line.split()[-1]))
        elif line.startswith("Total Time:") and step > warmup:
            amgx += float(line.split()[2])
        elif line.startswith("Courant Number mean"):
            co = line.split(":", 1)[1].strip()
    if step <= warmup or warmup not in et:
        return None
    n = step - warmup
    its = " ".join(f"{k}:{sum(v)/len(v):.1f}" for k, v in iters.items())
    return (et[step] - et[warmup]) / n, amgx / n, its, co


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--case", required=True)
    ap.add_argument("--solver", required=True)
    ap.add_argument("--np", type=int, default=4)
    ap.add_argument("--dict", action="append", required=True, metavar="NAME=TOL")
    ap.add_argument("--recipes", nargs="+", default=DEFAULT_RECIPES)
    ap.add_argument("--warmup", type=int, default=5)
    ap.add_argument("--amgx-configs", default=os.path.expanduser(
        os.path.join(os.environ.get("CUDA_DEPS_DIR", "~/dev"), "AMGX/src/configs")))
    a = ap.parse_args()
    case = os.path.expanduser(a.case)
    dicts = [(n, float(t)) for n, t in (d.split("=") for d in a.dict)]

    print(f"{'recipe':36s} {'s/step':>8s} {'AMGX s':>7s}  iterations  final Courant")
    for name in a.recipes:
        for dname, tol in dicts:
            out = os.path.join(case, "system", f"amgx{dname}Options")
            json.dump(make_cfg(a.amgx_configs, name, tol), open(out, "w"), indent=4)
        log = os.path.join(case, f"log.tune_{name}")
        rc = subprocess.run(f"cd {case} && mpirun -np {a.np} {a.solver} -parallel > {log} 2>&1",
                            shell=True).returncode
        r = parse(log, a.warmup) if rc == 0 else None
        if r is None:
            print(f"{name:36s} FAILED (see {log})", flush=True)
        else:
            print(f"{name:36s} {r[0]:8.3f} {r[1]:7.3f}  {r[2]:10s} {r[3]}", flush=True)
    print("All recipes should reach the same final Courant number; discard any that differs.")


if __name__ == "__main__":
    sys.exit(main())
