"""Wrapper client Ollama."""

import json
import urllib.request
from typing import Any

from pman.config import settings


class OllamaClient:
    """Client sincrono per Ollama API."""

    def __init__(self, host: str | None = None, model: str | None = None):
        self.host = (host or settings.ollama_host).rstrip("/")
        self.model = model or settings.ollama_model

    def _post(self, endpoint: str, data: dict) -> dict[str, Any]:
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

    def generate(
        self,
        prompt: str,
        system: str = "",
        stream: bool = False,
        options: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Genera testo con /api/generate."""
        data: dict[str, Any] = {
            "model": self.model,
            "prompt": prompt,
            "stream": stream,
            "options": options or {"num_gpu": 99},
        }
        if system:
            data["system"] = system
        return self._post("/api/generate", data)

    def chat(
        self,
        messages: list[dict[str, str]],
        stream: bool = False,
    ) -> dict[str, Any]:
        """Chat con /api/chat."""
        data = {
            "model": self.model,
            "messages": messages,
            "stream": stream,
            "options": {"num_gpu": 99},
        }
        return self._post("/api/chat", data)

    def list_models(self) -> list[str]:
        """Lista modelli disponibili."""
        url = f"{self.host}/api/tags"
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            return [m["name"] for m in data.get("models", [])]
