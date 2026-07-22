"""
Module client partagé pour les appels à l'API Mistral.
Utilisé par les agents Éclaireur et Analyste pour éviter la duplication de code.
"""

import os
import json
import urllib.request
from urllib.error import HTTPError, URLError


def call_mistral(
    system_prompt: str,
    user_prompt: str,
    model: str = "mistral-small-latest",
    temperature: float = 0.3,
    json_mode: bool = False
) -> str:
    """
    Appelle l'API Mistral Chat Completions et retourne le contenu de la réponse.

    Args:
        system_prompt: Le prompt système qui définit le rôle de l'agent.
        user_prompt: Le message utilisateur à envoyer.
        model: Le modèle Mistral à utiliser.
        temperature: Contrôle la créativité (0.0 = déterministe, 1.0 = créatif).
        json_mode: Si True, force le modèle à répondre en JSON valide.

    Returns:
        Le contenu textuel de la réponse du modèle.

    Raises:
        RuntimeError: Si la clé API est manquante ou si l'appel échoue.
    """
    api_key = os.environ.get("MISTRAL_API_KEY")
    if not api_key:
        raise RuntimeError(
            "❌ MISTRAL_API_KEY n'est pas définie dans les variables d'environnement."
        )

    url = "https://api.mistral.ai/v1/chat/completions"

    data = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": temperature,
    }

    # Active le mode JSON structuré si demandé
    if json_mode:
        data["response_format"] = {"type": "json_object"}

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode("utf-8"),
        headers=headers,
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=120) as response:
            response_data = json.loads(response.read().decode("utf-8"))
            return response_data["choices"][0]["message"]["content"]
    except HTTPError as e:
        error_body = e.read().decode("utf-8")
        raise RuntimeError(
            f"❌ Erreur API Mistral HTTP {e.code} : {error_body}"
        ) from e
    except URLError as e:
        raise RuntimeError(
            f"❌ Erreur de connexion à l'API Mistral : {e.reason}"
        ) from e
