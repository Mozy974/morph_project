"""
ExperienceReplayStore : Magasin de Replay d'Expérience et Feedback-Loop (Niveau 6.0 Auto-Évolution).
Permet l'apprentissage continu et l'injection de Few-Shot d'erreurs similaires résolues dans le passé.
"""

import json
import os
import datetime
from typing import List, Dict, Any, Optional

EXPERIENCE_FILE = os.path.join(os.path.dirname(__file__), "experience_replay.json")


class ExperienceReplayStore:
    """
    Stocke les expériences de Self-Healing réussies ou échouées
    pour fournir un contexte Few-Shot ultra-pertinent aux agents.
    """

    def __init__(self, store_path: str = EXPERIENCE_FILE):
        self.store_path = os.path.abspath(store_path)
        self.experiences: List[Dict[str, Any]] = self._load_experiences()

    def _load_experiences(self) -> List[Dict[str, Any]]:
        if os.path.exists(self.store_path):
            try:
                with open(self.store_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"[ExperienceReplay] ⚠️ Erreur lecture store : {e}")
        return []

    def _save_experiences(self) -> None:
        try:
            os.makedirs(os.path.dirname(self.store_path), exist_ok=True)
            with open(self.store_path, "w", encoding="utf-8") as f:
                json.dump(self.experiences, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[ExperienceReplay] ❌ Erreur sauvegarde store : {e}")

    def record_experience(
        self,
        error_traceback: str,
        failing_code: str,
        patch_applied: str,
        resolved: bool,
        keywords: Optional[List[str]] = None
    ) -> None:
        """Enregistre un événement de correction ou d'échec dans l'historique d'expérience."""
        exp = {
            "id": len(self.experiences) + 1,
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "error_snippet": error_traceback[:500],
            "failing_code_snippet": failing_code[:500],
            "patch_applied": patch_applied,
            "resolved": resolved,
            "keywords": keywords or []
        }
        self.experiences.append(exp)
        self._save_experiences()
        print(f"[ExperienceReplay] 🧠 Nouvelle expérience enregistrée (ID: {exp['id']}, Résolu: {resolved})")

    def find_similar_experiences(self, current_error: str, limit: int = 3) -> List[Dict[str, Any]]:
        """
        Recherche des expériences similaires basées sur des mots-clés d'erreurs communes.
        (ex: SyntaxError, KeyError, ImportError, AssertionError).
        """
        if not self.experiences:
            return []

        matched = []
        error_upper = current_error.upper()

        for exp in reversed(self.experiences):  # Priorité aux plus récentes
            if not exp.get("resolved", False):
                continue
            err_snip = exp.get("error_snippet", "").upper()

            # Calcul de correspondance simple
            score = 0
            for key in ["SYNTAXERROR", "KEYERROR", "TYPEERROR", "IMPORTERROR", "ASSERTIONERROR", "ATTRIBUTEERROR", "INDEXERROR"]:
                if key in error_upper and key in err_snip:
                    score += 5

            # Mots clés communs
            words = set(w for w in current_error.split() if len(w) > 4)
            for w in words:
                if w in exp.get("error_snippet", ""):
                    score += 1

            if score > 0:
                matched.append((score, exp))

        matched.sort(key=lambda x: x[0], reverse=True)
        return [item[1] for item in matched[:limit]]

    def get_few_shot_prompt_context(self, current_error: str) -> str:
        """Génère un bloc Few-Shot d'exemples de résolution pertinents."""
        similar = self.find_similar_experiences(current_error)
        if not similar:
            return ""

        context = "\n--- EXEMPLES DE CORRECTIONS RÉUSSIES PASSÉES (FEW-SHOT REPLAY) ---\n"
        for i, exp in enumerate(similar, 1):
            context += f"\n[Exemple {i}]\n"
            context += f"ERREUR PASSÉE : {exp.get('error_snippet')}\n"
            context += f"PATCH RECOMMANDÉ :\n{exp.get('patch_applied')}\n"
        context += "--------------------------------------------------------\n"

        return context
