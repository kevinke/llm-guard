#!/usr/bin/env python3

from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import Sequence

from huggingface_hub import snapshot_download


MODELS = [
    {
        "name": "anonymize_ai4privacy_v2",
        "repo_id": "Isotonic/deberta-v3-base_finetuned_ai4privacy_v2",
        "revision": "9ea992753ab2686be4a8f64605ccc7be197ad794",
    },
    {
        "name": "prompt_injection_v2",
        "repo_id": "ProtectAI/deberta-v3-base-prompt-injection-v2",
        "revision": "89b085cd330414d3e7d9dd787870f315957e1e9f",
    },
]


DEFAULT_MINIMAL_ALLOW_PATTERNS = [
    "onnx/*",
    "*.json",
    "*.model",
    "*.txt",
]


def _resolve_allow_patterns(
    allow_patterns: Sequence[str],
    full_snapshot: bool,
) -> list[str] | None:
    if allow_patterns:
        return list(allow_patterns)

    if full_snapshot:
        return None

    # Faster default: fetch ONNX + tokenizer/config artifacts only.
    return DEFAULT_MINIMAL_ALLOW_PATTERNS.copy()


def _resolve_ignore_patterns(ignore_patterns: Sequence[str]) -> list[str] | None:
    if not ignore_patterns:
        return None

    return list(ignore_patterns)


def _apply_environment(
    endpoint: str | None,
    download_timeout: int,
    disable_hf_transfer: bool,
) -> None:
    if endpoint:
        os.environ["HF_ENDPOINT"] = endpoint

    os.environ["HF_HUB_DOWNLOAD_TIMEOUT"] = str(download_timeout)

    if disable_hf_transfer:
        os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "0"
    else:
        os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "1"


def download_model(
    repo_id: str,
    revision: str,
    target_dir: Path,
    *,
    max_workers: int,
    etag_timeout: float,
    endpoint: str | None,
    allow_patterns: list[str] | None,
    ignore_patterns: list[str] | None,
) -> None:
    target_dir.mkdir(parents=True, exist_ok=True)

    # Snapshot download supports concurrent workers and file filters for faster pulls.
    snapshot_download(
        repo_id=repo_id,
        revision=revision,
        local_dir=str(target_dir),
        max_workers=max_workers,
        etag_timeout=etag_timeout,
        endpoint=endpoint,
        allow_patterns=allow_patterns,
        ignore_patterns=ignore_patterns,
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Download ONNX model snapshots for local CPU demo."
    )
    parser.add_argument(
        "--output-dir",
        default="./models",
        help="Directory where model folders will be created.",
    )
    parser.add_argument(
        "--max-workers",
        type=int,
        default=16,
        help="Parallel file download workers for snapshot_download (default: 16).",
    )
    parser.add_argument(
        "--etag-timeout",
        type=float,
        default=30,
        help="Metadata timeout in seconds for ETag checks (default: 30).",
    )
    parser.add_argument(
        "--download-timeout",
        type=int,
        default=120,
        help="HF_HUB_DOWNLOAD_TIMEOUT in seconds (default: 120).",
    )
    parser.add_argument(
        "--endpoint",
        default=None,
        help="Optional Hugging Face endpoint or mirror, e.g. https://hf-mirror.com",
    )
    parser.add_argument(
        "--disable-hf-transfer",
        action="store_true",
        help="Disable hf_transfer acceleration even if available.",
    )
    parser.add_argument(
        "--allow-pattern",
        action="append",
        default=[],
        help="File pattern to include. Repeatable. Defaults to a fast minimal set.",
    )
    parser.add_argument(
        "--ignore-pattern",
        action="append",
        default=[],
        help="File pattern to exclude. Repeatable.",
    )
    parser.add_argument(
        "--full-snapshot",
        action="store_true",
        help="Download full repository snapshot (disable default minimal filter).",
    )
    args = parser.parse_args()

    if args.max_workers <= 0:
        raise ValueError("--max-workers must be greater than 0")

    if args.etag_timeout <= 0:
        raise ValueError("--etag-timeout must be greater than 0")

    if args.download_timeout <= 0:
        raise ValueError("--download-timeout must be greater than 0")

    base_dir = Path(args.output_dir).resolve()
    base_dir.mkdir(parents=True, exist_ok=True)

    allow_patterns = _resolve_allow_patterns(args.allow_pattern, args.full_snapshot)
    ignore_patterns = _resolve_ignore_patterns(args.ignore_pattern)

    _apply_environment(args.endpoint, args.download_timeout, args.disable_hf_transfer)

    print(f"Downloading models to: {base_dir}")
    print(
        "Settings: "
        f"max_workers={args.max_workers}, etag_timeout={args.etag_timeout}, "
        f"download_timeout={args.download_timeout}, "
        f"endpoint={os.environ.get('HF_ENDPOINT', 'default')}, "
        f"hf_transfer={os.environ.get('HF_HUB_ENABLE_HF_TRANSFER')}, "
        f"allow_patterns={allow_patterns if allow_patterns else 'FULL_SNAPSHOT'}"
    )

    for model in MODELS:
        model_dir = base_dir / model["name"]
        print(
            f"- {model['name']}: {model['repo_id']} @ {model['revision']} -> {model_dir}"
        )
        download_model(
            model["repo_id"],
            model["revision"],
            model_dir,
            max_workers=args.max_workers,
            etag_timeout=args.etag_timeout,
            endpoint=args.endpoint,
            allow_patterns=allow_patterns,
            ignore_patterns=ignore_patterns,
        )

    print("Done. ONNX demo models are ready.")


if __name__ == "__main__":
    main()
