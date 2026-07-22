"""
TokenBudgetController : Contrôleur de Budget Tokens & Appels LLM (Niveau 8.0 Auto-Évolution Collective).
Plafonne strictement la consommation de ressources et le nombre d'appels LLM par job et par guilde.
"""

import json
import os
from typing import Dict, Any


class TokenBudgetExceededError(Exception):
    """Exception levée lorsque le budget d'appels ou de tokens d'un job est épuisé."""
    pass


class TokenBudgetController:
    """
    Contrôleur de Budget de Consommation LLM (Niveau 8.0).
    Empêche les emballements récursifs et protège les ressources mémoire (RAM/CPU/Ollama).
    """

    def __init__(self, max_calls_per_job: int = 25, max_tokens_per_job: int = 100000):
        self.max_calls_per_job = max_calls_per_job
        self.max_tokens_per_job = max_tokens_per_job
        self.job_budgets: Dict[str, Dict[str, Any]] = {}

    def init_job_budget(self, job_id: str, custom_max_calls: int = None, custom_max_tokens: int = None) -> None:
        """Initialise le suivi budgétaire pour un nouveau job."""
        if job_id not in self.job_budgets:
            self.job_budgets[job_id] = {
                "max_calls": custom_max_calls or self.max_calls_per_job,
                "max_tokens": custom_max_tokens or self.max_tokens_per_job,
                "consumed_calls": 0,
                "consumed_tokens": 0,
                "guild_calls": {}
            }

    def check_and_consume(self, job_id: str, guild: str = "GLOBAL", estimated_tokens: int = 1000) -> bool:
        """
        Vérifie et consomme le budget pour un appel LLM.
        Lève TokenBudgetExceededError si le plafond est dépassé.
        """
        if not job_id:
            job_id = "default_job"

        self.init_job_budget(job_id)
        budget = self.job_budgets[job_id]

        if budget["consumed_calls"] + 1 > budget["max_calls"]:
            msg = f"❌ PLAFOND D'APPELS ATTEINT pour le job '{job_id}' ({budget['consumed_calls']}/{budget['max_calls']} appels)."
            print(f"[TokenBudgetController] {msg}")
            raise TokenBudgetExceededError(msg)

        if budget["consumed_tokens"] + estimated_tokens > budget["max_tokens"]:
            msg = f"❌ PLAFOND DE TOKENS ATTEINT pour le job '{job_id}' ({budget['consumed_tokens']}/{budget['max_tokens']} tokens)."
            print(f"[TokenBudgetController] {msg}")
            raise TokenBudgetExceededError(msg)

        # Consommation autorisée
        budget["consumed_calls"] += 1
        budget["consumed_tokens"] += estimated_tokens
        budget["guild_calls"][guild] = budget["guild_calls"].get(guild, 0) + 1

        print(f"[TokenBudgetController] 🟢 Budget OK pour '{job_id}' [Guilde: {guild}] (Appel {budget['consumed_calls']}/{budget['max_calls']}, Tokens: {budget['consumed_tokens']}/{budget['max_tokens']})")
        return True

    def get_job_stats(self, job_id: str) -> Dict[str, Any]:
        """Retourne les statistiques de consommation d'un job."""
        return self.job_budgets.get(job_id, {
            "consumed_calls": 0,
            "consumed_tokens": 0,
            "max_calls": self.max_calls_per_job,
            "max_tokens": self.max_tokens_per_job,
            "guild_calls": {}
        })
