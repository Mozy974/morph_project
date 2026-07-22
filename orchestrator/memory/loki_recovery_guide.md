# 📖 Guide de Restauration SRE — Loki & Prometheus Disaster Recovery (PRA)

Ce document décrit les procédures opérationnelles pour restaurer la stack d'observabilité (Loki, Prometheus, Grafana, Tempo) à la suite d'un incident ou d'une panne majeure d'infrastructure.

---

## 1. Procédure de Restauration du Cluster Loki

En cas de corruption du stockage de logs ou de crash des ingesteurs Loki :

### Étape 1 : Nettoyage et Vérification du Verrou
```bash
# Vérification de l'état des verrous locaux
ls -la /tmp/loki/
./scripts/clean_purge_lock.sh
```

### Étape 2 : Restauration depuis les Sauvegardes S3 / Local
```bash
# Copie des chunks d'index archivés vers le répertoire de stockage
mkdir -p /tmp/loki/chunks /tmp/loki/rules
cp -r /var/lib/rgpd_backups/loki_chunks_* /tmp/loki/chunks/
```

### Étape 3 : Redémarrage des Ingesteurs et du Querier
```bash
# Redémarrage du cluster Loki via Docker / Systemd
docker-compose restart loki-write loki-read
```

---

## 2. Procédure de Restauration des Métriques Prometheus

```bash
# 1. Vérifier la validité des fichiers de règles
promtool check rules deploy/prometheus/alerts.yml

# 2. Recharger la configuration Prometheus sans interruption (Hot Reload)
curl -X POST http://localhost:9091/-/reload
```

---

## 3. Matrice d'Escalade et Contacts SRE

| Composant | SRE Référent | Seuil Critique | Action d'Urgence |
| :--- | :--- | :--- | :--- |
| **Loki Log Stack** | Équipe SRE / Logs | Corruption chunks TSDB | Basculement sur stockage secondaire `/var/lib/rgpd_backups/` |
| **Prometheus Alerts** | Équipe SRE / Metrics | Hit Ratio < 80% pendant 5 min | Exécution `generate_sre_report.py` & audit des TTLs |
| **RGPD Purge Lock** | Équipe Sécurité & Data | Deadlock sur `/tmp/intent_classifier_purge.lock` | Exécution `./scripts/clean_purge_lock.sh` |
