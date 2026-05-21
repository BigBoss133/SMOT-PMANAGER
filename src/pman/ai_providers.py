# ai_providers.py
"""AI provider abstraction and factory with graceful fallback and circuit breaker.

This module defines a common interface for AI back‑ends (Ollama and OpenAI) and a
factory that attempts to instantiate the requested provider. If initialization
fails (e.g., missing binary, network error, missing API key) the factory logs a
warning and falls back to Ollama, guaranteeing that the application can continue
operating.

OllamaProvider also implements a circuit breaker: after 3 consecutive failures
the provider is disabled for 120 seconds to prevent cascading errors.
"""

from __future__ import annotations

import json
import time
import urllib.request
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Optional

from pman.config import settings
from pman.errors import AIError


@dataclass
class CircuitState:
    failures: int = 0
    last_failure: float = 0.0
    disabled: bool = False


class AIProvider(ABC):
    """Abstract base class for all AI providers.

    Concrete implementations must implement ``generate`` which returns the model
    response as a string.
    """

    @abstractmethod
    def generate(
        self,
        prompt: str,
        system: str = "",
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """Generate a completion for *prompt*.

        *system* is an optional system‑prompt that will be prepended to the user
        prompt when the provider supports it. *temperature* and *max_tokens* are
        optional generation parameters.
        """
        raise NotImplementedError


class OllamaProvider(AIProvider):
    """Ollama provider with circuit breaker protection.

    After ``CIRCUIT_THRESHOLD`` consecutive failures the provider is disabled for
    ``CIRCUIT_TIMEOUT`` seconds. The first token must arrive within ``TTFT_TIMEOUT``
    seconds otherwise the request is treated as a failure.
    """

    CIRCUIT_THRESHOLD = 3
    CIRCUIT_TIMEOUT = 120
    TTFT_TIMEOUT = 15

    def __init__(self, settings_obj: Any = None):
        self.host = (settings.ollama_host).rstrip("/")
        self.model = settings.ollama_model
        self._circuit = CircuitState()

    def _check_circuit(self) -> None:
        if self._circuit.disabled:
            if time.time() - self._circuit.last_failure > self.CIRCUIT_TIMEOUT:
                self._circuit.disabled = False
                self._circuit.failures = 0
            else:
                raise AIError("Ollama circuit breaker is open — too many failures")

    def _record_failure(self) -> None:
        self._circuit.failures += 1
        self._circuit.last_failure = time.time()
        if self._circuit.failures >= self.CIRCUIT_THRESHOLD:
            self._circuit.disabled = True

    def _record_success(self) -> None:
        self._circuit.failures = 0

    def _post(self, endpoint: str, data: dict) -> dict:
        url = f"{self.host}{endpoint}"
        payload = json.dumps(data).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=self.TTFT_TIMEOUT) as resp:
            return json.loads(resp.read().decode())

    def generate(
        self,
        prompt: str,
        system: str = "",
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        self._check_circuit()

        payload: dict[str, Any] = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {"num_gpu": 99},
        }
        if system:
            payload["system"] = system
        if temperature is not None:
            payload["options"]["temperature"] = temperature
        if max_tokens is not None:
            payload["options"]["num_predict"] = max_tokens

        try:
            result = self._post("/api/generate", payload)
            self._record_success()
            return result.get("response", "")
        except Exception as exc:
            self._record_failure()
            raise AIError(f"Ollama generation failed: {exc}") from exc


class OpenAIProvider(AIProvider):
    """Very lightweight OpenAI wrapper using the public chat completions endpoint.

    It expects ``settings.openai_api_key`` to be defined; otherwise an exception
    is raised during initialisation.
    """

    def __init__(self, settings_obj: Any = None):
        api_key = getattr(settings, "openai_api_key", None)
        if not api_key:
            raise AIError("OpenAI API key not configured in settings")
        self.api_key = api_key
        self.model = getattr(settings, "openai_model", "gpt-4o-mini")
        self.base_url = "https://api.openai.com/v1/chat/completions"

    def _post(self, data: dict) -> dict:
        payload = json.dumps(data).encode("utf-8")
        req = urllib.request.Request(
            self.base_url,
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            return json.loads(resp.read().decode())

    def generate(
        self,
        prompt: str,
        system: str = "",
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        messages = [{"role": "user", "content": prompt}]
        if system:
            messages.insert(0, {"role": "system", "content": system})
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature if temperature is not None else 0.7,
        }
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        result = self._post(payload)
        return result.get("choices", [{}])[0].get("message", {}).get("content", "")


class AIFactory:
    """Factory that creates an ``AIProvider`` instance.

    It first tries the user‑selected provider (``settings.ai_provider``). If that
    instantiation fails, it falls back to ``OllamaProvider`` and logs a warning.
    """

    @staticmethod
    def create() -> AIProvider:
        provider_name = getattr(settings, "ai_provider", "ollama").lower()
        try:
            if provider_name == "openai":
                return OpenAIProvider()
            # Default – Ollama
            return OllamaProvider()
        except Exception as exc:
            # Simple stdout warning – in a real app this would go through the
            # logger configured elsewhere.
            print(
                f"[WARN] Failed to initialise '{provider_name}' provider: {exc}."
                " Falling back to Ollama."
            )
            return OllamaProvider()


# Export the concrete classes for external imports
__all__ = ["AIProvider", "OllamaProvider", "OpenAIProvider", "AIFactory"]
