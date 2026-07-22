"""
Module de notifications Webhook multi-plateformes (Slack, Discord, Custom) (orchestrator/notifier.py).
Envoie des alertes en temps réel sur les événements clés du SuperAgent.
"""

import os
import json
import urllib.request
from typing import Dict, Any, Optional


class NotificationManager:
    def __init__(self, webhook_url: Optional[str] = None):
        self.webhook_url = webhook_url or os.getenv("WEBHOOK_URL", "")

    def send_notification(self, title: str, message: str, color: str = "#36a64f", metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Envoie une notification formatée vers un webhook (Slack, Discord ou Webhook générique).
        """
        if not self.webhook_url:
            # Mode silencieux si aucun webhook n'est configuré
            return False

        payload = {
            "title": title,
            "text": message,
            "color": color,
            "metadata": metadata or {}
        }

        # Détection du format (Discord vs Slack/Generic)
        if "discord.com" in self.webhook_url:
            formatted_payload = {
                "embeds": [{
                    "title": title,
                    "description": message,
                    "color": 3066993 if color == "#36a64f" else 15158332,
                    "fields": [
                        {"name": k, "value": str(v), "inline": True}
                        for k, v in (metadata or {}).items()
                    ]
                }]
            }
        else:
            # Format Slack / Generic Webhook
            formatted_payload = payload

        try:
            data_bytes = json.dumps(formatted_payload).encode("utf-8")
            req = urllib.request.Request(
                self.webhook_url,
                data=data_bytes,
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                print(f"[Notifier] 🔔 Notification envoyée avec succès (Status: {resp.status})")
                return True
        except Exception as e:
            print(f"[Notifier] ⚠️ Échec de l'envoi de la notification Webhook : {e}")
            return False

    def notify_job_start(self, job_id: str, task_name: str):
        return self.send_notification(
            title=f"🚀 Nouveau Job SuperAgent [{job_id[:8]}]",
            message=f"Tâche : {task_name}",
            color="#3498db",
            metadata={"Job ID": job_id[:8], "Status": "STARTED"}
        )

    def notify_job_success(self, job_id: str, score: int, duration_s: float):
        return self.send_notification(
            title=f"🎉 Job SuperAgent Réussi [{job_id[:8]}]",
            message=f"Le job a été validé avec un score Analyste de **{score}/100** !",
            color="#2ecc71",
            metadata={"Job ID": job_id[:8], "Score": f"{score}/100", "Durée": f"{duration_s}s"}
        )

    def notify_hitl_pending(self, job_id: str, skill_key: str):
        return self.send_notification(
            title=f"👤 Modération HITL Requis [{job_id[:8]}]",
            message=f"Un nouveau skill distillé ('{skill_key}') nécessite la modération de l'utilisateur.",
            color="#f39c12",
            metadata={"Job ID": job_id[:8], "Skill": skill_key}
        )
