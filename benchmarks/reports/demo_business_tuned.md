# LLM Guard Resource Benchmark

## Configuration

- Type: input
- Scanners: Anonymize, PromptInjection, Toxicity, BanTopics, Secrets, TokenLimit, Regex
- Concurrency: 1, 2, 5
- Iterations per concurrency: 1
- Warmup requests: 0
- Payload size chars: 161
- Use ONNX: false
- Thread settings: torch=4, interop=1, OMP=4, MKL=4

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
| Load time ms | 4096.11 |
| RSS before load MB | 678.92 |
| RSS after load MB | 1485.89 |
| RSS delta after load MB | 806.97 |
| Cold request latency ms | 1732.66 |
| Cold request RSS peak MB | 2539.68 |
| Cold request CPU avg estimate % | 353.38 |
| Cold request CPU cores avg estimate | 3.53 |

## Steady State

| Concurrency | Throughput RPS | Avg ms | P95 ms | Max ms | RSS peak MB | CPU avg % | CPU avg cores | CPU peak % | CPU peak cores |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 0.69 | 1448.15 | 1448.15 | 1448.15 | 2585.02 | 372.86 | 3.73 | 413.34 | 4.13 |
| 2 | 0.94 | 2118.01 | 2127.01 | 2128.01 | 2641.12 | 735.31 | 7.35 | 813.9 | 8.14 |
| 5 | 1.23 | 4012.59 | 4058.4 | 4058.77 | 2776.66 | 946.62 | 9.47 | 1278.3 | 12.78 |
