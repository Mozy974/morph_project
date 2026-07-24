"""
Moteur de recherche gratuit pour le SuperAgent Morph.
Remplace Tavily API par DuckDuckGo (zéro coût, zéro clé API).

Usage:
    from orchestrator.search import search_web

    results = search_web("dernières avancées IA 2026", max_results=5)
    for r in results["results"]:
        print(f"- {r['title']}: {r['url']}")

Fonctionne sans clé API, sans compte, sans limite de taux connue.
"""
import json
import urllib.request
import urllib.parse
from urllib.error import HTTPError, URLError
from typing import List, Dict, Any, Optional

# DuckDuckGo HTML endpoint (pas de clé API requise)
DDG_URL = "https://html.duckduckgo.com/html/"

# User-Agent réaliste pour éviter les blocages
USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"


def _extract_results(html: str) -> List[Dict[str, str]]:
    """
    Extrait les résultats de recherche depuis la page HTML de DuckDuckGo.
    """
    results = []
    # On cherche les blocs de résultats : <a rel="nofollow" class="result__a" href="...">
    # avec le titre dans le texte du lien, et le snippet dans <a class="result__snippet">
    
    lines = html.split("\n")
    current_result = {}
    in_result = False

    for line in lines:
        # Début d'un résultat : balise <a> avec class result__a
        if 'class="result__a"' in line:
            # Extraire l'URL
            href_start = line.find('href="')
            if href_start != -1:
                href_start += 6
                href_end = line.find('"', href_start)
                url = line[href_start:href_end]
                # Nettoyer les paramètres de tracking DuckDuckGo
                if "//duckduckgo.com/l/?uddg=" in url:
                    import urllib.parse as up
                    parsed = up.urlparse(url)
                    qs = up.parse_qs(parsed.query)
                    if "uddg" in qs:
                        url = urllib.parse.unquote(qs["uddg"][0])
                current_result["url"] = url

            # Extraire le titre (le texte entre > et </a>)
            title_start = line.find(">", href_end if 'href="' in line else 0) + 1
            title_end = line.find("</a>", title_start)
            if title_start > 0 and title_end > title_start:
                current_result["title"] = line[title_start:title_end].strip()
            
            in_result = True

        # Snippet : chercher class="result__snippet"
        elif 'class="result__snippet"' in line and in_result:
            # Extraire le texte entre > et </a>
            snippet_start = line.find(">", line.find('class="result__snippet"')) + 1
            snippet_end = line.find("</a>", snippet_start)
            if snippet_start > 0 and snippet_end > snippet_start:
                current_result["content"] = line[snippet_start:snippet_end].strip()
                # Nettoyer les balises HTML résiduelles
                current_result["content"] = current_result["content"].replace("<br>", "\n").replace("&quot;", '"').replace("&#x27;", "'")

        # Fin du bloc résultat
        elif '</div>' in line and in_result and "url" in current_result and "title" in current_result:
            if "content" not in current_result:
                current_result["content"] = ""
            results.append(current_result)
            current_result = {}
            in_result = False

    return results


from orchestrator.circuit_breaker import tavily_circuit_breaker


def _search_web_raw(query: str, max_results: int = 5) -> Dict[str, Any]:
    if not query or not query.strip():
        return {
            "success": False,
            "query": query,
            "results": [],
            "error": "Requête vide.",
        }

    max_results = min(max_results, 10)
    data = urllib.parse.urlencode({"q": query}).encode("utf-8")
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
        "Content-Type": "application/x-www-form-urlencoded",
    }

    req = urllib.request.Request(
        DDG_URL,
        data=data,
        headers=headers,
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            html = response.read().decode("utf-8", errors="replace")

        all_results = _extract_results(html)
        clean_results = [
            {
                "title": r.get("title", "Sans titre"),
                "url": r.get("url", ""),
                "content": r.get("content", ""),
            }
            for r in all_results[:max_results]
        ]

        if not clean_results:
            return {
                "success": False,
                "query": query,
                "results": [],
                "error": "Aucun résultat trouvé.",
            }

        return {
            "success": True,
            "query": query,
            "results": clean_results,
            "error": None,
        }
    except Exception as e:
        raise RuntimeError(f"Erreur recherche web: {str(e)}") from e


def _search_web_fallback(query: str, max_results: int = 5) -> Dict[str, Any]:
    """Fallback exécuté si la recherche web disjoncte (Circuit Breaker OPEN)."""
    return {
        "success": False,
        "query": query,
        "results": [
            {
                "title": "Mode Dégradé RAG Local",
                "url": "local://chromadb_fallback",
                "content": "Recherche web temporairement désactivée (Circuit Breaker Actif). Basculement vers la base vectorielle locale."
            }
        ],
        "error": "Circuit Breaker Web Search actif - Mode dégradé."
    }


def search_web(query: str, max_results: int = 5) -> Dict[str, Any]:
    """
    Effectue une recherche Web sous le contrôle du Circuit Breaker.
    """
    return tavily_circuit_breaker.call(
        _search_web_raw,
        query,
        max_results=max_results,
        fallback=_search_web_fallback
    )

