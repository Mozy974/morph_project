"""
DistributedRLEngine : Moteur d'Apprentissage par Renforcement Distribué (Niveau 9.0 Conscience Collective).
Évalue la qualité des trajectoires multi-agents avec une pondération hybride (80% TDD / 20% Vitesse).
"""

import json
from typing import Dict, Any, List, Optional


class DistributedRLEngine:
    """
    Moteur RL Distribué (Niveau 9.0).
    Calcule le Reward Score des actions d'agents pour faire évoluer les politiques de choix de modèles et de stratégies.
    """

    def __init__(self, weight_tdd: float = 0.8, weight_speed: float = 0.2):
        self.nom = "Distributed RL Engine"
        self.weight_tdd = weight_tdd
        self.weight_speed = weight_speed

    def calculate_reward_score(
        self,
        tdd_passed: bool,
        attempts: int,
        duration_sec: float,
        target_duration_sec: float = 15.0
    ) -> Dict[str, Any]:
        """
        Calcule la récompense globale (0.0 à 1.0) selon la pondération 80% TDD / 20% Vitesse.
        """
        # Score TDD (80%)
        if not tdd_passed:
            tdd_score = 0.0
        else:
            # Récompense maximale si passé du 1er coup, décrément léger si retries
            tdd_score = max(0.2, 1.0 - (attempts - 1) * 0.25)

        # Score Vitesse (20%)
        if duration_sec <= target_duration_sec:
            speed_score = 1.0
        else:
            speed_score = max(0.1, target_duration_sec / (duration_sec + 0.001))

        # Combined Reward
        reward_score = (self.weight_tdd * tdd_score) + (self.weight_speed * speed_score)
        reward_score = round(min(1.0, max(0.0, reward_score)), 3)

        print(f"[{self.nom}] 🎯 RL Reward Score : {reward_score:.3f} (TDD Score: {tdd_score:.2f}, Speed Score: {speed_score:.2f})")

        return {
            "reward_score": reward_score,
            "tdd_score": tdd_score,
            "speed_score": speed_score,
            "weights": {"tdd": self.weight_tdd, "speed": self.weight_speed}
        }
