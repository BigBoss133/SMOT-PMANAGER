# ai_providers.py
"""AI provider abstraction and factory with graceful fallback.
This module defines a common interface for AI back‑ends (Ollama and OpenAI) and a
factory that attempts to instantiate the requested provider. If initialization
fails (e.g., missing binary, network error, missing API key) the factory logs a
warning and falls back to Ollama, guaranteeing that the application can continue
operating.
"""

from __future__ import annotations

import json
import urllib.request
from abc import ABC, abstractmethod
from typing import Any

from pman.config import settings


class AIProvider(ABC):
    """Abstract base class for all AI providers.

    Concrete implementations must implement ``generate`` which returns the model
    response as a string.
    """

    @abstractmethod
    def generate(self, prompt: str, system: str = "") -> str:
        """Generate a completion for *prompt*.
        *system* is an optional system‑prompt that will be prepended to the user
        prompt when the provider supports it.
        """
        raise NotImplementedError


class OllamaProvider(AIProvider):
    """Thin wrapper around the synchronous ``OllamaClient`` defined in
    ``pman.ollama``. It re‑uses the same HTTP logic but returns the generated text
    only.
    """

    def __init__(self, settings_obj: Any = None):
        # ``settings`` is imported from pman.config – we keep a reference for
        # potential future extensions.
        self.host = (settings.ollama_host).rstrip("/")
        self.model = settings.ollama_model

    def _post(self, endpoint: str, data: dict) -> dict:
        url = f"{self.host}{endpoint}"
        payload = json.dumps(data).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            return json.loads(resp.read().decode())

    def generate(self, prompt: str, system: str = "") -> str:
        payload: dict[str, Any] = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {"num_gpu": 99},
        }
        if system:
            payload["system"] = system
        result = self._post("/api/generate", payload)
        # Ollama returns a dict with a "response" key containing the text.
        return result.get("response", "")


class OpenAIProvider(AIProvider):
    """Very lightweight OpenAI wrapper using the public completions endpoint.
    It expects ``settings.OPENAI_API_KEY`` to be defined; otherwise an exception
    is raised during initialisation.
    """

    def __init__(self, settings_obj: Any = None):
        api_key = getattr(settings, "openai_api_key", None)
        if not api_key:
            raise ValueError("OpenAI API key not configured in settings")
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

    def generate(self, prompt: str, system: str = "") -> str:
        messages = [{"role": "user", "content": prompt}]
        if system:
            messages.insert(0, {"role": "system", "content": system})
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.7,
        }
        result = self._post(payload)
        # OpenAI returns a list of choices; we take the first message content.
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
            print(f"[WARN] Failed to initialise '{provider_name}' provider: {exc}. Falling back to Ollama.")
            return OllamaProvider()

# Export the concrete classes for external imports
__all__ = ["AIProvider", "OllamaProvider", "OpenAIProvider", "AIFactory"]
