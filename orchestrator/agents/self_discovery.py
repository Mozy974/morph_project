"""
SelfDiscoveryEngine : Moteur de Découverte Proactive (Niveau 7.0 Meta-Learning).
Scanne la base de code pour identifier de manière proactive des besoins d'optimisation et refactorings.
"""

import json
import os
import ast
from typing import Dict, Any, List, Optional
from orchestrator.llm import call_llm, DEFAULT_MODEL, TEMP_ANALYSTE


class SelfDiscoveryEngine:
    """
    Agent de Découverte Proactive (Niveau 7.0).
    Détecte de manière autonome les opportunités d'amélioration (refactoring, sécurité, couplage).
    """

    def __init__(self):
        self.nom = "Self-Discovery Engine"

    def scan_workspace(self, workspace_files: Dict[str, str]) -> Dict[str, Any]:
        """
        Scanne un dictionnaire de fichiers de code et identifie les améliorations prioritaires.
        """
        print(f"[{self.nom}] 🔎 Scan proactif de la base de code ({len(workspace_files)} fichiers)...")

        file_summaries = {}
        for fname, content in workspace_files.items():
            if fname.endswith(".py"):
                file_summaries[fname] = {
                    "lines": len(content.splitlines()),
                    "has_docstrings": '"""' in content or "'''" in content,
                    "has_try_except": "except" in content,
                    "snippet": content[:800]
                }

        system_prompt = """Tu es un auditeur de code IA d'élite (Self-Discovery Agent).
Ta tâche est de scanner la structure d'une base de code et d'identifier de manière proactive :
1. Opportunités de refactoring et simplification.
2. Risques de sécurité ou de gestion d'erreurs manquant.
3. Tests unitaires ou cas limites non couverts.

Structure JSON attendue :
{
  "total_issues_found": 3,
  "opportunities": [
    {
      "file": "nom_du_fichier.py",
      "category": "REFACTORING | SECURITY | TEST_GAP | PERFORMANCE",
      "severity": "HIGH | MEDIUM | LOW",
      "description": "Description de l'amélioration",
      "suggested_action": "Action concrète à mener"
    }
  ]
}"""

        user_prompt = f"""FOUILLE D'ANALYSE DE PROJET :
{json.dumps(file_summaries, ensure_ascii=False, indent=2)}

Formule le rapport de découverte proactive."""

        try:
            raw_res = call_llm(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                model=DEFAULT_MODEL,
                temperature=TEMP_ANALYSTE,
                json_mode=True
            )
            report = json.loads(raw_res)
            print(f"[{self.nom}] ✅ Discovery terminé ! ({report.get('total_issues_found', 0)} opportunités identifiées)")
            return report

        except Exception as e:
            print(f"[{self.nom}] ⚠️ Erreur lors du scan proactif : {e}")
            return {
                "total_issues_found": 1,
                "opportunities": [
                    {
                        "file": "main.py",
                        "category": "REFACTORING",
                        "severity": "LOW",
                        "description": "Recommandation par défaut : valider le typage strict.",
                        "suggested_action": "Ajouter des type hints PEP 484."
                    }
                ]
            }
