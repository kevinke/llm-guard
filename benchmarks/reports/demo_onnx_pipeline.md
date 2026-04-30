# LLM Guard Resource Benchmark

## Configuration

- Type: input
- Scanners: Anonymize, PromptInjection, TokenLimit
- Concurrency: 1, 2, 5
- Iterations per concurrency: 5
- Warmup requests: 2
- Payload size chars: 317
- Use ONNX: false
- Thread settings: torch=n/a, interop=n/a, OMP=n/a, MKL=n/a

## Machine

- Hostname: DESKTOP-KK-WJ15X
- Platform: Linux-6.6.87.2-microsoft-standard-WSL2-x86_64-with-glibc2.39
- Python: 3.12.3
- Logical CPU count: 16
- Total memory MB: 11852.19
- Torch: 2.11.0+cu130
- CUDA available: false

## Load And Cold Start

| Metric | Value |
| --- | --- |
| Load time ms | 5480.8 |
| RSS before load MB | 676.93 |
| RSS after load MB | 988.27 |
| RSS delta after load MB | 311.34 |
| Cold request latency ms | 1423.66 |
| Cold request RSS peak MB | 1692.52 |
| Cold request CPU avg estimate % | 343.31 |
| Cold request CPU cores avg estimate | 3.43 |

## Steady State

| Concurrency | Throughput RPS | Avg ms | P95 ms | Max ms | RSS peak MB | CPU avg % | CPU avg cores | CPU peak % | CPU peak cores |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 2.92 | 341.73 | 348.77 | 350.06 | 1729.49 | 695.69 | 6.96 | 774.84 | 7.75 |
| 2 | 2.79 | 715.62 | 722.37 | 722.86 | 1773.59 | 609.19 | 6.09 | 732.91 | 7.33 |
| 5 | 3.28 | 1502.51 | 1733.64 | 1741.64 | 1890.21 | 710.11 | 7.1 | 939.06 | 9.39 |
