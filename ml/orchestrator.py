"""Prompt orchestration utilities with optional LangChain integration."""
from __future__ import annotations

import logging
from typing import Dict, List, Optional

LOGGER = logging.getLogger(__name__)

PROMPT_TEMPLATE = (
    "You are a multilingual assistant. Always answer using the target language.\n"
    "Target language: {target_language}\n"
    "Conversation history:\n{history}\n"
    "User: {user_input}\n"
    "Assistant:"
)

try:  # Attempt to import LangChain components
    from langchain.chains import LLMChain
    from langchain.memory import ConversationBufferMemory
    from langchain.prompts import PromptTemplate

    try:  # LangChain 0.1.x base class
        from langchain_core.language_models import LLM as LangChainLLMBase
    except ImportError:  # pragma: no cover - fallback for older versions
        from langchain.llms.base import LLM as LangChainLLMBase  # type: ignore

    try:  # LangChain 0.1.x integrations live in langchain_community
        from langchain_community.llms import HuggingFacePipeline
    except ImportError:  # pragma: no cover - fallback for older versions
        try:
            from langchain.llms import HuggingFacePipeline  # type: ignore
        except ImportError:  # pragma: no cover
            HuggingFacePipeline = None  # type: ignore

    _LANGCHAIN_AVAILABLE = True
except ImportError:  # pragma: no cover - LangChain not installed in the runtime
    LLMChain = None  # type: ignore
    ConversationBufferMemory = None  # type: ignore
    PromptTemplate = None  # type: ignore
    LangChainLLMBase = object  # type: ignore
    HuggingFacePipeline = None  # type: ignore
    _LANGCHAIN_AVAILABLE = False

try:
    from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline

    _TRANSFORMERS_AVAILABLE = True
except Exception:  # pragma: no cover - transformers not installed during tests
    AutoModelForCausalLM = None  # type: ignore
    AutoTokenizer = None  # type: ignore
    pipeline = None  # type: ignore
    _TRANSFORMERS_AVAILABLE = False


class TemplateResponder:
    """A lightweight template-based responder used as a fallback model."""

    def generate(self, prompt: str) -> str:
        language = self._extract_language(prompt)
        message = self._extract_user_message(prompt)
        if not message:
            return "I'm ready whenever you want to chat."
        translated_prefix = f"[{language}] " if language else ""
        return f"{translated_prefix}You said: {message}. Let me know if you need more help."

    @staticmethod
    def _extract_language(prompt: str) -> str:
        for line in reversed(prompt.splitlines()):
            lowered = line.lower()
            if lowered.startswith("target language:"):
                return line.split(":", 1)[1].strip() or "en"
        return "en"

    @staticmethod
    def _extract_user_message(prompt: str) -> str:
        for line in reversed(prompt.splitlines()):
            if line.startswith("User:"):
                return line.split(":", 1)[1].strip()
        return ""


if _LANGCHAIN_AVAILABLE:

    class TemplateLLM(LangChainLLMBase):
        """Adapter that wraps :class:`TemplateResponder` in a LangChain LLM interface."""

        def __init__(self, responder: TemplateResponder) -> None:
            super().__init__()
            self._responder = responder

        def _call(self, prompt: str, stop: Optional[List[str]] = None) -> str:  # pragma: no cover - thin wrapper
            return self._responder.generate(prompt)

        @property
        def _llm_type(self) -> str:  # pragma: no cover - metadata only
            return "template-responder"


    class PromptOrchestrator:
        """Coordinate prompts and conversation state using LangChain."""

        def __init__(
            self,
            model_path: Optional[str] = None,
            generation_config: Optional[Dict[str, object]] = None,
        ) -> None:
            self._responder = TemplateResponder()
            self._llm = self._initialise_llm(model_path, generation_config)
            self._memory = ConversationBufferMemory(
                memory_key="history",
                input_key="user_input",
                return_messages=False,
            )
            self._prompt = PromptTemplate(
                input_variables=["history", "user_input", "target_language"],
                template=PROMPT_TEMPLATE,
            )
            self._chain = LLMChain(llm=self._llm, prompt=self._prompt, memory=self._memory)

        def _initialise_llm(
            self,
            model_path: Optional[str],
            generation_config: Optional[Dict[str, object]],
        ):
            if (
                model_path
                and HuggingFacePipeline is not None
                and _TRANSFORMERS_AVAILABLE
                and AutoModelForCausalLM is not None
                and AutoTokenizer is not None
                and pipeline is not None
            ):
                try:
                    tokenizer = AutoTokenizer.from_pretrained(model_path)
                    model = AutoModelForCausalLM.from_pretrained(model_path)
                    if tokenizer.pad_token is None:
                        tokenizer.pad_token = tokenizer.eos_token
                    pipeline_config: Dict[str, object] = {
                        "max_new_tokens": 128,
                        "do_sample": False,
                        "temperature": 0.7,
                    }
                    if generation_config:
                        pipeline_config.update(generation_config)
                    text_generation = pipeline(
                        "text-generation", model=model, tokenizer=tokenizer, **pipeline_config
                    )
                    return HuggingFacePipeline(pipeline=text_generation)
                except Exception as exc:  # pragma: no cover - requires HF runtime
                    LOGGER.warning("Falling back to template responder: %s", exc)
            return TemplateLLM(self._responder)

        def run(self, user_input: str, target_language: str = "en") -> str:
            if not user_input.strip():
                return "I'm ready whenever you want to chat."
            response = self._chain.predict(user_input=user_input, target_language=target_language)
            return response.strip()

        def reset(self) -> None:
            self._memory.clear()

else:

    class PromptOrchestrator:
        """Simplified orchestrator used when LangChain is not installed."""

        def __init__(
            self,
            model_path: Optional[str] = None,  # pylint: disable=unused-argument
            generation_config: Optional[Dict[str, object]] = None,  # pylint: disable=unused-argument
        ) -> None:
            LOGGER.info(
                "LangChain is unavailable; using a minimal in-memory orchestrator."
            )
            self._responder = TemplateResponder()
            self._history: List[str] = []

        def run(self, user_input: str, target_language: str = "en") -> str:
            if not user_input.strip():
                return "I'm ready whenever you want to chat."
            history_text = "\n".join(self._history)
            prompt = PROMPT_TEMPLATE.format(
                history=history_text,
                user_input=user_input,
                target_language=target_language,
            )
            response = self._responder.generate(prompt)
            self._history.append(f"User: {user_input}")
            self._history.append(f"Assistant: {response}")
            return response.strip()

        def reset(self) -> None:
            self._history.clear()
