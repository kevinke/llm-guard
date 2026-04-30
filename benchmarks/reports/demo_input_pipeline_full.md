# LLM Guard Resource Benchmark

## Configuration

- Type: input
- Scanners: Anonymize, PromptInjection, Toxicity, BanTopics, Secrets, TokenLimit, Regex
- Concurrency: 1, 2, 5
- Iterations per concurrency: 1
- Warmup requests: 0
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
| Load time ms | 3558.6 |
| RSS before load MB | 678.8 |
| RSS after load MB | 1485.28 |
| RSS delta after load MB | 806.47 |
| Cold request latency ms | 1070.71 |
| Cold request RSS peak MB | 2541.71 |
| Cold request CPU avg estimate % | 711.37 |
| Cold request CPU cores avg estimate | 7.11 |

## Steady State

| Concurrency | Throughput RPS | Avg ms | P95 ms | Max ms | RSS peak MB | CPU avg % | CPU avg cores | CPU peak % | CPU peak cores |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 1.13 | 885.0 | 885.0 | 885.0 | 2579.64 | 785.41 | 7.85 | 845.93 | 8.46 |
| 2 | 1.25 | 1586.5 | 1592.52 | 1593.19 | 2653.7 | 718.68 | 7.19 | 1046.32 | 10.46 |
| 5 | 1.46 | 3380.38 | 3410.12 | 3414.53 | 2791.79 | 917.23 | 9.17 | 1478.06 | 14.78 |
