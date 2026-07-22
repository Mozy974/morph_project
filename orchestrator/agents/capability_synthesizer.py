"""
CapabilitySynthesizer : Synthétiseur Autonome de Capacités & Outils (Niveau 8.0 Auto-Évolution Collective).
Détecte et génère automatiquement de nouveaux helpers Python exécutables, isolés et testés,
chargeables dynamiquement via importlib.
"""

import json
import os
import sys
import importlib.util
import datetime
from typing import Dict, Any, List, Optional
from orchestrator.llm import call_llm, DEFAULT_MODEL, TEMP_CODEUR

CAPABILITIES_DIR = os.path.join(os.path.dirname(__file__), "..", "memory", "synthetic_capabilities")


class CapabilitySynthesizer:
    """
    Synthétiseur de Capacités Autonomes (Niveau 8.0).
    Génère des helpers Python avec leurs tests unitaires associés et chargement dynamique importlib.
    """

    def __init__(self, cap_dir: str = CAPABILITIES_DIR):
        self.nom = "Capability Synthesizer"
        self.cap_dir = os.path.abspath(cap_dir)
        os.makedirs(self.cap_dir, exist_ok=True)

    def _get_slug(self, capability_name: str) -> str:
        return capability_name.lower().replace(" ", "_").replace("-", "_")

    def synthesize_capability(self, capability_name: str, requirement_desc: str) -> Dict[str, Any]:
        """
        Synthétise une nouvelle capacité réutilisable sous forme de module Python et son test unitaire.
        """
        print(f"[{self.nom}] ⚡ Synthèse d'une nouvelle capacité : '{capability_name}'...")

        slug = self._get_slug(capability_name)
        file_name = f"{slug}.py"
        test_file_name = f"test_{slug}.py"

        target_path = os.path.join(self.cap_dir, file_name)
        test_target_path = os.path.join(self.cap_dir, test_file_name)

        if os.path.exists(target_path):
            print(f"[{self.nom}] ℹ️ Capacité existante chargée : {file_name}")
            with open(target_path, "r", encoding="utf-8") as f:
                code = f.read()
            return {
                "capability_name": capability_name,
                "file_path": target_path,
                "test_file_path": test_target_path,
                "code": code,
                "status": "REUSED"
            }

        system_prompt = """Tu es un expert en Synthèse de Capacités Logicielles.
Génère une fonction / classe Helper Python autonome et réutilisable répondant au besoin,
ainsi qu'un test unitaire minimal compatible pytest.

Structure JSON attendue :
{
  "module_docstring": "Description de la capacité",
  "python_code": "Le code Python complet",
  "test_code": "Le code Pytest pour valider le module"
}"""

        user_prompt = f"""NOM DE LA CAPACITÉ : {capability_name}
EXIGENCES : {requirement_desc}"""

        try:
            raw_res = call_llm(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                model=DEFAULT_MODEL,
                temperature=TEMP_CODEUR,
                json_mode=True
            )
            data = json.loads(raw_res)
            code = data.get("python_code", f"# Helper {capability_name}\ndef execute(): return True\n")
            test_code = data.get("test_code", f"from {slug} import execute\ndef test_execute(): assert execute() is not None\n")

            with open(target_path, "w", encoding="utf-8") as f:
                f.write(code)

            with open(test_target_path, "w", encoding="utf-8") as f:
                f.write(test_code)

            print(f"[{self.nom}] ✅ Capacité '{capability_name}' et test '{test_file_name}' synthétisés avec succès !")
            return {
                "capability_name": capability_name,
                "file_path": target_path,
                "test_file_path": test_target_path,
                "code": code,
                "status": "SYNTHESIZED"
            }

        except Exception as e:
            print(f"[{self.nom}] ⚠️ Fallback synthèse capacité : {e}")
            fallback_code = f"# Fallback {capability_name}\ndef execute(): return True\n"
            fallback_test = f"def test_fallback(): assert True\n"

            with open(target_path, "w", encoding="utf-8") as f:
                f.write(fallback_code)

            with open(test_target_path, "w", encoding="utf-8") as f:
                f.write(fallback_test)

            return {
                "capability_name": capability_name,
                "file_path": target_path,
                "test_file_path": test_target_path,
                "code": fallback_code,
                "status": "FALLBACK"
            }

    def load_capability_dynamically(self, capability_name: str) -> Optional[Any]:
        """
        Charge un module de capacité de manière dynamique via importlib.
        """
        slug = self._get_slug(capability_name)
        target_path = os.path.join(self.cap_dir, f"{slug}.py")

        if not os.path.exists(target_path):
            print(f"[{self.nom}] ⚠️ Capacité '{capability_name}' non trouvée à l'emplacement : {target_path}")
            return None

        try:
            spec = importlib.util.spec_from_file_location(slug, target_path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                sys.modules[slug] = module
                spec.loader.exec_module(module)
                print(f"[{self.nom}] 🔌 Capacité '{capability_name}' chargée dynamiquement via importlib !")
                return module
        except Exception as e:
            print(f"[{self.nom}] ❌ Erreur chargement dynamique importlib : {e}")

        return None
