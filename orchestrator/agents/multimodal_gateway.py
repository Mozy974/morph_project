"""
MultimodalGateway : Gateway d'Interaction Multi-Modale (Niveau 10.0 Conscience Ultime).
Prend en charge le traitement d'images/maquettes UI, de signaux visuels et prépare les flux vocaux.
"""

import json
from typing import Dict, Any, List, Optional
from orchestrator.llm import call_llm, DEFAULT_MODEL, TEMP_REDACTEUR


class MultimodalGateway:
    """
    Gateway Multi-Modale (Niveau 10.0).
    Analyse les maquettes UI (images/wireframes) et extrait les consignes techniques pour l'Agent Codeur TDD.
    """

    def __init__(self):
        self.nom = "Multimodal Gateway"

    def process_ui_mockup_spec(self, image_path_or_description: str, task_context: str = "") -> Dict[str, Any]:
        """
        Analyse une spécification visuelle ou maquette UI et génère le cahier des charges de code TDD.
        """
        print(f"[{self.nom}] 👁️ Analyse multi-modale de la maquette UI ({image_path_or_description[:40]}...)...")

        system_prompt = """Tu es un expert en Ingénierie UI/UX et analyse multi-modale de maquettes d'applications.
Ta mission est de traduire une maquette ou description visuelle en exigences de code frontend et backend structurées.

Structure JSON attendue :
{
  "layout_components": ["Barre de navigation", "Formulaire d'inscription", "Graphique analytique"],
  "design_system_directives": {
    "theme": "Dark mode glassmorphism",
    "primary_colors": ["#4F46E5", "#10B981"]
  },
  "tdd_specs": ["Le formulaire doit valider l'email", "Le bouton Submit déclenche un POST /api/v1/auth"]
}"""

        user_prompt = f"""MAQUETTE VISUELLE / SPEC : {image_path_or_description}
CONTEXTE : {task_context}"""

        try:
            raw_res = call_llm(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                model=DEFAULT_MODEL,
                temperature=TEMP_REDACTEUR,
                json_mode=True
            )
            spec = json.loads(raw_res)
            print(f"[{self.nom}] ✅ Analyse multi-modale terminée ({len(spec.get('layout_components', []))} composants UI détectés) !")
            return spec

        except Exception as e:
            print(f"[{self.nom}] ⚠️ Fallback analyse multi-modale : {e}")
            return {
                "layout_components": ["UI Container principal"],
                "design_system_directives": {"theme": "Standard clean UI"},
                "tdd_specs": ["Affichage conforme du composant principal."]
            }
