import pytest

from pman.ai_providers import AIProvider, CircuitState
from pman.errors import AIError


class TestCircuitBreaker:
    def test_circuit_closes_after_threshold(self):
        provider = AIProvider()
        provider._record_failure()
        provider._record_failure()
        provider._record_failure()
        assert provider._circuit.disabled is True

    def test_circuit_opens_after_timeout(self):
        provider = AIProvider()
        provider._circuit.disabled = True
        provider._circuit.last_failure = 0
        provider._check_circuit()
        assert provider._circuit.disabled is False

    def test_success_resets_failures(self):
        provider = AIProvider()
        provider._record_failure()
        provider._record_success()
        assert provider._circuit.failures == 0

    def test_check_circuit_raises_when_disabled(self):
        provider = AIProvider()
        provider._circuit.disabled = True
        provider._circuit.last_failure = 9999999999
        with pytest.raises(AIError, match="circuit breaker"):
            provider._check_circuit()
