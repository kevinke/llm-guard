import argparse
import importlib
import json
import timeit
from pathlib import Path
from typing import Dict, List

import numpy

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in __import__("sys").path:
    __import__("sys").path.insert(0, str(REPO_ROOT))


def _common_module():
    return importlib.import_module("benchmarks.common")


def benchmark_input_scanner(scanner_name: str, repeat_times: int, use_onnx: bool) -> (List, int):
    common = _common_module()
    build_input_scanner = common.build_input_scanner
    get_default_input_prompt = common.get_default_input_prompt
    scanner = build_input_scanner(scanner_name, use_onnx=use_onnx)

    prompt = get_default_input_prompt(scanner_name)

    latency_list = timeit.repeat(lambda: scanner.scan(prompt), number=1, repeat=repeat_times)

    return latency_list, len(prompt)


def benchmark_output_scanner(scanner_name: str, repeat_times: int, use_onnx: bool) -> (List, int):
    common = _common_module()
    build_output_scanner = common.build_output_scanner
    get_default_output_payload = common.get_default_output_payload
    scanner = build_output_scanner(scanner_name, use_onnx=use_onnx)

    prompt, output = get_default_output_payload(scanner_name)

    latency_list = timeit.repeat(
        lambda: scanner.scan(prompt, output), number=1, repeat=repeat_times
    )

    return latency_list, len(output)


def get_output(scanner_name: str, scanner_type: str, latency_list, input_length: int) -> Dict:
    latency_ms = sum(latency_list) / float(len(latency_list)) * 1000.0
    latency_variance = numpy.var(latency_list, dtype=numpy.float64) * 1000.0
    throughput = input_length * (1000.0 / latency_ms)

    return {
        "scanner": scanner_name,
        "scanner Type": scanner_type,
        "input_length": input_length,
        "test_times": len(latency_list),
        "latency_variance": f"{latency_variance:.2f}",
        "latency_90_percentile": f"{numpy.percentile(latency_list, 90) * 1000.0:.2f}",
        "latency_95_percentile": f"{numpy.percentile(latency_list, 95) * 1000.0:.2f}",
        "latency_99_percentile": f"{numpy.percentile(latency_list, 99) * 1000.0:.2f}",
        "average_latency_ms": f"{latency_ms:.2f}",
        "QPS": f"{throughput:.2f}",
    }


def main():
    parser = argparse.ArgumentParser(description="Benchmark scanners in llm-guard library.")
    parser.add_argument(
        "type", choices=["input", "output"], help="Type of the scanner to benchmark."
    )
    parser.add_argument("scanner", type=str, help="Name of the scanner class to benchmark.")
    parser.add_argument(
        "--repeat",
        type=int,
        default=5,
        help="Number of times to repeat the benchmark.",
    )
    parser.add_argument(
        "--use-onnx",
        type=bool,
        default=False,
        help="Whether to use ONNX for inference, when possible.",
    )

    args = parser.parse_args()

    if args.type == "input":
        latency_list, length = benchmark_input_scanner(args.scanner, args.repeat, args.use_onnx)
    elif args.type == "output":
        latency_list, length = benchmark_output_scanner(args.scanner, args.repeat, args.use_onnx)
    else:
        raise ValueError("Type is not found")

    # Structured Output
    output = get_output(args.scanner, args.type, latency_list, length)
    print(json.dumps(output, indent=4))


if __name__ == "__main__":
    main()
