"""Reproducible projection-size/orientation benchmark; no result caching."""
import argparse
import importlib.util
import hashlib
import json
from pathlib import Path
import platform
import os
import statistics
import time
from datetime import datetime, timezone
from importlib.metadata import version, PackageNotFoundError

import numpy as np
import projection


def cpu_model():
    if platform.system() == "Windows":
        import winreg
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                                r"HARDWARE\DESCRIPTION\System\CentralProcessor\0") as key:
                return winreg.QueryValueEx(key, "ProcessorNameString")[0].strip()
        except OSError:
            pass
    return platform.processor()


def cases():
    center = np.array([249.5, 249.5, 249.5])
    u = np.array([1., 1., 0.]) / np.sqrt(2)
    v = np.array([-1., 1., 2.]) / np.sqrt(6)
    return [
        ("small_triangle", "triangle", ((250, 180, 100), (250, 330, 100), (250, 180, 250))),
        ("small_trapezoid", "trapezoid", ((250, 200, 100), (250, 300, 100), (250, 170, 250), (250, 330, 250))),
        ("assignment_triangle", "triangle", ((200, 200, 0), (0, 200, 400), (400, 200, 400))),
        ("assignment_rectangle", "trapezoid", ((200, 0, 0), (200, 0, 500), (200, 400, 0), (200, 400, 500))),
        ("review_large_trapezoid", "trapezoid", ((250, 149.5, 0), (250, 349.5, 0), (250, 0, 499), (250, 499, 499))),
        ("diagonal_triangle", "triangle", ((0, 0, 0), (499, 499, 0), (499, 0, 499))),
        ("diagonal_rectangle", "trapezoid", ((0, 0, 0), (499, 499, 0), (0, 0, 499), (499, 499, 499))),
        ("tilted_trapezoid", "trapezoid",
         (center - 80*u - 200*v, center + 80*u - 200*v,
          center - 200*u + 200*v, center + 200*u + 200*v)),
    ]


def run(repetitions=40, warmups=3, trials=3, module=projection, shape=None):
    volume = np.random.default_rng(20261101).integers(0, 256, (500, 500, 500), dtype=np.uint8)
    report = {
        "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
        "projection_sha256": hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest(),
        "environment": {"platform": platform.platform(), "processor": platform.processor(),
                        "machine": platform.machine(), "python": platform.python_version(),
                        "numpy": np.__version__, "backend": getattr(module, "BACKEND", "legacy numpy"),
                        "cpu_model": cpu_model(), "logical_cpus": os.cpu_count()},
        "method": {"volume_shape": list(volume.shape), "dtype": str(volume.dtype),
                   "seed": 20261101, "warmups": warmups, "repetitions": repetitions,
                   "trials": trials, "timer": "perf_counter_ns", "result_cache": False,
                   "includes": "geometry validation, scanline construction, sampling and output allocation",
                   "excludes": "volume generation, NRRD loading, CSV parsing and MP4 encoding"},
        "cases": [],
    }
    for package in ("numba", "llvmlite", "pynrrd", "imageio", "imageio-ffmpeg"):
        try:
            report["environment"][package] = version(package)
        except PackageNotFoundError:
            report["environment"][package] = None
    for order in ("C", "F"):
        data = np.array(volume, order=order, copy=True)
        for name, kind, points in cases():
            if shape and kind != shape:
                continue
            function = module.project_triangle if kind == "triangle" else module.project_trapezoid
            coordinates = [list(map(float, p)) for p in points]
            item = {"name": name, "kind": kind, "order": order, "points": coordinates}
            try:
                cold_start = time.perf_counter_ns()
                result = function(data, *points)
                item["first_call_ms"] = (time.perf_counter_ns() - cold_start) / 1e6
                for _ in range(warmups):
                    result = function(data, *points)
                trial_fps = []
                times = []
                for _ in range(trials):
                    samples = []
                    for _ in range(repetitions):
                        start = time.perf_counter_ns()
                        result = function(data, *points)
                        samples.append((time.perf_counter_ns() - start) / 1e6)
                    trial_fps.append(1000 / statistics.mean(samples))
                    times.extend(samples)
                item.update(output_shape=list(result.shape),
                            mean_ms=statistics.mean(times), median_ms=statistics.median(times),
                            min_ms=min(times), max_ms=max(times),
                            p95_ms=float(np.percentile(times, 95)),
                            fps=1000/statistics.mean(times), trial_fps=trial_fps,
                            above_30=all(fps > 30 for fps in trial_fps), timings_ms=times)
                print(f"{order} {name:25s} {result.shape!s:13s} {item['fps']:8.2f} FPS", flush=True)
            except ValueError as error:
                item["error"] = str(error)
                print(f"{order} {name}: REJECTED: {error}", flush=True)
            report["cases"].append(item)
    return report


def main(shape=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repetitions", type=int, default=40)
    parser.add_argument("--warmups", type=int, default=3)
    parser.add_argument("--trials", type=int, default=3)
    parser.add_argument("--json", type=Path)
    parser.add_argument("--module-file", type=Path, help="Compare an older projection.py without modifying it")
    args = parser.parse_args()
    if min(args.repetitions, args.warmups, args.trials) < 1:
        parser.error("repetitions, warmups and trials must be positive")
    module = projection
    if args.module_file:
        spec = importlib.util.spec_from_file_location("benchmark_comparison", args.module_file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    report = run(args.repetitions, args.warmups, args.trials, module, shape)
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
