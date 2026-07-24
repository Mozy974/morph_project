"""
Tests unitaires pour le module Circuit Breaker (tests/test_circuit_breaker.py).
"""

import time
import pytest
from orchestrator.circuit_breaker import (
    CircuitBreaker,
    CircuitState,
    CircuitBreakerOpenError
)


def test_circuit_breaker_initial_state():
    cb = CircuitBreaker("test_service", failure_threshold=2, recovery_timeout=1.0)
    assert cb.state == CircuitState.CLOSED
    assert cb.failure_count == 0
    assert cb.can_execute() is True


def test_circuit_breaker_success_resets_failures():
    cb = CircuitBreaker("test_success", failure_threshold=3, recovery_timeout=1.0)

    def dummy_func():
        return "OK"

    result = cb.call(dummy_func)
    assert result == "OK"
    assert cb.state == CircuitState.CLOSED
    assert cb.failure_count == 0


def test_circuit_breaker_trips_to_open_on_threshold():
    cb = CircuitBreaker("test_failing", failure_threshold=2, recovery_timeout=0.5)

    def failing_func():
        raise ValueError("Simulated Network Error")

    def fallback_func():
        return "FALLBACK_SUCCESS"

    # 1er échec : reste CLOSED (1/2)
    res1 = cb.call(failing_func, fallback=fallback_func)
    assert res1 == "FALLBACK_SUCCESS"
    assert cb.state == CircuitState.CLOSED
    assert cb.failure_count == 1

    # 2e échec : passe en OPEN (2/2)
    res2 = cb.call(failing_func, fallback=fallback_func)
    assert res2 == "FALLBACK_SUCCESS"
    assert cb.state == CircuitState.OPEN

    # Appel direct sans fallback doit lever CircuitBreakerOpenError
    with pytest.raises(CircuitBreakerOpenError):
        cb.call(failing_func)


def test_circuit_breaker_half_open_recovery():
    cb = CircuitBreaker("test_recovery", failure_threshold=2, recovery_timeout=0.2)

    def failing_func():
        raise RuntimeError("API Error")

    def success_func():
        return "RECOVERED"

    # Déclencher disjonction (OPEN)
    cb.call(failing_func, fallback=lambda: "FB")
    cb.call(failing_func, fallback=lambda: "FB")
    assert cb.state == CircuitState.OPEN

    # Attendre l'expiration du temps de récupération
    time.sleep(0.3)

    # L'appel suivant passe en HALF_OPEN
    assert cb.can_execute() is True
    assert cb.state == CircuitState.HALF_OPEN

    # Succès en HALF_OPEN réinitialise l'état vers CLOSED
    res = cb.call(success_func)
    assert res == "RECOVERED"
    assert cb.state == CircuitState.CLOSED
    assert cb.failure_count == 0
