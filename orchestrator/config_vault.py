"""
Gestionnaire de Secrets et Abstraction Vault (orchestrator/config_vault.py).
Permet de récupérer les clés d'API et identifiants sensibles depuis HashiCorp Vault,
les secrets montés Kubernetes (/vault/secrets/), avec fallback sécurisé sur l'environnement local.
"""

import os
from typing import Optional


def get_secret(key_name: str, default_value: Optional[str] = None) -> Optional[str]:
    """
    Récupère dynamiquement un secret depuis Vault (/vault/secrets/key_name)
    ou l'environnement.
    """
    # 1. Vérification des secrets montés par HashiCorp Vault Agent / Kubernetes
    vault_path = f"/vault/secrets/{key_name.lower()}"
    if os.path.exists(vault_path):
        try:
            with open(vault_path, "r", encoding="utf-8") as f:
                val = f.read().strip()
                if val:
                    return val
        except Exception:
            pass

    # 2. Variable d'environnement classique (dev / staging)
    env_val = os.getenv(key_name)
    if env_val:
        return env_val

    # 3. Fallback sur le paramètre par défaut
    return default_value


def get_mistral_api_key() -> Optional[str]:
    return get_secret("MISTRAL_API_KEY")


def get_tavily_api_key() -> Optional[str]:
    return get_secret("TAVILY_API_KEY") or get_secret("SEARCH_API_KEY")
