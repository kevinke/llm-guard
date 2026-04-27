# LLM Guard API

[Documentation](https://protectai.github.io/llm-guard/api/overview/)

## CPU Demo Workflow

This branch adds a local CPU demo flow that avoids downloading spaCy assets during API startup and lets you preload the ONNX models used by the demo scanners.

### Files

- `config/scanners.demo.cpu.yml` uses a minimal demo scanner set and reads models from `/models`.
- `docker-compose.demo.cpu.yml` starts the API with the demo scanner config mounted read-only.
- `scripts/download_onnx_models.py` downloads the ONNX snapshots needed by the demo into `./models`.

### Run the demo

From `llm_guard_api/`:

```sh
python scripts/download_onnx_models.py --output-dir ./models
docker compose -f docker-compose.demo.cpu.yml up --build
```

The API will start on `http://localhost:8000` with `AUTH_TOKEN=demo-token`.

### Notes

- The demo compose file mounts `./models` into the container as `/models`, so the model download step is expected before first startup.
- After the models are downloaded once, the demo no longer depends on runtime model downloads for the configured scanners.
- The default API config is still `config/scanners.yml`. The CPU demo uses the separate `config/scanners.demo.cpu.yml` file on purpose.
