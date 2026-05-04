# Optimization Strategies

## ONNX Runtime

ONNX (Open Neural Network Exchange) provides a high-performance inference engine for machine learning models, allowing for faster and more efficient model execution. If an ONNX version of a model is available, it can serve as a substantial optimization for the scanner.

To leverage ONNX Runtime, you must first install the appropriate package:

```sh
pip install llm-guard[onnxruntime] # for CPU instances
pip install llm-guard[onnxruntime-gpu] # for GPU instances
```

Activate ONNX by initializing your scanner with the use_onnx parameter set to True:

```python
scanner = Code(languages=["PHP"], use_onnx=True)
```

In case you have issues installing the ONNX Runtime package, you can check the [official documentation](https://onnxruntime.ai/docs/install/).

## ONNX Runtime with Quantization

Although not built-in in the library, you can use quantized or optimized versions of the models.
However, that doesn't always lead to better latency but can reduce the model size.

## Enabling Low CPU/Memory Usage

To minimize CPU and memory usage:

```python
from llm_guard.input_scanners.code import Code, DEFAULT_MODEL

DEFAULT_MODEL.kwargs["low_cpu_mem_usage"] = True
scanner = Code(languages=["PHP"], model=DEFAULT_MODEL)
```

For an in-depth understanding of this feature and its impact on large model handling, refer to the detailed [Large Model Loading Documentation](https://huggingface.co/docs/transformers/main_classes/model#large-model-loading).

Alternatively, quantization can be used to reduce the model size and memory usage.

## Local Resource Benchmarking

If you want to estimate whether a scanner or scanner pipeline can run on a personal PC, use the local benchmark CLI:

```sh
python benchmarks/resource_benchmark.py input PromptInjection --concurrency 1 2 5
```

You can benchmark a pipeline by passing multiple scanners in order:

```sh
python benchmarks/resource_benchmark.py input PromptInjection Toxicity --concurrency 1 2 5
```

For output scanners:

```sh
python benchmarks/resource_benchmark.py output Sensitive --concurrency 1 2 5
```

The report includes:

- model load time and RSS delta after loading scanners
- cold request latency
- steady-state latency percentiles under each concurrency level
- throughput in requests per second
- sampled process RSS and CPU usage during the run

You can also export the same run as JSON, Markdown, or CSV:

```sh
python benchmarks/resource_benchmark.py input PromptInjection \
	--json-output benchmarks/reports/prompt_injection.json \
	--markdown-output benchmarks/reports/prompt_injection.md \
	--csv-output benchmarks/reports/prompt_injection.csv
```

If you want to cap CPU usage on a personal PC, you can limit the runtime threads used by PyTorch and BLAS:

```sh
python benchmarks/resource_benchmark.py input Anonymize PromptInjection Toxicity \
	--torch-num-threads 4 \
	--torch-num-interop-threads 1 \
	--omp-num-threads 4 \
	--mkl-num-threads 4
```

The report will include the thread settings so you can compare latency and CPU usage across runs.

If you want to benchmark your own traffic shape instead of the bundled examples, pass `--prompt-file` and `--output-file`.

## Use smaller models

For certain scanners, smaller model variants are available e.g. distilbert, bert-small, bert-tiny versions.
These models are designed for enhanced performance, offering reduced latency without significantly compromising accuracy or effectiveness.

## PyTorch hacks

To speed up warm compile times:

```python
import torch
torch.set_float32_matmul_precision('high')

import torch._inductor.config
torch._inductor.config.fx_graph_cache = True
```

## Streaming mode

To optimize the output scanning, you can analyze the output in chunks. In [OpenAI](./openai.md) guide, we demonstrate how to use LLM Guard to protect OpenAI client with streaming.
