import json
from typing import Dict, Any, Optional

from orchestrator.llm import call_llm, DEFAULT_MODEL, TEMP_ANALYSTE
from orchestrator.interfaces import QATestSuite


class AgentAnalyste:
    def __init__(self):
        self.nom = "Analyste Beta"

    def evaluer_rapport(self, rapport_brut: dict, loop_index: int = 0) -> dict:
        """
        Évalue de manière critique le rapport produit par l'Agent Éclaireur.
        Utilise l'API Mistral pour une analyse argumentée.
        Si le rapport est insuffisant, fournit une `consigne_feedback` pour la boucle de rétroaction.
        """
        print(f"[{self.nom}] Réception du rapport de l'Éclaireur (Itération #{loop_index + 1}). Début de l'évaluation...")

        system_prompt = """Tu es un agent analyste critique expert.
Tu reçois un rapport de recherche d'un autre agent (l'Éclaireur) et tu dois l'évaluer rigoureusement.

Tu dois répondre UNIQUEMENT avec un objet JSON valide, sans aucun texte avant ou après.
Le JSON doit avoir exactement cette structure :
{
    "sujet_etudie": "le sujet du rapport",
    "rapport_eclaireur": {},
    "conclusion_analyste": {
        "decision": "Validé pour la production | Rejeté | À approfondir",
        "score_confiance": 0-100,
        "commentaire": "un commentaire détaillé et argumenté",
        "consigne_feedback": "Consigne précise à l'Éclaireur sur ce qu'il doit approfondir/rechercher (seulement si score < 70 ou décision != Validé pour la production, sinon string vide)"
    }
}

RÈGLES :
- Évalue chaque point clé du rapport : est-il plausible, vague, incomplet ou contradictoire ?
- Si des sources Web sont présentes, vérifie si elles renforcent la crédibilité des points clés.
- Attribue un score de confiance entre 0 et 100 basé sur la qualité et la complétude du rapport.
- Choisis une décision parmi : "Validé pour la production", "Rejeté", ou "À approfondir".
- Si le score est < 70 ou la décision est "Rejeté" / "À approfondir", donne une "consigne_feedback" TRÈS PRECISE.
- Sois exigeant et constructif."""

        user_prompt = f"Évalue ce rapport de recherche (Itération {loop_index + 1}) :\n{json.dumps(rapport_brut, ensure_ascii=False, indent=2)}"

        try:
            raw_response = call_llm(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                model=DEFAULT_MODEL,
                temperature=TEMP_ANALYSTE,
                json_mode=True,
            )

            resultat = json.loads(raw_response)

            # Assure la compatibilité : on injecte toujours le rapport original
            resultat["rapport_eclaireur"] = rapport_brut
            resultat["sujet_etudie"] = rapport_brut.get("sujet_analyse", "Inconnu")

            conclusion = resultat.get("conclusion_analyste", {})
            score = conclusion.get("score_confiance", 0)
            decision = conclusion.get("decision", "")

            # Sécurité : générer une consigne si absente et nécessaire
            if (score < 70 or decision != "Validé pour la production") and not conclusion.get("consigne_feedback"):
                conclusion["consigne_feedback"] = f"Le rapport a obtenu un score de {score}/100 ({decision}). Veuillez approfondir la recherche avec des sources web plus récentes et des exemples concrets."

            print(f"[{self.nom}] Évaluation terminée (Score: {score}/100 | Décision: {decision})")
            return resultat

        except json.JSONDecodeError:
            print(f"[{self.nom}] ⚠️ Réponse non-JSON reçue, construction d'un verdict de secours.")
            return {
                "sujet_etudie": rapport_brut.get("sujet_analyse", "Inconnu"),
                "rapport_eclaireur": rapport_brut,
                "conclusion_analyste": {
                    "decision": "À approfondir",
                    "score_confiance": 50,
                    "commentaire": f"Analyse automatique échouée sur la forme. Réponse brute : {raw_response[:300]}",
                    "consigne_feedback": "Rechercher des informations plus claires et structurées sur le sujet."
                },
            }
        except RuntimeError as e:
            print(f"[{self.nom}] ❌ Erreur API : {e}")
            return {
                "sujet_etudie": rapport_brut.get("sujet_analyse", "Inconnu"),
                "rapport_eclaireur": rapport_brut,
                "conclusion_analyste": {
                    "decision": "Rejeté",
                    "score_confiance": 0,
                    "commentaire": f"Impossible d'évaluer le rapport : {str(e)}",
                    "consigne_feedback": "Vérifier l'état de l'API et relancer l'analyse."
                },
            }

    def generer_suite_de_tests_opposable(self, sujet: str, rapport_eclaireur: Optional[dict] = None) -> QATestSuite:
        """
        En tant qu'architecte Assurance Qualité (QA), conçoit la suite de tests unitaires/d'intégration
        opposables et immuables (test_main.py) que l'Agent Codeur devra satisfaire sans la modifier.
        """
        print(f"[{self.nom}] 🧪 Conception de la suite de tests opposable (QA TestSuite)...")

        system_prompt = """Tu es un ingénieur Assurance Qualité (QA / Test Architect) senior.
Ta mission est de concevoir un contrat de test automatisé strict, opposable et immuable en Python avec pytest pour valider la fonctionnalité demandée.

Tu dois répondre UNIQUEMENT avec un objet JSON valide matching le schéma suivant :
{
    "explication_tests": "Explication des cas nominaux (Happy Path), des cas limites (Edge cases) et des exceptions testées",
    "test_main_code": "Code Python complet de test_main.py utilisant pytest",
    "requirements_txt": "pytest"
}

RÈGLES STRICTES :
1. Le fichier test_main.py doit importer la fonction/classe à tester depuis main.py (`from main import ...`).
2. Teste à la fois les cas nominaux et les cas d'erreurs (ex: `pytest.raises(...)` pour les exceptions).
3. Le code de test doit être valide, moderne et autonome.
4. Ce contrat est immuable : le développeur devra faire passer ces tests au vert sans modifier test_main.py."""

        user_prompt = f"Sujet fonctionnel : {sujet}\n"
        if rapport_eclaireur:
            user_prompt += f"Analyse et spécifications :\n{json.dumps(rapport_eclaireur, ensure_ascii=False, indent=2)}\n"

        user_prompt += "\nGénère la QATestSuite structurée en JSON."

        try:
            raw_response = call_llm(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                model=DEFAULT_MODEL,
                temperature=TEMP_ANALYSTE,
                json_mode=True,
            )
            data = json.loads(raw_response)
            suite = QATestSuite(
                explication_tests=data.get("explication_tests", "Suite de tests unitaires pytest"),
                test_main_code=data.get("test_main_code", "# Code test_main.py\nimport pytest\n"),
                requirements_txt=data.get("requirements_txt", "pytest")
            )
            suite.test_hash = suite.compute_hash()
            print(f"[{self.nom}] ✅ Suite de tests QA générée (immuable) - Sceau SHA-256 : {suite.test_hash[:16]}...")
            return suite
        except Exception as e:
            print(f"[{self.nom}] ⚠️ Erreur génération QA TestSuite : {e}. Fallback générique.")
            return QATestSuite(
                explication_tests="Tests unitaires de base",
                test_main_code="import pytest\nfrom main import execute\n\ndef test_execute():\n    assert execute() is not None\n",
                requirements_txt="pytest"
            )
