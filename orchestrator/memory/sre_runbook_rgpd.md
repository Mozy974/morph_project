# 📖 Runbook SRE & Plan de Reprise d'Activité (PRA) RGPD

Ce document décrit les procédures opérationnelles pour la gestion du système de purge, la résolution des verrous d'exclusivité et la restauration des archives d'audit RGPD dans **SuperAgent Morph**.

---

## 🛠️ 1. Déblocage Manuel d'un Verrou de Purge (Troubleshooting)

### Symptôme
Le log émet l'avertissement suivant :
`[Intent & Sentiment Classifier] ⚠️ Purge déjà en cours ou verrou non acquis (exclusivité respectée).`

### Procédure d'Escalade
1. Vérifier si un processus de purge est en cours d'exécution :
   ```bash
   ps aux | grep purge
   ```
2. Si le processus est bloqué ou orphelin, supprimer le verrou système :
   ```bash
   rm -f /tmp/intent_classifier_purge.lock
   ```
3. Relancer la purge manuellement ou via le script de maintenance :
   ```bash
   python3 -c "from orchestrator.agents import IntentSentimentClassifier; IntentSentimentClassifier().purge_old_audit_logs(30)"
   ```

---

## 📦 2. Plan de Reprise d'Activité (PRA) — Archives RGPD

### Emplacement des Archives
Les archives de pré-purge sont stockées de manière persistante dans :
`/var/lib/rgpd_backups/` (ou fallback : `orchestrator/memory/rgpd_backups/`)

### Procédure de Restauration Manuelle
1. Lister les sauvegardes disponibles :
   ```bash
   ls -la /var/lib/rgpd_backups/
   ```
2. Vérifier l'intégrité du fichier JSON d'archive :
   ```bash
   python3 -m json.tool /var/lib/rgpd_backups/audit_backup_YYYYMMDD_HHMMSS.json > /dev/null
   ```
3. Exporter l'archive vers un stockage sécurisé S3 / Cold Storage pour la rétention légale de 5 ans.

---

## 📊 3. Indicateurs de Santé & Métriques Surveillées

- **Gauge Cache Hit Ratio** : `superagent_classifier_cache_hit_ratio` (Seuil d'alerte < 80%)
- **Counter Requêtes Routées** : `superagent_classifier_routed_total`
- **Latence L1 Cache** : `< 10 ms`
