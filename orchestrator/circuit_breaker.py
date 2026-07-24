"""
Module Circuit Breaker pour la résilience des API externes (orchestrator/circuit_breaker.py).

Gère la machine à états CLOSED -> OPEN -> HALF_OPEN pour isoler les pannes
des services tiers (Mistral AI, Tavily API) et basculer sur un mode dégradé (fallback).
"""

import time
import logging
from enum import Enum
from typing import Callable, Any, Dict, Optional, Tuple

from orchestrator.metrics import (
    CIRCUIT_BREAKER_STATE,
    CIRCUIT_BREAKER_TRIPPED
)

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    CLOSED = 0       # Fonctionnement normal, requêtes autorisées
    HALF_OPEN = 1    # Test de récupération, requêtes limitées
    OPEN = 2         # Disjoncté, requêtes bloquées (échec immédiat + fallback)


class CircuitBreakerOpenError(Exception):
    """Exception levée lorsqu'un appel est tenté alors que le Circuit Breaker est OPEN."""
    pass


class CircuitBreaker:
    """
    Implémentation du pattern Circuit Breaker pour la résilience réseau et API.
    """

    def __init__(
        self,
        name: str,
        failure_threshold: int = 3,
        recovery_timeout: float = 30.0
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout

        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = 0.0
        self.success_count = 0

        self._update_metrics()

    def _update_metrics(self):
        """Met à jour les jauges Prometheus."""
        CIRCUIT_BREAKER_STATE.labels(service=self.name).set(self.state.value)

    def _on_success(self):
        """Gère un appel réussi."""
        if self.state == CircuitState.HALF_OPEN:
            logger.info(f"🟢 [CircuitBreaker:{self.name}] Récupération réussie ! Passage de HALF_OPEN -> CLOSED.")
            self.state = CircuitState.CLOSED
            self.failure_count = 0
            self._update_metrics()
        elif self.state == CircuitState.CLOSED:
            self.failure_count = 0

    def _on_failure(self, error: Exception):
        """Gère un échec d'appel."""
        self.failure_count += 1
        self.last_failure_time = time.time()

        logger.warning(
            f"⚠️ [CircuitBreaker:{self.name}] Échec #{self.failure_count}/{self.failure_threshold}: {error}"
        )

        if self.failure_count >= self.failure_threshold:
            if self.state != CircuitState.OPEN:
                logger.error(
                    f"🔴 [CircuitBreaker:{self.name}] Seuil d'échecs atteint ({self.failure_count}). "
                    f"Basculement en état OPEN pour {self.recovery_timeout}s."
                )
                self.state = CircuitState.OPEN
                CIRCUIT_BREAKER_TRIPPED.labels(service=self.name).inc()
                self._update_metrics()

    def can_execute(self) -> bool:
        """Détermine si un appel réseau peut être tenté."""
        if self.state == CircuitState.CLOSED:
            return True

        if self.state == CircuitState.OPEN:
            now = time.time()
            if (now - self.last_failure_time) >= self.recovery_timeout:
                logger.info(
                    f"🟡 [CircuitBreaker:{self.name}] Temps de pause écoulé ({self.recovery_timeout}s). "
                    f"Passage de OPEN -> HALF_OPEN."
                )
                self.state = CircuitState.HALF_OPEN
                self._update_metrics()
                return True
            return False

        if self.state == CircuitState.HALF_OPEN:
            return True

        return False

    def call(self, func: Callable, *args, fallback: Optional[Callable] = None, **kwargs) -> Any:
        """
        Exécute la fonction `func` sous le contrôle du Circuit Breaker.
        En cas de disjonction (OPEN), exécute le `fallback` s'il est fourni.
        """
        if not self.can_execute():
            msg = f"Circuit Breaker '{self.name}' est OPEN (service en panne ou indisponible)."
            logger.error(f"🛑 [CircuitBreaker:{self.name}] Requête rejetée (Fast Fail).")
            if fallback is not None:
                return fallback(*args, **kwargs)
            raise CircuitBreakerOpenError(msg)

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure(e)
            if fallback is not None:
                logger.info(f"🔄 [CircuitBreaker:{self.name}] Exécution du fallback suite à l'échec.")
                return fallback(*args, **kwargs)
            raise e

    def get_status(self) -> Dict[str, Any]:
        """Retourne le dictionnaire d'état du disjoncteur."""
        return {
            "service": self.name,
            "state": self.state.name,
            "state_value": self.state.value,
            "failure_count": self.failure_count,
            "failure_threshold": self.failure_threshold,
            "recovery_timeout": self.recovery_timeout,
            "last_failure_time": self.last_failure_time
        }


# Dynamic instances singleton pour Mistral et Tavily / DDG
mistral_circuit_breaker = CircuitBreaker("mistral_api", failure_threshold=3, recovery_timeout=30.0)
tavily_circuit_breaker = CircuitBreaker("tavily_api", failure_threshold=3, recovery_timeout=30.0)
