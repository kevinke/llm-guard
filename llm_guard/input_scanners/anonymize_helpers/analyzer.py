import copy
import logging
import os
from pathlib import Path

import spacy
from presidio_analyzer import (
    AnalyzerEngine,
    EntityRecognizer,
    Pattern,
    PatternRecognizer,
    RecognizerRegistry,
)
from presidio_analyzer.context_aware_enhancers import LemmaContextAwareEnhancer
from presidio_analyzer.nlp_engine import NlpEngine, NlpEngineProvider
from spacy.cli import download  # type: ignore

from .ner_mapping import NERConfig
from .predefined_recognizers import _get_predefined_recognizers
from .predefined_recognizers.zh import CustomPatternRecognizer
from .regex_patterns import RegexPattern
from .transformers_recognizer import TransformersRecognizer


LOGGER = logging.getLogger(__name__)


def _add_recognizers(
    registry: RecognizerRegistry,
    regex_groups: list[RegexPattern],
    custom_names: list[str],
    supported_languages: list[str] = ["en"],
) -> RecognizerRegistry:
    """
    Create a RecognizerRegistry and populate it with regex patterns and custom names.

    Parameters:
        regex_groups: List of regex patterns.
        custom_names: List of custom names to recognize.

    Returns:
        RecognizerRegistry: A RecognizerRegistry object loaded with regex and custom name recognizers.
    """

    for language in supported_languages:
        # custom recognizer per language
        if len(custom_names) > 0:
            custom_recognizer = PatternRecognizer

            if language == "zh":
                custom_recognizer = CustomPatternRecognizer

            registry.add_recognizer(
                custom_recognizer(
                    supported_entity="CUSTOM",
                    supported_language=language,
                    deny_list=custom_names,
                )
            )

        # predefined recognizers per language
        for _Recognizer in _get_predefined_recognizers(language):
            registry.add_recognizer(_Recognizer(supported_language=language))

    for pattern_data in regex_groups:
        languages = pattern_data["languages"] or ["en"]
        label = pattern_data["name"]
        reuse = pattern_data.get("reuse", False)

        patterns: list[Pattern] = list(
            map(
                lambda exp: Pattern(name=label, regex=exp, score=pattern_data["score"]),
                pattern_data.get("expressions", []) or [],
            )
        )

        for language in languages:
            if language not in supported_languages:
                continue

            if isinstance(reuse, dict):
                new_recognizer = copy.deepcopy(
                    registry.get_recognizers(language=reuse["language"], entities=[reuse["name"]])[
                        0
                    ]
                )
                new_recognizer.supported_language = language
                registry.add_recognizer(new_recognizer)
            else:
                registry.add_recognizer(
                    PatternRecognizer(
                        supported_entity=label,
                        supported_language=language,
                        patterns=patterns,
                        context=pattern_data["context"],
                    )
                )

    return registry


def _get_nlp_engine(languages: list[str]) -> NlpEngine:
    models = []
    skip_spacy_download = os.getenv("LLM_GUARD_SKIP_SPACY_DOWNLOAD", "0") == "1"

    for language in languages:
        model_name = f"{language}_core_web_sm"
        if not spacy.util.is_package(model_name):
            fallback_path = Path.home() / ".cache" / "llm_guard" / "spacy" / f"{language}_blank"

            if skip_spacy_download:
                if not fallback_path.exists():
                    fallback_path.parent.mkdir(parents=True, exist_ok=True)
                    spacy.blank(language).to_disk(fallback_path)

                LOGGER.warning(
                    "Skipping spaCy model download for '%s' (LLM_GUARD_SKIP_SPACY_DOWNLOAD=1). "
                    "Using blank fallback at '%s'.",
                    model_name,
                    fallback_path,
                )
                model_name = str(fallback_path)
                models.append({"lang_code": language, "model_name": model_name})
                continue

            try:
                # Use small spaCy model for better linguistic signals when available.
                download(model_name)
            except Exception as exc:
                # In restricted networks, model downloads can fail. Fallback to a local blank
                # pipeline so initialization does not fail hard for the whole scanner stack.
                if not fallback_path.exists():
                    fallback_path.parent.mkdir(parents=True, exist_ok=True)
                    spacy.blank(language).to_disk(fallback_path)

                LOGGER.warning(
                    "Failed to download spaCy model '%s'. Using blank fallback at '%s'. Error: %s",
                    model_name,
                    fallback_path,
                    exc,
                )
                model_name = str(fallback_path)

        models.append({"lang_code": language, "model_name": model_name})

    configuration = {"nlp_engine_name": "spacy", "models": models}

    return NlpEngineProvider(nlp_configuration=configuration).create_engine()


def get_transformers_recognizer(
    *,
    recognizer_conf: NERConfig,
    use_onnx: bool = False,
    supported_language: str = "en",
) -> EntityRecognizer:
    """
    This function loads a transformers recognizer given a recognizer configuration.

    Args:
        recognizer_conf: Configuration to recognize PII data.
        use_onnx: Whether to use the ONNX version of the model. Default is False.
        supported_language: The language to use for the recognizer. Default is "en".
    """
    model = recognizer_conf.get("DEFAULT_MODEL")
    supported_entities = recognizer_conf.get("PRESIDIO_SUPPORTED_ENTITIES")
    transformers_recognizer = TransformersRecognizer(
        model=model,
        supported_entities=supported_entities,
        supported_language=supported_language,
    )
    transformers_recognizer.load_transformer(
        use_onnx=use_onnx,
        **recognizer_conf,
    )
    return transformers_recognizer


def get_analyzer(
    recognizer: EntityRecognizer,
    regex_groups: list[RegexPattern],
    custom_names: list[str],
    supported_languages: list[str],
) -> AnalyzerEngine:
    nlp_engine = _get_nlp_engine(languages=supported_languages)

    registry = RecognizerRegistry(supported_languages=supported_languages)
    registry.load_predefined_recognizers(nlp_engine=nlp_engine)
    registry = _add_recognizers(registry, regex_groups, custom_names, supported_languages)
    registry.add_recognizer(recognizer)
    registry.remove_recognizer("SpacyRecognizer")

    return AnalyzerEngine(
        nlp_engine=nlp_engine,
        registry=registry,
        supported_languages=supported_languages,
        context_aware_enhancer=LemmaContextAwareEnhancer(
            context_similarity_factor=0.35,
            min_score_with_context_similarity=0.4,
        ),
    )
