from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from pman.ai_providers import OllamaProvider
from pman.errors import AIError


class TestCircuitBreaker:
    def test_circuit_closes_after_threshold(self):
        provider = OllamaProvider()
        provider._record_failure()
        provider._record_failure()
        provider._record_failure()
        assert provider._circuit.disabled is True

    def test_circuit_opens_after_timeout(self):
        provider = OllamaProvider()
        provider._circuit.disabled = True
        provider._circuit.last_failure = 0
        provider._check_circuit()
        assert provider._circuit.disabled is False

    def test_success_resets_failures(self):
        provider = OllamaProvider()
        provider._record_failure()
        provider._record_success()
        assert provider._circuit.failures == 0

    def test_check_circuit_raises_when_disabled(self):
        provider = OllamaProvider()
        provider._circuit.disabled = True
        provider._circuit.last_failure = 9999999999
        with pytest.raises(AIError, match="circuit breaker"):
            provider._check_circuit()


class TestAsyncGenerate:
    @pytest.mark.asyncio
    async def test_generate_success(self):
        provider = OllamaProvider()
        mock_resp = {"response": "Hello world"}
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = mock_resp
        with patch("pman.ai_providers.httpx.AsyncClient") as MockClient:
            instance = MockClient.return_value.__aenter__.return_value
            instance.post = AsyncMock(return_value=mock_response)
            result = await provider.generate("Say hello")
            assert result == "Hello world"

    @pytest.mark.asyncio
    async def test_generate_circuit_breaker(self):
        provider = OllamaProvider()
        provider._circuit.disabled = True
        provider._circuit.last_failure = 9999999999
        with pytest.raises(AIError, match="circuit breaker"):
            await provider.generate("Say hello")
