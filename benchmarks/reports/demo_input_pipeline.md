# LLM Guard Resource Benchmark

## Configuration

- Type: input
- Scanners: Anonymize, PromptInjection, Toxicity, BanTopics, Secrets, TokenLimit, Regex
- Concurrency: 1, 2, 5
- Iterations per concurrency: 2
- Warmup requests: 1
- Payload size chars: 317
- Use ONNX: false

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
| Load time ms | 179659.18 |
| RSS before load MB | 678.59 |
| RSS after load MB | 1608.51 |
| RSS delta after load MB | 929.92 |
| Cold request latency ms | 1550.13 |
| Cold request RSS peak MB | 2677.26 |
| Cold request CPU avg estimate % | 623.06 |
| Cold request CPU cores avg estimate | 6.23 |

## Steady State

| Concurrency | Throughput RPS | Avg ms | P95 ms | Max ms | RSS peak MB | CPU avg % | CPU avg cores | CPU peak % | CPU peak cores |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 1.09 | 918.62 | 992.31 | 1000.5 | 2721.39 | 785.12 | 7.85 | 14585.6 | 145.86 |
| 2 | 1.29 | 1535.81 | 1561.48 | 1562.21 | 2753.23 | 711.89 | 7.12 | 1056.8 | 10.57 |
| 5 | 1.39 | 3544.89 | 3696.73 | 3711.5 | 2962.98 | 858.5 | 8.59 | 1265.2 | 12.65 |
