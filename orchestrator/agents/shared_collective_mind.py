"""
SharedCollectiveMind : Conscience Partagée & Vecteur d'État Global (Niveau 9.0 Conscience Collective).
Espace de représentation mentale unifié synchronisant la mémoire de travail et les croyances du Swarm.
"""

import json
import os
import datetime
from typing import Dict, Any, List, Optional
from orchestrator.memory.event_bus import publish_event

MIND_STATE_FILE = os.path.join(os.path.dirname(__file__), "..", "memory", "collective_mind_state.json")


class SharedCollectiveMind:
    """
    Conscience Partagée du Swarm (Niveau 9.0).
    Maintient un état mental unifié et synchronisé en mémoire, Redis et fichier snapshot.
    """

    def __init__(self, store_path: str = MIND_STATE_FILE):
        self.nom = "Shared Collective Mind"
        self.store_path = os.path.abspath(store_path)
        self.mind_state: Dict[str, Any] = self._load_mind_state()

    def _load_mind_state(self) -> Dict[str, Any]:
        if os.path.exists(self.store_path):
            try:
                with open(self.store_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"[{self.nom}] ⚠️ Erreur chargement conscience collective : {e}")
        return {
            "version": 1.0,
            "collective_focus": "System Initialization",
            "active_beliefs": [],
            "shared_context": {},
            "updated_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }

    def _save_mind_state(self) -> None:
        try:
            os.makedirs(os.path.dirname(self.store_path), exist_ok=True)
            with open(self.store_path, "w", encoding="utf-8") as f:
                json.dump(self.mind_state, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[{self.nom}] ❌ Erreur sauvegarde conscience collective : {e}")

    def update_mind_state(
        self,
        focus: str,
        belief_updates: Optional[List[str]] = None,
        context_data: Optional[Dict[str, Any]] = None,
        job_id: str = "collective_mind"
    ) -> Dict[str, Any]:
        """
        Met à jour la conscience collective partagée et informe la flotte via le bus d'événements.
        """
        self.mind_state["collective_focus"] = focus
        if belief_updates:
            self.mind_state["active_beliefs"].extend(belief_updates)
            # Conserver les 20 croyances les plus récentes
            self.mind_state["active_beliefs"] = self.mind_state["active_beliefs"][-20:]

        if context_data:
            self.mind_state["shared_context"].update(context_data)

        self.mind_state["updated_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        self._save_mind_state()

        print(f"[{self.nom}] 🧠 Conscience collective mise à jour : Focus='{focus}'")
        publish_event(
            job_id=job_id,
            event_type="collective_mind_update",
            message=f"🧠 Conscience partagée synchronisée : '{focus}'",
            payload={"focus": focus, "active_beliefs_count": len(self.mind_state["active_beliefs"])}
        )

        return self.mind_state

    def get_current_mind(self) -> Dict[str, Any]:
        """Retourne l'état actuel de la conscience collective."""
        return self.mind_state
