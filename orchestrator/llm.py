"""
Client LLM unifié pour le SuperAgent Morph.
Priorise Ollama (local, gratuit) avec fallback automatique sur Mistral API.

Usage:
    from orchestrator.llm import call_llm

    # Appel standard (Ollama d'abord, fallback Mistral)
    response = call_llm(
        system_prompt="Tu es un assistant utile.",
        user_prompt="Explique la relativité générale.",
        model="mistral:7b"  # ou "llama3.1:8b", "qwen2.5:7b", etc.
    )

    # Mode JSON structuré
    data = call_llm(..., json_mode=True)

Configuration:
    - OLLAMA_BASE_URL: URL de l'instance Ollama (défaut: http://localhost:11434)
    - MISTRAL_API_KEY: clé API Mistral pour le fallback
    - LLM_PROVIDER: forcer "ollama" ou "mistral" (défaut: auto)
"""
import json
import os
import urllib.request
from urllib.error import HTTPError, URLError
from typing import Optional, Dict, Any

# --- Configuration ---
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY", "")
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "auto")  # "auto", "ollama", "mistral"

# Modèle par défaut pour tous les agents (un seul endroit à modifier)
DEFAULT_MODEL = os.getenv("LLM_DEFAULT_MODEL", "llama3.2:latest")

# Températures par agent (centralisées pour ajustement facile)
TEMP_ECLAIREUR = 0.3    # Recherche/analyse — factuel
TEMP_ANALYSTE = 0.2     # Évaluation critique — très factuel
TEMP_CODEUR = 0.2       # Génération de code — précis
TEMP_REDACTEUR = 0.5    # Rédaction rapport — créatif
TEMP_DISTILLATEUR = 0.1 # Synthèse — très déterministe

# Mapping des noms de modèles entre Ollama et Mistral API
MODEL_MAP = {
    # Ollama models → Mistral API equivalents
    "llama3.2:latest": "mistral-small-latest",
    "llama3.1:8b": "mistral-small-latest",
    "llama3.1:70b": "mistral-large-latest",
    "qwen2.5:7b": "mistral-small-latest",
    "qwen2.5:32b": "mistral-medium-latest",
}


def _call_ollama(
    system_prompt: str,
    user_prompt: str,
    model: str = "mistral:7b",
    temperature: float = 0.3,
    json_mode: bool = False,
) -> Optional[str]:
    """
    Appelle une instance Ollama locale via son API REST.
    Retourne None si Ollama est inaccessible.
    """
    url = f"{OLLAMA_BASE_URL}/api/chat"

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    data = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "stream": False,
    }

    if json_mode:
        data["format"] = "json"

    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=120) as response:
            response_data = json.loads(response.read().decode("utf-8"))
            return response_data["message"]["content"]
    except (HTTPError, URLError, ConnectionRefusedError, TimeoutError) as e:
        print(f"[LLM] ⚠️ Ollama inaccessible ({e}). Fallback sur Mistral API.")
        return None
    except (KeyError, json.JSONDecodeError) as e:
        print(f"[LLM] ⚠️ Réponse Ollama invalide : {e}")
        return None


def _call_mistral(
    system_prompt: str,
    user_prompt: str,
    model: str = "mistral-small-latest",
    temperature: float = 0.3,
    json_mode: bool = False,
) -> str:
    """
    Appelle l'API Mistral Chat Completions.
    Lève RuntimeError si la clé API est manquante ou si l'appel échoue.
    """
    if not MISTRAL_API_KEY:
        raise RuntimeError(
            "❌ MISTRAL_API_KEY non définie et Ollama inaccessible."
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
        "Authorization": f"Bearer {MISTRAL_API_KEY}",
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


def call_llm(
    system_prompt: str,
    user_prompt: str,
    model: str = "mistral:7b",
    temperature: float = 0.3,
    json_mode: bool = False,
) -> str:
    """
    Appelle un LLM avec priorité Ollama (local, gratuit).
    Fallback automatique sur Mistral API si Ollama est indisponible.

    Args:
        system_prompt: Le prompt système définissant le rôle de l'agent.
        user_prompt: Le message utilisateur.
        model: Nom du modèle Ollama (ex: "mistral:7b", "llama3.1:8b", "qwen2.5:7b").
               En fallback Mistral, le modèle est automatiquement mappé.
        temperature: Contrôle la créativité (0.0 = déterministe, 1.0 = créatif).
        json_mode: Si True, force le modèle à répondre en JSON valide.

    Returns:
        Le contenu textuel de la réponse du modèle.

    Raises:
        RuntimeError: Si aucun provider n'est disponible.
    """
    provider = LLM_PROVIDER

    if provider == "auto" or provider == "ollama":
        # Essayer Ollama
        result = _call_ollama(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            model=model,
            temperature=temperature,
            json_mode=json_mode,
        )
        if result is not None:
            return result
        if provider == "ollama":
            raise RuntimeError(
                "❌ Ollama est configuré comme provider unique (LLM_PROVIDER=ollama) "
                "mais le serveur est inaccessible. Vérifie que Ollama tourne sur "
                f"{OLLAMA_BASE_URL}"
            )
        provider = "mistral"

    if provider == "mistral":
        # Mapper le nom du modèle Ollama vers Mistral API
        mistral_model = MODEL_MAP.get(model, model)
        return _call_mistral(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            model=mistral_model,
            temperature=temperature,
            json_mode=json_mode,
        )

    raise RuntimeError(f"❌ Provider LLM inconnu : {provider}")
