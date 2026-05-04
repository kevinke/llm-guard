from __future__ import annotations

import argparse
import concurrent.futures
import importlib
import json
import os
import platform
import sys
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, List, Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

try:
    import psutil
except ImportError:  # pragma: no cover
    psutil = None


def _common_module():
    return importlib.import_module("benchmarks.common")


def _torch_module():
    try:
        return importlib.import_module("torch")
    except ImportError as error:  # pragma: no cover
        raise RuntimeError(
            "torch is required to run this benchmark. Install llm-guard runtime dependencies first."
        ) from error


def _optional_torch_module():
    try:
        return importlib.import_module("torch")
    except ImportError:
        return None


def _numpy_module():
    return importlib.import_module("numpy")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Benchmark llm-guard latency, throughput, and process resource usage."
    )
    parser.add_argument("type", choices=["input", "output"], help="Scanner pipeline type.")
    parser.add_argument(
        "scanners",
        nargs="+",
        help="Scanner class names to benchmark in order. Pass multiple names to measure a pipeline.",
    )
    parser.add_argument(
        "--concurrency",
        nargs="+",
        type=int,
        default=[1, 2, 5],
        help="Concurrency levels to test. Defaults to 1 2 5.",
    )
    parser.add_argument(
        "--iterations-per-concurrency",
        type=int,
        default=5,
        help="Requests to run per worker at each concurrency level.",
    )
    parser.add_argument(
        "--warmup-requests",
        type=int,
        default=2,
        help="Warmup requests to run before steady-state measurements.",
    )
    parser.add_argument(
        "--sample-interval-ms",
        type=float,
        default=50.0,
        help="Resource sampling interval in milliseconds.",
    )
    parser.add_argument(
        "--torch-num-threads",
        type=int,
        help="Optional torch intra-op thread limit.",
    )
    parser.add_argument(
        "--torch-num-interop-threads",
        type=int,
        help="Optional torch inter-op thread limit.",
    )
    parser.add_argument(
        "--omp-num-threads",
        type=int,
        help="Optional OMP_NUM_THREADS override for this benchmark process.",
    )
    parser.add_argument(
        "--mkl-num-threads",
        type=int,
        help="Optional MKL_NUM_THREADS override for this benchmark process.",
    )
    parser.add_argument(
        "--prompt-file",
        type=Path,
        help="Optional UTF-8 prompt file. Defaults to the first scanner example.",
    )
    parser.add_argument(
        "--output-file",
        type=Path,
        help="Optional UTF-8 output file for output scanners. Defaults to the first scanner example.",
    )
    parser.add_argument(
        "--use-onnx",
        action="store_true",
        help="Use ONNX runtime when the selected scanners support it.",
    )
    parser.add_argument(
        "--json-output",
        type=Path,
        help="Optional path to write the JSON report to disk.",
    )
    parser.add_argument(
        "--markdown-output",
        type=Path,
        help="Optional path to write a Markdown summary report.",
    )
    parser.add_argument(
        "--csv-output",
        type=Path,
        help="Optional path to write a CSV summary report.",
    )

    return parser.parse_args()


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _get_total_memory_bytes() -> int | None:
    if psutil is not None:
        return int(psutil.virtual_memory().total)

    if hasattr(os, "sysconf") and "SC_PAGE_SIZE" in os.sysconf_names and "SC_PHYS_PAGES" in os.sysconf_names:
        return int(os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES"))

    return None


def _get_rss_bytes() -> int | None:
    if psutil is not None:
        return int(psutil.Process().memory_info().rss)

    statm_path = Path("/proc/self/statm")
    if statm_path.exists():
        resident_pages = int(statm_path.read_text(encoding="utf-8").split()[1])
        return int(resident_pages * os.sysconf("SC_PAGE_SIZE"))

    return None


def _get_peak_rss_bytes() -> int | None:
    try:
        import resource
    except ImportError:  # pragma: no cover
        return None

    peak_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    if platform.system() == "Darwin":
        return int(peak_rss)

    return int(peak_rss * 1024)


def _bytes_to_mb(value: int | None) -> float | None:
    if value is None:
        return None

    return round(value / (1024.0 * 1024.0), 2)


def _percentile(values: Sequence[float], percentile: int) -> float:
    if not values:
        return 0.0

    return round(float(_numpy_module().percentile(values, percentile)), 2)


def _mean(values: Sequence[float]) -> float:
    if not values:
        return 0.0

    return round(float(sum(values) / len(values)), 2)


def _cpu_cores_from_percent(cpu_percent: float | None) -> float | None:
    if cpu_percent is None:
        return None

    return round(cpu_percent / 100.0, 2)


def _build_machine_info() -> dict[str, Any]:
    total_memory_bytes = _get_total_memory_bytes()
    torch_module = _optional_torch_module()
    cuda_available = bool(torch_module is not None and torch_module.cuda.is_available())
    return {
        "hostname": platform.node(),
        "platform": platform.platform(),
        "python_version": platform.python_version(),
        "cpu_count_logical": os.cpu_count(),
        "total_memory_mb": _bytes_to_mb(total_memory_bytes),
        "torch_version": torch_module.__version__ if torch_module is not None else None,
        "cuda_available": cuda_available,
        "cuda_device": torch_module.cuda.get_device_name(0) if cuda_available else None,
    }


def apply_runtime_thread_settings(args: argparse.Namespace):
    if args.omp_num_threads is not None:
        os.environ["OMP_NUM_THREADS"] = str(args.omp_num_threads)

    if args.mkl_num_threads is not None:
        os.environ["MKL_NUM_THREADS"] = str(args.mkl_num_threads)

    if args.torch_num_threads is None and args.torch_num_interop_threads is None:
        return

    torch_module = _torch_module()
    if args.torch_num_threads is not None:
        torch_module.set_num_threads(args.torch_num_threads)

    if args.torch_num_interop_threads is not None:
        torch_module.set_num_interop_threads(args.torch_num_interop_threads)


def _thread_settings(args: argparse.Namespace) -> dict[str, Any]:
    return {
        "torch_num_threads": args.torch_num_threads,
        "torch_num_interop_threads": args.torch_num_interop_threads,
        "omp_num_threads": args.omp_num_threads,
        "mkl_num_threads": args.mkl_num_threads,
    }


def run_input_pipeline(scanners: Sequence[Any], prompt: str) -> tuple[str, list[dict[str, Any]]]:
    current_prompt = prompt
    scanner_results: list[dict[str, Any]] = []
    for scanner in scanners:
        start_time = time.perf_counter()
        current_prompt, is_valid, risk_score = scanner.scan(current_prompt)
        scanner_results.append(
            {
                "scanner": type(scanner).__name__,
                "is_valid": is_valid,
                "risk_score": risk_score,
                "latency_ms": round((time.perf_counter() - start_time) * 1000.0, 2),
            }
        )

    return current_prompt, scanner_results


def run_output_pipeline(
    scanners: Sequence[Any], prompt: str, output: str
) -> tuple[str, list[dict[str, Any]]]:
    current_output = output
    scanner_results: list[dict[str, Any]] = []
    for scanner in scanners:
        start_time = time.perf_counter()
        current_output, is_valid, risk_score = scanner.scan(prompt, current_output)
        scanner_results.append(
            {
                "scanner": type(scanner).__name__,
                "is_valid": is_valid,
                "risk_score": risk_score,
                "latency_ms": round((time.perf_counter() - start_time) * 1000.0, 2),
            }
        )

    return current_output, scanner_results


@dataclass
class Sample:
    timestamp_s: float
    rss_bytes: int | None
    cpu_time_seconds: float | None


class ResourceSampler:
    def __init__(self, interval_seconds: float):
        self.interval_seconds = interval_seconds
        self.samples: list[Sample] = []
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._process = psutil.Process() if psutil is not None else None
        self._start_process_time = 0.0
        self._end_process_time = 0.0
        self._start_wall_time = 0.0
        self._end_wall_time = 0.0

    def _capture_sample(self):
        cpu_time_seconds = None
        if self._process is not None:
            cpu_times = self._process.cpu_times()
            cpu_time_seconds = float(cpu_times.user + cpu_times.system)
        self.samples.append(
            Sample(
                timestamp_s=time.perf_counter(),
                rss_bytes=_get_rss_bytes(),
                cpu_time_seconds=cpu_time_seconds,
            )
        )

    def _run(self):
        while not self._stop_event.wait(self.interval_seconds):
            self._capture_sample()

    def start(self):
        self.samples = []
        self._stop_event.clear()
        self._start_process_time = time.process_time()
        self._start_wall_time = time.perf_counter()
        self._capture_sample()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> dict[str, Any]:
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join()
        self._capture_sample()
        self._end_process_time = time.process_time()
        self._end_wall_time = time.perf_counter()

        rss_values = [sample.rss_bytes for sample in self.samples if sample.rss_bytes is not None]
        cpu_values = []
        for previous_sample, current_sample in zip(self.samples, self.samples[1:]):
            if previous_sample.cpu_time_seconds is None or current_sample.cpu_time_seconds is None:
                continue
            wall_delta = current_sample.timestamp_s - previous_sample.timestamp_s
            if wall_delta <= 0:
                continue
            cpu_delta = current_sample.cpu_time_seconds - previous_sample.cpu_time_seconds
            cpu_values.append(round((cpu_delta / wall_delta) * 100.0, 2))
        wall_duration = self._end_wall_time - self._start_wall_time
        cpu_time_seconds = self._end_process_time - self._start_process_time
        return {
            "samples": len(self.samples),
            "rss_peak_mb": _bytes_to_mb(max(rss_values)) if rss_values else None,
            "rss_min_mb": _bytes_to_mb(min(rss_values)) if rss_values else None,
            "cpu_percent_avg": round(sum(cpu_values) / len(cpu_values), 2) if cpu_values else None,
            "cpu_percent_peak": round(max(cpu_values), 2) if cpu_values else None,
            "cpu_percent_avg_estimate": round((cpu_time_seconds / wall_duration) * 100.0, 2)
            if wall_duration > 0
            else None,
            "cpu_cores_avg_estimate": _cpu_cores_from_percent(
                round((cpu_time_seconds / wall_duration) * 100.0, 2) if wall_duration > 0 else None
            ),
            "cpu_cores_peak": _cpu_cores_from_percent(round(max(cpu_values), 2) if cpu_values else None),
            "cpu_time_seconds": round(cpu_time_seconds, 3),
            "process_peak_rss_mb": _bytes_to_mb(_get_peak_rss_bytes()),
        }


def _format_value(value: Any) -> str:
    if value is None:
        return "n/a"

    if isinstance(value, bool):
        return "true" if value else "false"

    return str(value)


def render_markdown_report(result: dict[str, Any]) -> str:
    lines: list[str] = []
    configuration = result["configuration"]
    machine = result["machine"]
    load = result["load"]
    cold = result["cold_request"]
    steady_state = result["steady_state"]

    lines.append("# LLM Guard Resource Benchmark")
    lines.append("")
    lines.append("## Configuration")
    lines.append("")
    lines.append(f"- Type: {_format_value(configuration['type'])}")
    lines.append(f"- Scanners: {', '.join(load['scanners'])}")
    lines.append(f"- Concurrency: {', '.join(str(level) for level in configuration['concurrency'])}")
    lines.append(
        f"- Iterations per concurrency: {_format_value(configuration['iterations_per_concurrency'])}"
    )
    lines.append(f"- Warmup requests: {_format_value(configuration['warmup_requests'])}")
    lines.append(f"- Payload size chars: {_format_value(load['payload_size_chars'])}")
    lines.append(f"- Use ONNX: {_format_value(load['use_onnx'])}")
    lines.append(
        "- Thread settings: "
        f"torch={_format_value(configuration['thread_settings']['torch_num_threads'])}, "
        f"interop={_format_value(configuration['thread_settings']['torch_num_interop_threads'])}, "
        f"OMP={_format_value(configuration['thread_settings']['omp_num_threads'])}, "
        f"MKL={_format_value(configuration['thread_settings']['mkl_num_threads'])}"
    )
    lines.append("")
    lines.append("## Machine")
    lines.append("")
    lines.append(f"- Hostname: {_format_value(machine['hostname'])}")
    lines.append(f"- Platform: {_format_value(machine['platform'])}")
    lines.append(f"- Python: {_format_value(machine['python_version'])}")
    lines.append(f"- Logical CPU count: {_format_value(machine['cpu_count_logical'])}")
    lines.append(f"- Total memory MB: {_format_value(machine['total_memory_mb'])}")
    lines.append(f"- Torch: {_format_value(machine['torch_version'])}")
    lines.append(f"- CUDA available: {_format_value(machine['cuda_available'])}")
    if machine["cuda_device"] is not None:
        lines.append(f"- CUDA device: {_format_value(machine['cuda_device'])}")
    lines.append("")
    lines.append("## Load And Cold Start")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("| --- | --- |")
    lines.append(f"| Load time ms | {_format_value(load['load_time_ms'])} |")
    lines.append(f"| RSS before load MB | {_format_value(load['rss_before_load_mb'])} |")
    lines.append(f"| RSS after load MB | {_format_value(load['rss_after_load_mb'])} |")
    lines.append(f"| RSS delta after load MB | {_format_value(load['rss_delta_after_load_mb'])} |")
    lines.append(f"| Cold request latency ms | {_format_value(cold['latency_ms'])} |")
    lines.append(
        f"| Cold request RSS peak MB | {_format_value(cold['resources']['rss_peak_mb'])} |"
    )
    lines.append(
        f"| Cold request CPU avg estimate % | {_format_value(cold['resources']['cpu_percent_avg_estimate'])} |"
    )
    lines.append(
        f"| Cold request CPU cores avg estimate | {_format_value(cold['resources']['cpu_cores_avg_estimate'])} |"
    )
    lines.append("")
    lines.append("## Steady State")
    lines.append("")
    lines.append(
        "| Concurrency | Throughput RPS | Avg ms | P95 ms | Max ms | RSS peak MB | CPU avg % | CPU avg cores | CPU peak % | CPU peak cores |"
    )
    lines.append(
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"
    )
    for item in steady_state:
        resources = item["resources"]
        lines.append(
            f"| {_format_value(item['concurrency'])} | {_format_value(item['throughput_rps'])} | {_format_value(item['latency_avg_ms'])} | {_format_value(item['latency_p95_ms'])} | {_format_value(item['latency_max_ms'])} | {_format_value(resources['rss_peak_mb'])} | {_format_value(resources['cpu_percent_avg_estimate'])} | {_format_value(resources['cpu_cores_avg_estimate'])} | {_format_value(resources['cpu_percent_peak'])} | {_format_value(resources['cpu_cores_peak'])} |"
        )

    return "\n".join(lines) + "\n"


def render_csv_report(result: dict[str, Any]) -> str:
    machine = result["machine"]
    configuration = result["configuration"]
    load = result["load"]
    cold = result["cold_request"]

    rows = [
        [
            "type",
            "scanners",
            "concurrency",
            "iterations_per_concurrency",
            "warmup_requests",
            "torch_num_threads",
            "torch_num_interop_threads",
            "omp_num_threads",
            "mkl_num_threads",
            "payload_size_chars",
            "load_time_ms",
            "rss_after_load_mb",
            "rss_delta_after_load_mb",
            "cold_request_latency_ms",
            "cold_request_rss_peak_mb",
            "cold_request_cpu_avg_percent",
            "cold_request_cpu_avg_cores",
            "throughput_rps",
            "latency_avg_ms",
            "latency_p95_ms",
            "latency_max_ms",
            "rss_peak_mb",
            "cpu_avg_percent",
            "cpu_avg_cores",
            "cpu_peak_percent",
            "cpu_peak_cores",
            "cpu_count_logical",
            "total_memory_mb",
            "torch_version",
            "cuda_available",
        ]
    ]

    for item in result["steady_state"]:
        resources = item["resources"]
        rows.append(
            [
                configuration["type"],
                ";".join(load["scanners"]),
                item["concurrency"],
                configuration["iterations_per_concurrency"],
                configuration["warmup_requests"],
                configuration["thread_settings"]["torch_num_threads"],
                configuration["thread_settings"]["torch_num_interop_threads"],
                configuration["thread_settings"]["omp_num_threads"],
                configuration["thread_settings"]["mkl_num_threads"],
                load["payload_size_chars"],
                load["load_time_ms"],
                load["rss_after_load_mb"],
                load["rss_delta_after_load_mb"],
                cold["latency_ms"],
                cold["resources"]["rss_peak_mb"],
                cold["resources"]["cpu_percent_avg_estimate"],
                cold["resources"]["cpu_cores_avg_estimate"],
                item["throughput_rps"],
                item["latency_avg_ms"],
                item["latency_p95_ms"],
                item["latency_max_ms"],
                resources["rss_peak_mb"],
                resources["cpu_percent_avg_estimate"],
                resources["cpu_cores_avg_estimate"],
                resources["cpu_percent_peak"],
                resources["cpu_cores_peak"],
                machine["cpu_count_logical"],
                machine["total_memory_mb"],
                machine["torch_version"],
                machine["cuda_available"],
            ]
        )

    return "\n".join(
        ",".join(str(cell) for cell in row)
        for row in rows
    ) + "\n"


def benchmark_cold_request(benchmark_once: Callable[[], Any]) -> dict[str, Any]:
    sampler = ResourceSampler(interval_seconds=0.01)
    sampler.start()
    start_time = time.perf_counter()
    _, scanner_results = benchmark_once()
    latency_ms = round((time.perf_counter() - start_time) * 1000.0, 2)
    resource_stats = sampler.stop()

    return {
        "latency_ms": latency_ms,
        "scanner_results": scanner_results,
        "resources": resource_stats,
    }


def warmup(benchmark_once: Callable[[], Any], warmup_requests: int):
    for _ in range(max(0, warmup_requests)):
        benchmark_once()


def benchmark_concurrency(
    benchmark_once: Callable[[], Any],
    concurrency: int,
    iterations_per_concurrency: int,
    sample_interval_seconds: float,
) -> dict[str, Any]:
    total_requests = concurrency * iterations_per_concurrency
    latencies_ms: list[float] = []
    scanner_result_template: list[dict[str, Any]] = []

    def run_single_request() -> None:
        start_time = time.perf_counter()
        _, scanner_results = benchmark_once()
        latency_ms = round((time.perf_counter() - start_time) * 1000.0, 2)
        latencies_ms.append(latency_ms)
        if not scanner_result_template:
            scanner_result_template.extend(scanner_results)

    sampler = ResourceSampler(interval_seconds=sample_interval_seconds)
    sampler.start()
    wall_start = time.perf_counter()
    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = [executor.submit(run_single_request) for _ in range(total_requests)]
        for future in concurrent.futures.as_completed(futures):
            future.result()
    wall_time_s = time.perf_counter() - wall_start
    resource_stats = sampler.stop()

    return {
        "concurrency": concurrency,
        "total_requests": total_requests,
        "wall_time_ms": round(wall_time_s * 1000.0, 2),
        "throughput_rps": round(total_requests / wall_time_s, 2) if wall_time_s > 0 else 0.0,
        "latency_avg_ms": _mean(latencies_ms),
        "latency_p50_ms": _percentile(latencies_ms, 50),
        "latency_p90_ms": _percentile(latencies_ms, 90),
        "latency_p95_ms": _percentile(latencies_ms, 95),
        "latency_p99_ms": _percentile(latencies_ms, 99),
        "latency_max_ms": round(max(latencies_ms), 2) if latencies_ms else 0.0,
        "resources": resource_stats,
        "scanner_results_example": scanner_result_template,
    }


def resolve_payload(args: argparse.Namespace) -> tuple[str, str | None]:
    common = _common_module()
    if args.type == "input":
        if args.prompt_file is not None:
            return _read_text(args.prompt_file), None

        return common.get_default_input_prompt(args.scanners[0]), None

    if args.prompt_file is not None:
        prompt = _read_text(args.prompt_file)
    else:
        prompt, _ = common.get_default_output_payload(args.scanners[0])

    if args.output_file is not None:
        output = _read_text(args.output_file)
    else:
        _, output = common.get_default_output_payload(args.scanners[0])

    return prompt, output


def build_pipeline(args: argparse.Namespace, prompt: str, output: str | None) -> tuple[Callable[[], Any], dict[str, Any]]:
    _torch_module()
    common = _common_module()
    rss_before_load = _get_rss_bytes()
    build_started_at = time.perf_counter()

    if args.type == "input":
        scanners = common.build_input_scanners(args.scanners, use_onnx=args.use_onnx)
        benchmark_once = lambda: run_input_pipeline(scanners, prompt)
        payload_size = len(prompt)
    else:
        assert output is not None
        scanners = common.build_output_scanners(args.scanners, use_onnx=args.use_onnx)
        benchmark_once = lambda: run_output_pipeline(scanners, prompt, output)
        payload_size = len(output)

    load_time_ms = round((time.perf_counter() - build_started_at) * 1000.0, 2)
    rss_after_load = _get_rss_bytes()

    return benchmark_once, {
        "scanner_count": len(scanners),
        "scanners": args.scanners,
        "payload_size_chars": payload_size,
        "use_onnx": args.use_onnx,
        "load_time_ms": load_time_ms,
        "rss_before_load_mb": _bytes_to_mb(rss_before_load),
        "rss_after_load_mb": _bytes_to_mb(rss_after_load),
        "rss_delta_after_load_mb": _bytes_to_mb(
            None
            if rss_before_load is None or rss_after_load is None
            else rss_after_load - rss_before_load
        ),
    }


def main():
    args = parse_args()
    apply_runtime_thread_settings(args)
    prompt, output = resolve_payload(args)
    benchmark_once, load_stats = build_pipeline(args, prompt, output)

    cold_request = benchmark_cold_request(benchmark_once)
    warmup(benchmark_once, args.warmup_requests)
    concurrency_results = [
        benchmark_concurrency(
            benchmark_once,
            concurrency=concurrency,
            iterations_per_concurrency=args.iterations_per_concurrency,
            sample_interval_seconds=args.sample_interval_ms / 1000.0,
        )
        for concurrency in args.concurrency
    ]

    result = {
        "machine": _build_machine_info(),
        "configuration": {
            "type": args.type,
            "concurrency": args.concurrency,
            "iterations_per_concurrency": args.iterations_per_concurrency,
            "warmup_requests": args.warmup_requests,
            "sample_interval_ms": args.sample_interval_ms,
            "thread_settings": _thread_settings(args),
        },
        "load": load_stats,
        "cold_request": cold_request,
        "steady_state": concurrency_results,
    }

    rendered = json.dumps(result, indent=2)
    print(rendered)

    if args.json_output is not None:
        args.json_output.write_text(rendered + "\n", encoding="utf-8")

    if args.markdown_output is not None:
        args.markdown_output.write_text(render_markdown_report(result), encoding="utf-8")

    if args.csv_output is not None:
        args.csv_output.write_text(render_csv_report(result), encoding="utf-8")


if __name__ == "__main__":
    main()