"""
Module de Maintenance Prédictive pour ChromaDB (orchestrator/memory/chroma_maintenance.py).

Fournit les fonctionnalités de :
- Audit de Santé Sémantique (Densité vectorielle, Dérive Z-score, Score de Santé RAG 0-1).
- Nettoyage automatique des doublons sémantiques (Cosine Similarity > threshold).
- Pruning temporel (archivage à froid des documents inactifs).
- Détection du besoin de ré-indexation (+20% de croissance d'index).
- Mise à jour des métriques Prometheus pour l'observabilité Grafana.
"""

import os
import json
import logging
import time
from typing import Dict, List, Any, Optional, Tuple
import numpy as np

try:
    __import__('pysqlite3')
    import sys
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
except Exception:
    pass

import chromadb

from orchestrator.metrics import (
    CHROMADB_HEALTH_SCORE,
    CHROMADB_DRIFT_ZSCORE,
    CHROMADB_DUPLICATES_CLEANED
)

logger = logging.getLogger(__name__)


class ChromaMaintenanceManager:
    """Gestionnaire de maintenance prédictive pour bases vectorielles ChromaDB."""

    def __init__(
        self,
        db_path: str = "./chroma_db",
        cold_storage_dir: str = "./orchestrator/memory/backups/cold_storage",
        baseline_vector_mean: Optional[np.ndarray] = None
    ):
        self.db_path = db_path
        self.cold_storage_dir = cold_storage_dir
        self.baseline_vector_mean = baseline_vector_mean
        os.makedirs(self.cold_storage_dir, exist_ok=True)

    def get_client(self) -> chromadb.ClientAPI:
        """Retourne un client ChromaDB persistant ou éphémère."""
        if os.path.exists(self.db_path):
            return chromadb.PersistentClient(path=self.db_path)
        return chromadb.Client()

    def audit_health(
        self,
        collection: Any,
        baseline_mean: Optional[np.ndarray] = None
    ) -> Dict[str, Any]:
        """
        Audit la santé sémantique de la collection ChromaDB.

        Calculs :
        1. Distribution des vecteurs (moyenne et variance dans l'espace).
        2. Dérive sémantique (Z-score de distance euclidienne / cosinus vs baseline).
        3. Calcul d'un Score de Santé normalisé (0.0 à 1.0).
        """
        data = collection.get(include=['embeddings', 'metadatas', 'documents'])
        embeddings = data.get('embeddings')

        if embeddings is None or len(embeddings) == 0:
            logger.info("Collection vide ou sans embeddings générés.")
            health_score = 1.0
            drift_zscore = 0.0
            CHROMADB_HEALTH_SCORE.set(health_score)
            CHROMADB_DRIFT_ZSCORE.set(drift_zscore)
            return {
                "health_score": health_score,
                "drift_zscore": drift_zscore,
                "total_vectors": 0,
                "vector_dim": 0,
                "status": "HEALTHY",
                "recommended_action": "NO_ACTION"
            }

        matrix = np.array(embeddings)
        total_vectors, dim = matrix.shape

        # 1. Calcul de la moyenne et de la dispersion actuelle
        current_mean = np.mean(matrix, axis=0)
        current_std = np.std(matrix, axis=0)
        avg_dispersion = float(np.mean(current_std))

        # 2. Détection de dérive (Z-score)
        ref_mean = baseline_mean if baseline_mean is not None else self.baseline_vector_mean
        if ref_mean is not None and ref_mean.shape == current_mean.shape:
            dist = np.linalg.norm(current_mean - ref_mean)
            norm_factor = np.linalg.norm(ref_mean) + 1e-8
            drift_zscore = float(dist / (np.mean(current_std) + 1e-8))
        else:
            # Sans baseline, on enregistre la moyenne actuelle comme baseline initiale
            self.baseline_vector_mean = current_mean
            drift_zscore = 0.0

        # 3. Ratio de dispersion / régularité
        dispersion_penalty = min(0.3, max(0.0, (avg_dispersion - 0.5) * 0.5))
        drift_penalty = min(0.4, max(0.0, (drift_zscore - 1.0) * 0.15))

        health_score = max(0.0, min(1.0, 1.0 - dispersion_penalty - drift_penalty))

        # Mise à jour des métriques Prometheus
        CHROMADB_HEALTH_SCORE.set(health_score)
        CHROMADB_DRIFT_ZSCORE.set(drift_zscore)

        status = "HEALTHY"
        recommended_action = "NO_ACTION"

        if health_score < 0.5 or drift_zscore > 3.0:
            status = "CRITICAL"
            recommended_action = "FULL_REINDEX_REQUIRED"
        elif health_score < 0.75 or drift_zscore > 2.0:
            status = "WARNING"
            recommended_action = "RUN_DEDUPLICATION_AND_PRUNING"

        return {
            "health_score": round(health_score, 4),
            "drift_zscore": round(drift_zscore, 4),
            "total_vectors": total_vectors,
            "vector_dim": dim,
            "avg_dispersion": round(avg_dispersion, 4),
            "status": status,
            "recommended_action": recommended_action
        }

    def cleanup_duplicates(
        self,
        collection: Any,
        threshold: float = 0.98
    ) -> Dict[str, Any]:
        """
        Effectue une recherche interne de Cosine Similarity pour éliminer les doublons sémantiques.

        Si similarity >= threshold, le document le plus ancien (ou 2e occurence) est supprimé.
        """
        data = collection.get(include=['embeddings', 'metadatas', 'documents'])
        ids = data.get('ids', [])
        embeddings = data.get('embeddings')

        if embeddings is None or len(embeddings) < 2:
            return {"duplicates_found": 0, "deleted_ids": []}

        matrix = np.array(embeddings)
        norms = np.linalg.norm(matrix, axis=1, keepdims=True)
        norms[norms == 0] = 1e-8
        normalized = matrix / norms

        # Matrice de similarité Cosine (N x N)
        similarity_matrix = np.dot(normalized, normalized.T)

        ids_to_delete = set()
        n = len(ids)

        for i in range(n):
            if ids[i] in ids_to_delete:
                continue
            for j in range(i + 1, n):
                if ids[j] in ids_to_delete:
                    continue
                if similarity_matrix[i, j] >= threshold:
                    # Doublon sémantique détecté : on conserve l'élément i et marque j à supprimer
                    ids_to_delete.add(ids[j])

        deleted_list = list(ids_to_delete)
        if deleted_list:
            collection.delete(ids=deleted_list)
            CHROMADB_DUPLICATES_CLEANED.inc(len(deleted_list))
            logger.info(f"Nettoyage sémantique : {len(deleted_list)} doublons supprimés.")

        return {
            "duplicates_found": len(deleted_list),
            "deleted_ids": deleted_list,
            "threshold_used": threshold
        }

    def temporal_pruning(
        self,
        collection: Any,
        inactive_days: int = 180
    ) -> Dict[str, Any]:
        """
        Élague les documents inactifs depuis plus de `inactive_days` jours.
        Les documents supprimés sont exportés vers le stockage à froid.
        """
        data = collection.get(include=['metadatas', 'documents'])
        ids = data.get('ids', [])
        metadatas = data.get('metadatas', [])
        documents = data.get('documents', [])

        current_time = time.time()
        max_age_seconds = inactive_days * 86400

        prune_ids = []
        archive_items = []

        for idx, doc_id in enumerate(ids):
            meta = metadatas[idx] if metadatas and idx < len(metadatas) else {}
            last_accessed = meta.get("last_accessed_at", meta.get("timestamp", current_time))
            if isinstance(last_accessed, str):
                try:
                    last_accessed = float(last_accessed)
                except ValueError:
                    last_accessed = current_time

            if (current_time - last_accessed) > max_age_seconds:
                prune_ids.append(doc_id)
                archive_items.append({
                    "id": doc_id,
                    "metadata": meta,
                    "document": documents[idx] if documents and idx < len(documents) else "",
                    "archived_at": current_time
                })

        if archive_items:
            archive_filename = f"cold_archive_{int(current_time)}.json"
            archive_path = os.path.join(self.cold_storage_dir, archive_filename)
            with open(archive_path, "w", encoding="utf-8") as f:
                json.dump(archive_items, f, indent=2, ensure_ascii=False)

            collection.delete(ids=prune_ids)
            logger.info(f"Pruning temporel : {len(prune_ids)} documents archivés dans {archive_path}.")

        return {
            "pruned_count": len(prune_ids),
            "pruned_ids": prune_ids,
            "inactive_days_threshold": inactive_days
        }

    def check_reindex_trigger(
        self,
        collection: Any,
        baseline_count: int,
        max_growth_ratio: float = 0.20
    ) -> Dict[str, Any]:
        """
        Vérifie si la collection a grandi de plus de `max_growth_ratio` (+20%).
        """
        current_count = collection.count()
        if baseline_count <= 0:
            return {"should_reindex": False, "growth_ratio": 0.0, "current_count": current_count}

        growth_ratio = (current_count - baseline_count) / float(baseline_count)
        should_reindex = growth_ratio >= max_growth_ratio

        return {
            "should_reindex": should_reindex,
            "growth_ratio": round(growth_ratio, 4),
            "current_count": current_count,
            "baseline_count": baseline_count,
            "threshold_ratio": max_growth_ratio
        }

    def run_maintenance_cycle(
        self,
        collection_name: str = "superagent_knowledge",
        duplicate_threshold: float = 0.98,
        inactive_days: int = 180,
        baseline_count: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Exécute le cycle complet de maintenance prédictive.
        """
        client = self.get_client()
        try:
            collection = client.get_collection(name=collection_name)
        except Exception as e:
            logger.warning(f"Impossible de récupérer la collection '{collection_name}': {e}")
            return {"error": f"Collection '{collection_name}' introuvable."}

        audit_res = self.audit_health(collection)
        dedup_res = self.cleanup_duplicates(collection, threshold=duplicate_threshold)
        prune_res = self.temporal_pruning(collection, inactive_days=inactive_days)

        reindex_res = {}
        if baseline_count is not None:
            reindex_res = self.check_reindex_trigger(collection, baseline_count=baseline_count)

        return {
            "timestamp": time.time(),
            "collection": collection_name,
            "health_audit": audit_res,
            "deduplication": dedup_res,
            "pruning": prune_res,
            "reindex_check": reindex_res
        }
