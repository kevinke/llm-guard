# LLM Guard Resource Benchmark

## Configuration

- Type: input
- Scanners: Anonymize, PromptInjection, Toxicity, BanTopics, Secrets, TokenLimit, Regex
- Concurrency: 1, 2, 5
- Iterations per concurrency: 1
- Warmup requests: 0
- Payload size chars: 161
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
| Load time ms | 5881.38 |
| RSS before load MB | 678.71 |
| RSS after load MB | 1486.38 |
| RSS delta after load MB | 807.67 |
| Cold request latency ms | 1278.67 |
| Cold request RSS peak MB | 2553.55 |
| Cold request CPU avg estimate % | 726.64 |
| Cold request CPU cores avg estimate | 7.27 |

## Steady State

| Concurrency | Throughput RPS | Avg ms | P95 ms | Max ms | RSS peak MB | CPU avg % | CPU avg cores | CPU peak % | CPU peak cores |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 0.93 | 1079.91 | 1079.91 | 1079.91 | 2591.96 | 786.41 | 7.86 | 832.54 | 8.33 |
| 2 | 1.06 | 1890.05 | 1891.54 | 1891.7 | 2665.44 | 778.09 | 7.78 | 1036.83 | 10.37 |
| 5 | 1.26 | 3949.59 | 3974.07 | 3974.84 | 2827.15 | 1006.05 | 10.06 | 1377.41 | 13.77 |
