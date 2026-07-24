"""
Module client partagé pour les appels à l'API Mistral.
Utilisé par les agents Éclaireur et Analyste pour éviter la duplication de code.
"""

import os
import json
import urllib.request
from urllib.error import HTTPError, URLError


from orchestrator.circuit_breaker import mistral_circuit_breaker, CircuitBreakerOpenError


def _mistral_raw_request(
    system_prompt: str,
    user_prompt: str,
    model: str = "mistral-small-latest",
    temperature: float = 0.3,
    json_mode: bool = False
) -> str:
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
        with urllib.request.urlopen(req, timeout=30) as response:
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


def _mistral_fallback(
    system_prompt: str,
    user_prompt: str,
    model: str = "mistral-small-latest",
    temperature: float = 0.3,
    json_mode: bool = False
) -> str:
    """Fallback exécuté si le Circuit Breaker Mistral est OPEN ou échoue."""
    if json_mode:
        return json.dumps({
            "status": "FALLBACK_MODE",
            "message": "API Mistral momentanément indisponible (Circuit Breaker Actif). Réponse dégradée du système.",
            "data": []
        })
    return "⚠️ [Mode Dégradé] L'API Mistral est temporairement indisponible. Le système fonctionne en mode secours autonome."


def call_mistral(
    system_prompt: str,
    user_prompt: str,
    model: str = "mistral-small-latest",
    temperature: float = 0.3,
    json_mode: bool = False
) -> str:
    """
    Appelle l'API Mistral Chat Completions sous le contrôle du Circuit Breaker.
    """
    return mistral_circuit_breaker.call(
        _mistral_raw_request,
        system_prompt,
        user_prompt,
        model=model,
        temperature=temperature,
        json_mode=json_mode,
        fallback=_mistral_fallback
    )

