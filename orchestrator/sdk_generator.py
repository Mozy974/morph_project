"""
Module d'Agent Générateur d'OpenAPI & Client SDK (orchestrator/sdk_generator.py).
Extrait la structure des endpoints d'un code FastAPI/Flask et génère la spécification OpenAPI
ainsi qu'un client SDK Python prêt à l'emploi.
"""

import json
from typing import Dict, Any
from orchestrator.llm import call_llm, DEFAULT_MODEL


class SDKGeneratorAgent:
    def __init__(self):
        self.nom = "SDK Generator Agent"

    def generate_openapi_and_sdk(self, python_code: str) -> Dict[str, Any]:
        """
        Analyse le code Python et génère la spécification OpenAPI JSON et un Client SDK Python.

        Args:
            python_code: Le code source Python validé.

        Returns:
            Dictionnaire contenant:
            {
                "openapi_json": str,
                "sdk_python_code": str
            }
        """
        print(f"[{self.nom}] 📄 Génération de la spécification OpenAPI et du Client SDK...")

        system_prompt = """Tu es un expert en conception d'API et Génération de SDKs.
Examine le code Python fourni. Génère :
1. Une spécification OpenAPI 3.0 minimale valide au format JSON.
2. Un client SDK Python asynchrone utilisant `httpx` ou `urllib.request` pour consommer cette API.

Tu dois répondre UNIQUEMENT avec un objet JSON valide, sans texte avant ou après.
Structure JSON attendue :
{
  "openapi_json": { ... objet openapi 3.0 ... },
  "sdk_python_code": "import httpx\\n..."
}"""

        user_prompt = f"CODE SOURCE PYTHON :\n```python\n{python_code}\n```"

        try:
            raw_resp = call_llm(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                model=DEFAULT_MODEL,
                json_mode=True
            )
            result = json.loads(raw_resp)
            print(f"[{self.nom}] ✅ OpenAPI et Client SDK générés avec succès !")
            return result
        except Exception as e:
            print(f"[{self.nom}] ⚠️ Erreur lors de la génération SDK : {e}")
            return {
                "openapi_json": {"openapi": "3.0.0", "info": {"title": "API Autogénérée", "version": "1.0.0"}, "paths": {}},
                "sdk_python_code": "# Auto-generated SDK placeholder\nclass APIClient:\n    pass\n"
            }
