"""
Module RAG Hybride (Local ChromaDB + Web DuckDuckGo / Tavily)

Ce module fournit l'infrastructure RAG complète decouplée de toute interface utilisateur :
- Ingestion et indexation sémantique de documents texte et markdown avec ChromaDB & Mistral Embeddings.
- Recherche web via DuckDuckGo et Tavily (fallback).
- Métriques Prometheus intégrées pour le suivi de la latence et des requêtes en production.
"""

import os
import glob
import time
import logging
from typing import List, Dict, Tuple, Optional, Any

# Correctif SQLite pour ChromaDB si nécessaire
try:
    __import__('pysqlite3')
    import sys
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
except Exception:
    pass

try:
    from mistralai import Mistral
except ImportError:
    try:
        from mistralai.client import MistralClient as Mistral
    except ImportError:
        try:
            from mistralai.client import Mistral
        except ImportError:
            Mistral = None


from prometheus_client import Counter, Histogram

try:
    try:
        from ddgs import DDGS
    except ImportError:
        from duckduckgo_search import DDGS
    HAS_DDG = True
except ImportError:
    HAS_DDG = False


try:
    from tavily import TavilyClient
    HAS_TAVILY = True
except ImportError:
    HAS_TAVILY = False

logger = logging.getLogger(__name__)

# --- MÉTRIQUES PROMETHEUS ---
RAG_QUERIES_TOTAL = Counter(
    'rag_queries_total',
    'Nombre total de requêtes RAG exécutées',
    ['mode']
)
RAG_QUERY_DURATION_SECONDS = Histogram(
    'rag_query_duration_seconds',
    'Durée d\'exécution des requêtes RAG en secondes',
    ['mode']
)
RAG_SEARCH_COUNT = Counter(
    'rag_search_count',
    'Nombre de recherches exécutées par source',
    ['source']
)


def load_documents(dossier: str) -> Tuple[List[str], List[str]]:
    """Charge et découpe les fichiers .txt et .md d'un dossier en paragraphes.

    Args:
        dossier (str): Chemin du répertoire contenant les documents.

    Returns:
        Tuple[List[str], List[str]]: Un tuple (liste des textes, liste des métadonnées de source).
    """
    documents, sources = [], []
    if not os.path.exists(dossier):
        os.makedirs(dossier, exist_ok=True)
        return documents, sources

    fichiers = glob.glob(os.path.join(dossier, "*.txt")) + glob.glob(os.path.join(dossier, "*.md"))
    for fichier in fichiers:
        try:
            with open(fichier, "r", encoding="utf-8") as f:
                contenu = f.read()
                paragraphes = [p.strip() for p in contenu.split("\n\n") if len(p.strip()) > 50]
                for i, para in enumerate(paragraphes):
                    documents.append(para)
                    sources.append(f"{os.path.basename(fichier)} - bloc {i}")
        except Exception as e:
            logger.error(f"Erreur lors de la lecture de {fichier}: {e}")

    return documents, sources


class HybridRAGPipeline:
    """Pipeline RAG Hybride combinant recherche vectorielle locale et recherche Web.

    Attributes:
        docs_folder (str): Dossier contenant les documents locaux.
        api_key (str): Clé API Mistral.
        tavily_key (str): Clé API Tavily.
    """

    def __init__(
        self,
        mistral_api_key: Optional[str] = None,
        tavily_api_key: Optional[str] = None,
        docs_folder: str = "mes_documents"
    ):
        """Initialise les clients API et les variables de stockage."""
        self.docs_folder = docs_folder
        self.api_key = mistral_api_key or os.environ.get("MISTRAL_API_KEY")
        self.tavily_key = tavily_api_key or os.environ.get("TAVILY_API_KEY") or os.environ.get("SEARCH_API_KEY")

        if self.api_key:
            self.mistral_client = Mistral(api_key=self.api_key)
        else:
            self.mistral_client = None

        if HAS_TAVILY and self.tavily_key:
            try:
                self.tavily_client = TavilyClient(api_key=self.tavily_key)
            except Exception as e:
                logger.warning(f"Impossible d'initialiser TavilyClient: {e}")
                self.tavily_client = None
        else:
            self.tavily_client = None

        self.db_client = None
        self.collection = None
        self.is_indexed = False

    def init_vector_store(self, collection_name: str = "base_personnelle") -> bool:
        """Initialise et alimente la base vectorielle ChromaDB avec les documents locaux.

        Args:
            collection_name (str): Nom de la collection ChromaDB.

        Returns:
            bool: True si l'indexation a réussi, False sinon.
        """
        if not self.mistral_client:
            logger.error("Mistral Client non initialisé. Clé API manquante.")
            return False

        self.db_client = chromadb.Client()
        try:
            self.db_client.delete_collection(collection_name)
        except Exception:
            pass

        self.collection = self.db_client.create_collection(name=collection_name)
        documents, sources = load_documents(self.docs_folder)

        if not documents:
            self.is_indexed = False
            return False

        try:
            embeddings_resp = self.mistral_client.embeddings.create(
                model="mistral-embed",
                inputs=documents
            )
            embeddings = [e.embedding for e in embeddings_resp.data]

            self.collection.add(
                embeddings=embeddings,
                documents=documents,
                metadatas=[{"source": s} for s in sources],
                ids=[f"doc_{i}" for i in range(len(documents))]
            )
            self.is_indexed = True
            return True
        except Exception as e:
            logger.error(f"Erreur lors de l'indexation ChromaDB: {e}")
            self.is_indexed = False
            return False

    def search_duckduckgo(self, query: str, max_results: int = 3) -> List[Dict[str, str]]:
        """Recherche des données sur le Web via DuckDuckGo.

        Args:
            query (str): Requête de recherche.
            max_results (int): Nombre maximum de résultats.

        Returns:
            List[Dict[str, str]]: Liste de résultats contenant title, snippet, et url.
        """
        if not HAS_DDG:
            logger.warning("duckduckgo_search n'est pas installé.")
            return []

        RAG_SEARCH_COUNT.labels(source="duckduckgo").inc()
        try:
            results = []
            with DDGS() as ddgs:
                ddg_gen = ddgs.text(query, max_results=max_results)
                if ddg_gen:
                    for r in ddg_gen:
                        results.append({
                            "title": r.get("title", ""),
                            "snippet": r.get("body", ""),
                            "url": r.get("href", "")
                        })
            return results
        except Exception as e:
            logger.error(f"Erreur recherche DuckDuckGo: {e}")
            return []

    def search_tavily(self, query: str, max_results: int = 3) -> List[Dict[str, str]]:
        """Recherche des données sur le Web via Tavily.

        Args:
            query (str): Requête de recherche.
            max_results (int): Nombre maximum de résultats.

        Returns:
            List[Dict[str, str]]: Liste de résultats contenant title, snippet, et url.
        """
        if not self.tavily_client:
            return []
        
        RAG_SEARCH_COUNT.labels(source="tavily").inc()
        try:
            search_data = self.tavily_client.search(query=query, search_depth="basic")
            results = []
            for item in search_data.get("results", [])[:max_results]:
                results.append({
                    "title": item.get("title", ""),
                    "snippet": item.get("content", ""),
                    "url": item.get("url", "")
                })
            return results
        except Exception as e:
            logger.error(f"Erreur recherche Tavily: {e}")
            return []

    def search_local(self, query: str, n_results: int = 3) -> List[Dict[str, str]]:
        """Effectue une recherche sémantique dans la base vectorielle locale.

        Args:
            query (str): Requête utilisateur.
            n_results (int): Nombre de fragments à retourner.

        Returns:
            List[Dict[str, str]]: Liste de résultats avec la source et le contenu.
        """
        if not self.collection or not self.is_indexed or not self.mistral_client:
            return []

        RAG_SEARCH_COUNT.labels(source="chromadb").inc()
        try:
            prompt_emb = self.mistral_client.embeddings.create(
                model="mistral-embed",
                inputs=[query]
            ).data[0].embedding

            res = self.collection.query(query_embeddings=[prompt_emb], n_results=n_results)
            results = []
            if res and res.get("documents") and res["documents"][0]:
                for doc, meta in zip(res["documents"][0], res["metadatas"][0]):
                    results.append({
                        "source": meta.get("source", "Document local"),
                        "content": doc
                    })
            return results
        except Exception as e:
            logger.error(f"Erreur recherche locale ChromaDB: {e}")
            return []

    def decide_search_mode(self, query: str) -> str:
        """Détermine intelligemment le mode de recherche (WEB, LOCAL, HYBRID).

        Args:
            query (str): Requête utilisateur.

        Returns:
            str: "WEB", "LOCAL", ou "HYBRID".
        """
        if not self.mistral_client:
            return "HYBRID"

        prompt = (
            "Analyse la question suivante et détermine le mode de recherche approprié.\n"
            "Réponds par 'WEB' si la question concerne l'actualité/web, 'LOCAL' si la question concerne la documentation interne/personnelle, "
            "ou 'HYBRID' s'il faut consulter les deux.\n"
            f"Question : {query}\nChoix (WEB/LOCAL/HYBRID) :"
        )
        try:
            resp = self.mistral_client.chat.complete(
                model="mistral-small-latest",
                messages=[{"role": "user", "content": prompt}]
            )
            decision = resp.choices[0].message.content.strip().upper()
            if "WEB" in decision:
                return "WEB"
            elif "LOCAL" in decision:
                return "LOCAL"
            return "HYBRID"
        except Exception:
            return "HYBRID"

    def hybrid_query(
        self,
        query: str,
        search_mode: str = "auto",
        max_web_results: int = 3,
        n_local_results: int = 3
    ) -> Dict[str, Any]:
        """Exécute la stratégie RAG hybride et calcule les métriques de performance.

        Args:
            query (str): Question posée par l'utilisateur.
            search_mode (str): Mode de recherche ("AUTO", "HYBRID", "WEB", "LOCAL").
            max_web_results (int): Nombre de résultats web à extraire.
            n_local_results (int): Nombre de fragments locaux à extraire.

        Returns:
            Dict[str, Any]: Dictionnaire contenant mode_used, local_results, web_results et context.
        """
        start_time = time.time()
        mode = search_mode.upper()
        if mode == "AUTO":
            mode = self.decide_search_mode(query)

        RAG_QUERIES_TOTAL.labels(mode=mode).inc()

        local_results = []
        web_results = []

        if mode in ("LOCAL", "HYBRID"):
            local_results = self.search_local(query, n_results=n_local_results)

        if mode in ("WEB", "HYBRID") or not local_results:
            web_results = self.search_duckduckgo(query, max_results=max_web_results)
            if not web_results and self.tavily_client:
                web_results = self.search_tavily(query, max_results=max_web_results)

        context_parts = []
        if local_results:
            context_parts.append("--- CONTEXTE DOCUMENTS LOCAUX ---")
            for item in local_results:
                context_parts.append(f"[Source: {item['source']}]\n{item['content']}")

        if web_results:
            context_parts.append("--- CONTEXTE RECHERCHE WEB ---")
            for item in web_results:
                context_parts.append(f"[Web: {item['title']}] ({item['url']})\n{item['snippet']}")

        formatted_context = "\n\n".join(context_parts) if context_parts else "Aucun contexte trouvé."

        duration = time.time() - start_time
        RAG_QUERY_DURATION_SECONDS.labels(mode=mode).observe(duration)

        return {
            "mode_used": mode,
            "local_results": local_results,
            "web_results": web_results,
            "context": formatted_context,
            "duration_seconds": round(duration, 3)
        }

    def generate_response(
        self,
        query: str,
        context: str,
        history: Optional[List[Dict[str, str]]] = None,
        model: str = "mistral-small-latest"
    ) -> str:
        """Génère la réponse RAG synthétique finale à partir du contexte consolidé.

        Args:
            query (str): Question posée par l'utilisateur.
            context (str): Contexte formaté.
            history (Optional[List[Dict[str, str]]]): Historique de conversation.
            model (str): Modèle Mistral à utiliser.

        Returns:
            str: Réponse textuelle générée par l'IA.
        """
        if not self.mistral_client:
            return "Erreur : Client Mistral non configuré."

        system_prompt = (
            f"Tu es un expert technique. Réponds à la question en utilisant précisément ce contexte :\n\n"
            f"{context}\n\n"
            "IMPORTANT : À la fin de ta réponse, liste toujours clairement les sources utilisées sous forme de puces."
        )

        messages = [{"role": "system", "content": system_prompt}]
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": query})

        try:
            response = self.mistral_client.chat.complete(model=model, messages=messages)
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Erreur lors de la génération de réponse Mistral: {e}")
            return f"Erreur lors de la génération de la réponse : {e}"
