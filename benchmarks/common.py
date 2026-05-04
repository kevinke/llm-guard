from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Tuple

import torch

from llm_guard import input_scanners, output_scanners
from llm_guard.input_scanners.anonymize_helpers import DEBERTA_AI4PRIVACY_v2_CONF
from llm_guard.input_scanners.ban_substrings import MatchType as BanSubstringsMatchType
from llm_guard.input_scanners.base import Scanner as InputScanner
from llm_guard.output_scanners.base import Scanner as OutputScanner
from llm_guard.vault import Vault

torch.set_float32_matmul_precision("high")

import torch._inductor.config

torch._inductor.config.fx_graph_cache = True

BENCHMARKS_DIR = Path(__file__).resolve().parent

vault = Vault()


def build_input_scanner(scanner_name: str, use_onnx: bool) -> InputScanner:
    if scanner_name == "Anonymize":
        return input_scanners.Anonymize(
            vault=vault, use_onnx=use_onnx, recognizer_conf=DEBERTA_AI4PRIVACY_v2_CONF
        )

    if scanner_name == "BanCode":
        return input_scanners.BanCode(use_onnx=use_onnx)

    if scanner_name == "BanCompetitors":
        return input_scanners.BanCompetitors(
            competitors=["Google", "Bing", "Yahoo"],
            threshold=0.5,
            use_onnx=use_onnx,
        )

    if scanner_name == "BanSubstrings":
        return input_scanners.BanSubstrings(
            substrings=["backdoor", "malware", "virus"],
            match_type=BanSubstringsMatchType.WORD,
        )

    if scanner_name == "BanTopics":
        return input_scanners.BanTopics(topics=["violence", "attack", "war"], use_onnx=use_onnx)

    if scanner_name == "Code":
        return input_scanners.Code(languages=["Java"], is_blocked=True, use_onnx=use_onnx)

    if scanner_name == "Gibberish":
        return input_scanners.Gibberish(use_onnx=use_onnx)

    if scanner_name == "InvisibleText":
        return input_scanners.InvisibleText()

    if scanner_name == "Language":
        return input_scanners.Language(valid_languages=["en", "es"], use_onnx=use_onnx)

    if scanner_name == "PromptInjection":
        return input_scanners.PromptInjection(use_onnx=use_onnx)

    if scanner_name == "Regex":
        return input_scanners.Regex(patterns=[r"Bearer [A-Za-z0-9-._~+/]+"])

    if scanner_name == "Secrets":
        return input_scanners.Secrets()

    if scanner_name == "Sentiment":
        return input_scanners.Sentiment()

    if scanner_name == "TokenLimit":
        return input_scanners.TokenLimit(limit=50)

    if scanner_name == "Toxicity":
        return input_scanners.Toxicity(use_onnx=use_onnx)

    raise ValueError(f"Input scanner not found: {scanner_name}")


def build_output_scanner(scanner_name: str, use_onnx: bool) -> OutputScanner:
    if scanner_name == "BanCode":
        return output_scanners.BanCode(use_onnx=use_onnx)

    if scanner_name == "BanCompetitors":
        return output_scanners.BanCompetitors(
            competitors=["Google", "Bing", "Yahoo"],
            threshold=0.5,
            use_onnx=use_onnx,
        )

    if scanner_name == "BanSubstrings":
        return output_scanners.BanSubstrings(
            substrings=["backdoor", "malware", "virus"],
            match_type=BanSubstringsMatchType.WORD,
        )

    if scanner_name == "BanTopics":
        return output_scanners.BanTopics(topics=["violence", "attack", "war"], use_onnx=use_onnx)

    if scanner_name == "Bias":
        return output_scanners.Bias(use_onnx=use_onnx)

    if scanner_name == "Code":
        return output_scanners.Code(languages=["Java"], is_blocked=True, use_onnx=use_onnx)

    if scanner_name == "Deanonymize":
        return output_scanners.Deanonymize(vault)

    if scanner_name == "JSON":
        return output_scanners.JSON()

    if scanner_name == "Language":
        return output_scanners.Language(valid_languages=["en", "es"], use_onnx=use_onnx)

    if scanner_name == "LanguageSame":
        return output_scanners.LanguageSame(use_onnx=use_onnx)

    if scanner_name == "MaliciousURLs":
        return output_scanners.MaliciousURLs(use_onnx=use_onnx)

    if scanner_name == "NoRefusal":
        return output_scanners.NoRefusal(use_onnx=use_onnx)

    if scanner_name == "NoRefusalLight":
        return output_scanners.NoRefusalLight(use_onnx=use_onnx)

    if scanner_name == "ReadingTime":
        return output_scanners.ReadingTime(max_time=0.5, truncate=True)

    if scanner_name == "FactualConsistency":
        return output_scanners.FactualConsistency(use_onnx=use_onnx)

    if scanner_name == "Gibberish":
        return output_scanners.Gibberish(use_onnx=use_onnx)

    if scanner_name == "Regex":
        return output_scanners.Regex(patterns=[r"Bearer [A-Za-z0-9-._~+/]+"])

    if scanner_name == "Relevance":
        return output_scanners.Relevance(use_onnx=use_onnx)

    if scanner_name == "Sensitive":
        return output_scanners.Sensitive(
            redact=True, use_onnx=use_onnx, recognizer_conf=DEBERTA_AI4PRIVACY_v2_CONF
        )

    if scanner_name == "Sentiment":
        return output_scanners.Sentiment()

    if scanner_name == "Toxicity":
        return output_scanners.Toxicity(use_onnx=use_onnx)

    if scanner_name == "URLReachability":
        return output_scanners.URLReachability()

    raise ValueError(f"Output scanner not found: {scanner_name}")


def build_input_scanners(scanner_names: List[str], use_onnx: bool) -> List[InputScanner]:
    return [build_input_scanner(scanner_name, use_onnx=use_onnx) for scanner_name in scanner_names]


def build_output_scanners(scanner_names: List[str], use_onnx: bool) -> List[OutputScanner]:
    return [build_output_scanner(scanner_name, use_onnx=use_onnx) for scanner_name in scanner_names]


@lru_cache(maxsize=None)
def get_input_test_data() -> Dict[str, str]:
    with BENCHMARKS_DIR.joinpath("input_examples.json").open("r") as file:
        return json.load(file)


@lru_cache(maxsize=None)
def get_output_test_data() -> Dict[str, Tuple[str, str]]:
    with BENCHMARKS_DIR.joinpath("output_examples.json").open("r") as file:
        data = json.load(file)

    return {key: tuple(value) for key, value in data.items()}


def get_default_input_prompt(scanner_name: str) -> str:
    return get_input_test_data()[scanner_name]


def get_default_output_payload(scanner_name: str) -> Tuple[str, str]:
    return get_output_test_data()[scanner_name]