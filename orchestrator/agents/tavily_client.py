"""
Module client pour l'API Tavily (Recherche Web en temps réel).
"""

import os
import json
import urllib.request
from urllib.error import HTTPError, URLError


def search_web(query: str, max_results: int = 5) -> dict:
    """
    Effectue une recherche sur le Web via l'API Tavily.

    Args:
        query: Les termes de recherche.
        max_results: Nombre maximal de résultats à récupérer (défaut: 5).

    Returns:
        Un dictionnaire contenant les résultats de recherche :
        {
            "success": True/False,
            "query": query,
            "results": [
                {"title": "...", "url": "...", "content": "..."}, ...
            ],
            "error": None ou message d'erreur
        }
    """
    api_key = os.environ.get("TAVILY_API_KEY") or os.environ.get("SEARCH_API_KEY")
    
    if not api_key or api_key == "votre_cle_api_externe":
        return {
            "success": False,
            "query": query,
            "results": [],
            "error": "TAVILY_API_KEY non définie ou non valide."
        }

    url = "https://api.tavily.com/search"
    payload = {
        "api_key": api_key,
        "query": query,
        "search_depth": "basic",
        "max_results": max_results,
        "include_answer": False
    }

    headers = {
        "Content-Type": "application/json"
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            raw_results = res_data.get("results", [])
            
            clean_results = [
                {
                    "title": item.get("title", "Sans titre"),
                    "url": item.get("url", ""),
                    "content": item.get("content", "")
                }
                for item in raw_results
            ]
            
            return {
                "success": True,
                "query": query,
                "results": clean_results,
                "error": None
            }
    except HTTPError as e:
        error_body = e.read().decode("utf-8")
        return {
            "success": False,
            "query": query,
            "results": [],
            "error": f"Erreur HTTP {e.code}: {error_body}"
        }
    except URLError as e:
        return {
            "success": False,
            "query": query,
            "results": [],
            "error": f"Erreur de connexion : {e.reason}"
        }
    except Exception as e:
        return {
            "success": False,
            "query": query,
            "results": [],
            "error": str(e)
        }
