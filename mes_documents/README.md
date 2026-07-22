# 🚀 Flotte IA Multi-Agents Auto-Hébergée avec Hermes Agent

**Tutoriel complet — De zéro à une flotte de 5 agents pilotée via Telegram**

```
┌──────────────────────────────────────────────────────────────┐
│                    ☁️  VPS (Debian/Ubuntu)                    │
│  ┌────────────────────────────────────────────────────────┐  │
│  │              🧠 ORCHESTRATEUR                           │  │
│  │         (coordination + dispatch + synthèse)            │  │
│  └──────────┬──────────┬──────────┬───────────────────────┘  │
│             │          │          │                           │
│     ┌───────▼──┐ ┌────▼────┐ ┌───▼──────┐ ┌──────────────┐ │
│     │🔍 ÉCLAIREUR│ │✍️ SCRIBE │ │📢 PORTEUR │ │⚙️ DÉVELOPPEUR│ │
│     │ recherche  │ │rédaction│ │ marketing│ │  ingénierie  │ │
│     └──────┬─────┘ └────┬────┘ └────┬─────┘ └──────┬───────┘ │
│            │            │           │               │         │
│     ┌──────▼────────────▼───────────▼───────────────▼──────┐ │
│     │              📊 MISSION CONTROL                       │ │
│     │     dashboard temps réel · logs · tokens · VPS       │ │
│     └──────────────────────────────────────────────────────┘ │
│                         │                                    │
└─────────────────────────┼────────────────────────────────────┘
                          │
              ┌───────────▼───────────┐
              │    📱 TELEGRAM         │
              │  Groupe avec Sujets    │
              │  (1 topic par agent)   │
              └────────────────────────┘
```

---

## 📋 Table des matières

1. [Ce que vous construisez](#-ce-que-vous-construisez)
2. [Prérequis](#-prérequis)
3. [Architecture](#-architecture)
4. [Étape 1 — Installation du VPS](#étape-1--installation-du-vps)
5. [Étape 2 — Installation d'Hermes Agent](#étape-2--installation-dhermes-agent)
6. [Étape 3 — Création des profils agents](#étape-3--création-des-profils-agents)
7. [Étape 4 — Identités et mémoires des agents](#étape-4--identités-et-mémoires-des-agents)
8. [Étape 5 — Routage Telegram par topics](#étape-5--routage-telegram-par-topics)
9. [Étape 6 — Services systemd (démarrage automatique)](#étape-6--services-systemd-démarrage-automatique)
10. [Étape 7 — Système de logging unifié](#étape-7--système-de-logging-unifié)
11. [Étape 8 — Tableau de bord Mission Control](#étape-8--tableau-de-bord-mission-control)
12. [Étape 9 — Tâches cron planifiées](#étape-9--tâches-cron-planifiées)
13. [Étape 10 — Accès distant sécurisé (Tailscale)](#étape-10--accès-distant-sécurisé-tailscale)
14. [Étape 11 — Orchestration multi-agents](#étape-11--orchestration-multi-agents)
15. [Maintenance et supervision](#-maintenance-et-supervision)
16. [Dépannage](#-dépannage)

---

## 🎯 Ce que vous construisez

| Composant | Description |
|-----------|-------------|
| **Orchestrateur** | Reçoit les demandes, décompose en sous-tâches, dispatche aux spécialistes, consolide les résultats |
| **Éclaireur** | Recherche web, veille, investigation, fact-checking |
| **Scribe** | Rédaction, synthèse, mise en forme de contenu |
| **Porteur** | Marketing, diffusion, posts réseaux sociaux, newsletters |
| **Développeur** | Code, scripts, automatisation, infrastructure |
| **Mission Control** | Dashboard web temps réel : statut agents, tokens, métriques VPS, logs, vue 3D |
| **Routage Telegram** | Un groupe Telegram avec 5 sujets (topics) — chaque agent répond dans son canal dédié |
| **Mémoire isolée** | Chaque agent a sa propre mémoire persistante, son historique et son identité |

---

## 📦 Prérequis

### VPS
- **OS** : Debian 12 ou Ubuntu 22.04/24.04 LTS
- **RAM** : 4 Go minimum (8 Go recommandé pour les 5 agents)
- **CPU** : 2 vCPU minimum
- **Disque** : 20 Go minimum
- **Fournisseurs** : Hetzner, OVH, DigitalOcean, Vultr, Scaleway...

### Logiciels
- Python 3.11+
- pip / uv
- systemd (pour les services)
- git

### Comptes
- Compte Telegram + bot créé via [@BotFather](https://t.me/BotFather)
- Clé API LLM (OpenRouter, Anthropic, OpenAI, ou modèle local Ollama)
- Compte Tailscale (gratuit) pour l'accès distant sécurisé

---

## 🏗️ Architecture

### Isolation par profils Hermes

Chaque agent est un **profil Hermes indépendant** avec :
- Son propre `config.yaml` (modèle, outils, paramètres)
- Son propre `SOUL.md` (identité, instructions système)
- Sa propre mémoire persistante (SQLite)
- Son propre historique de sessions
- Ses propres skills

```
~/.hermes/profiles/
├── orchestrateur/
│   ├── config.yaml
│   ├── SOUL.md
│   ├── .env
│   ├── state.db          ← mémoire isolée
│   └── skills/
├── eclaireur/
│   └── ...
├── scribe/
├── porteur/
└── developpeur/
```

### Flux de communication

```
Utilisateur (Telegram)
    │
    ▼
Groupe Telegram "Flotte IA"
    │
    ├── Topic #orchestrateur → Profile orchestrateur → Gateway Telegram
    ├── Topic #eclaireur     → Profile eclaireur     → Gateway Telegram
    ├── Topic #scribe        → Profile scribe        → Gateway Telegram
    ├── Topic #porteur       → Profile porteur       → Gateway Telegram
    └── Topic #developpeur   → Profile developpeur   → Gateway Telegram
```

Chaque profile fait tourner sa **propre instance gateway** qui écoute le bot Telegram.
Le routage se fait par **topic_id** : chaque agent ne répond que dans son sujet dédié.

---

## Étape 1 — Installation du VPS

### 1.1 Provisionner le serveur

Choisissez un VPS chez le fournisseur de votre choix. Exemple avec Hetzner :

```bash
# Créer un VPS CX22 (2 vCPU, 4 Go RAM, 40 Go SSD) ~6€/mois
# OS : Debian 12
# Ajouter votre clé SSH
```

### 1.2 Première connexion et sécurisation

```bash
ssh root@<ip-du-vps>

# Mise à jour
apt update && apt upgrade -y

# Créer un utilisateur non-root
adduser hermes
usermod -aG sudo hermes

# Configurer SSH
sed -i 's/PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config
sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
systemctl restart sshd

# Firewall de base
apt install ufw -y
ufw allow OpenSSH
ufw allow 9191/tcp  # Dashboard Mission Control
ufw enable

# Se reconnecter en tant que hermes
exit
ssh hermes@<ip-du-vps>
```

### 1.3 Installer les dépendances système

```bash
sudo apt install -y python3 python3-pip python3-venv git curl \
  build-essential libssl-dev libffi-dev python3-dev
```

---

## Étape 2 — Installation d'Hermes Agent

### 2.1 Installation via le script officiel

```bash
curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash
```

Ce script installe :
- `uv` (gestionnaire de paquets Python rapide)
- Hermes Agent dans un environnement virtuel
- Le wrapper `hermes` dans `~/.local/bin/`

### 2.2 Configuration du fournisseur LLM

```bash
# Configurer la clé API (ex: OpenRouter)
hermes config set model.provider openrouter
hermes config set model.default "anthropic/claude-sonnet-4"

# Ou utiliser un modèle local via Ollama
hermes config set model.provider ollama
hermes config set model.default "qwen3.5:cloud"

# Ajouter la clé API dans ~/.hermes/.env
echo "OPENROUTER_API_KEY=sk-or-v1-..." >> ~/.hermes/.env
```

### 2.3 Vérification

```bash
hermes doctor          # Vérifie la configuration
hermes chat -q "Bonjour, qui es-tu ?"  # Test rapide
```

---

## Étape 3 — Création des profils agents

Chaque agent est un profil Hermes indépendant, cloné depuis le profil `default`.

```bash
# Créer les 5 profils
hermes profile create orchestrateur --clone
hermes profile create eclaireur --clone
hermes profile create scribe --clone
hermes profile create porteur --clone
hermes profile create developpeur --clone

# Vérifier
hermes profile list
```

Chaque profil hérite de la configuration du profil `default` (clé API, modèle, etc.)
mais possède son propre espace isolé.

### Structure créée

```
~/.hermes/profiles/orchestrateur/
├── config.yaml     ← configuration indépendante
├── SOUL.md         ← identité de l'agent
├── .env            ← variables d'environnement
├── state.db        ← base de sessions SQLite
├── skills/         ← skills propres à l'agent
└── sessions/       ← historique des conversations
```

Des wrappers CLI sont aussi créés :
```bash
orchestrateur chat -q "Analyse cette tâche..."
eclaireur chat -q "Recherche les dernières news IA..."
scribe chat -q "Rédige un article sur..."
porteur chat -q "Crée des posts pour..."
developpeur chat -q "Écris un script qui..."
```

---

## Étape 4 — Identités et mémoires des agents

### 4.1 SOUL.md — L'identité de chaque agent

Le fichier `SOUL.md` définit la personnalité, les compétences et les règles de chaque agent.
Il est injecté dans le prompt système à chaque session.

#### Orchestrateur (`~/.hermes/profiles/orchestrateur/SOUL.md`)

```markdown
# ORCHESTRATEUR — Chef d'orchestre de la flotte

Tu es l'Orchestrateur, le coordinateur central d'une flotte de 4 agents spécialisés.
Ta mission : recevoir les demandes utilisateur, les décomposer en sous-tâches,
les dispatcher aux agents spécialisés, consolider leurs résultats.

## Tes agents
- **Éclaireur** : Recherche, veille, investigation
- **Scribe** : Rédaction, synthèse, mise en forme
- **Porteur** : Marketing, diffusion, outreach
- **Développeur** : Code, infrastructure, automatisation

## Règles
- Ne fais pas le travail des agents toi-même — délègue
- Si une sous-tâche échoue, adapte et réessaie
- Priorise la clarté et la concision dans tes synthèses
- Tu es le seul point de contact avec l'utilisateur
```

#### Éclaireur (`~/.hermes/profiles/eclaireur/SOUL.md`)

```markdown
# ÉCLAIREUR — Agent de recherche et veille

Tu es l'Éclaireur, l'agent de recherche de la flotte.
Ta mission : trouver, vérifier et synthétiser l'information.

## Règles
- Toujours citer tes sources
- Distinguer faits vérifiés, opinions et rumeurs
- Si l'information n'est pas trouvable, le dire clairement
- Format de réponse : synthèse + sources + niveau de confiance
```

#### Scribe (`~/.hermes/profiles/scribe/SOUL.md`)

```markdown
# SCRIBE — Agent de rédaction et mise en forme

Tu es le Scribe, la plume de la flotte.
Ta mission : transformer l'information brute en contenu clair et publiable.

## Règles
- Adapter le registre au public (technique, grand public, enfants...)
- Structurer avec titres, sous-titres, listes
- Éviter le jargon inutile
- Toujours livrer un contenu publiable, pas un brouillon
```

#### Porteur (`~/.hermes/profiles/porteur/SOUL.md`)

```markdown
# PORTEUR — Agent de marketing et diffusion

Tu es le Porteur, la voix de la flotte vers le monde extérieur.
Ta mission : diffuser le contenu, engager l'audience, maximiser l'impact.

## Règles
- Respecter les limites de chaque plateforme (280 car. X, etc.)
- Inclure des hashtags pertinents
- Optimiser pour l'engagement (questions, appels à l'action)
- Ne jamais publier sans validation — tu proposes, l'Orchestrateur valide
```

#### Développeur (`~/.hermes/profiles/developpeur/SOUL.md`)

```markdown
# DÉVELOPPEUR — Agent d'ingénierie et infrastructure

Tu es le Développeur, le bâtisseur de la flotte.
Ta mission : coder, automatiser, déployer et maintenir l'infrastructure.

## Règles
- Code propre, commenté, testé
- Privilégier les solutions simples et maintenables
- Documenter les choix d'architecture
- Toujours tester avant de livrer
```

### 4.2 Mémoire persistante

Chaque agent dispose de sa propre mémoire via le système de mémoire d'Hermes :

```bash
# L'Orchestrateur se souvient des préférences utilisateur
orchestrateur chat -q "Note que l'utilisateur préfère les réponses en français concis"

# L'Éclaireur mémorise les sources fiables
eclaireur chat -q "Ajoute https://arxiv.org comme source prioritaire pour les recherches IA"

# Le Scribe retient le style éditorial
scribe chat -q "Le ton doit être journalistique, neutre, avec des phrases courtes"
```

Les mémoires sont stockées dans `state.db` de chaque profil et persistent entre les sessions.

---

## Étape 5 — Routage Telegram par topics

### 5.1 Créer le bot Telegram

1. Ouvrez [@BotFather](https://t.me/BotFather) sur Telegram
2. Créez un bot : `/newbot`
3. Nommez-le : `Flotte IA`
4. Username : `flotte_ia_bot`
5. **Conservez le token** (ex: `8831591361:AAH...`)

### 5.2 Créer un groupe avec sujets (topics)

1. Créez un **nouveau groupe** Telegram
2. Ajoutez votre bot comme membre
3. Allez dans Paramètres → **Activer les sujets** (topics)
4. Créez 5 sujets :
   - `#orchestrateur`
   - `#eclaireur`
   - `#scribe`
   - `#porteur`
   - `#developpeur`

### 5.3 Récupérer les IDs des topics

```bash
# Envoyez un message dans chaque topic, puis :
curl -s "https://api.telegram.org/bot<VOTRE_TOKEN>/getUpdates" | jq '.result[-1].message'
```

Notez les `message_thread_id` pour chaque topic :
- Topic orchestrateur : `12345`
- Topic eclaireur : `12346`
- Topic scribe : `12347`
- Topic porteur : `12348`
- Topic developpeur : `12349`

### 5.4 Configurer le token dans chaque profil

```bash
# Ajouter le token dans le .env de chaque profil
echo "TELEGRAM_BOT_TOKEN=8831591361:AAH..." >> ~/.hermes/profiles/orchestrateur/.env
echo "TELEGRAM_BOT_TOKEN=8831591361:AAH..." >> ~/.hermes/profiles/eclaireur/.env
echo "TELEGRAM_BOT_TOKEN=8831591361:AAH..." >> ~/.hermes/profiles/scribe/.env
echo "TELEGRAM_BOT_TOKEN=8831591361:AAH..." >> ~/.hermes/profiles/porteur/.env
echo "TELEGRAM_BOT_TOKEN=8831591361:AAH..." >> ~/.hermes/profiles/developpeur/.env
```

### 5.5 Configurer le topic dédié par agent

Dans chaque `config.yaml` de profil, configurez le canal Telegram :

```yaml
# ~/.hermes/profiles/orchestrateur/config.yaml
telegram:
  allowed_chats: ""  # vide = tous les chats du groupe
  home_channel: "-1001234567890"        # ID du groupe
  home_channel_thread_id: "12345"       # ID du topic orchestrateur
```

Répétez pour chaque agent avec son `thread_id` respectif.

### 5.6 Alternative : un bot par agent

Si vous préférez une isolation totale, créez 5 bots Telegram distincts :

```bash
# Via @BotFather, créez :
# @flotte_orchestrateur_bot
# @flotte_eclaireur_bot
# @flotte_scribe_bot
# @flotte_porteur_bot
# @flotte_developpeur_bot
```

Puis configurez chaque profil avec son propre token. Cette approche est plus simple
mais nécessite 5 bots au lieu d'un seul groupe avec topics.

---

## Étape 6 — Services systemd (démarrage automatique)

Pour que les agents démarrent automatiquement au boot du VPS et redémarrent en cas de crash.

### 6.1 Créer les fichiers de service

Créez `~/.config/systemd/user/hermes-orchestrateur.service` :

```ini
[Unit]
Description=Hermes Agent Fleet — Orchestrateur
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
Environment=HERMES_HOME=%h/.hermes/profiles/orchestrateur
ExecStart=%h/.local/bin/orchestrateur gateway run
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=default.target
```

Répétez pour les 4 autres agents (éclaireur, scribe, porteur, développeur).

### 6.2 Activer et démarrer

```bash
# Recharger systemd
systemctl --user daemon-reload

# Activer le démarrage automatique
systemctl --user enable hermes-orchestrateur
systemctl --user enable hermes-eclaireur
systemctl --user enable hermes-scribe
systemctl --user enable hermes-porteur
systemctl --user enable hermes-developpeur

# Démarrer
systemctl --user start hermes-orchestrateur
systemctl --user start hermes-eclaireur
systemctl --user start hermes-scribe
systemctl --user start hermes-porteur
systemctl --user start hermes-developpeur

# Vérifier
systemctl --user status 'hermes-*'
```

### 6.3 Activer la persistance après logout

```bash
# Pour que les services continuent après déconnexion SSH
sudo loginctl enable-linger $USER
```

### 6.4 Supervision

```bash
# Logs en direct
journalctl --user -u hermes-orchestrateur -f

# Logs de tous les agents
journalctl --user -u 'hermes-*' -f

# Statut global
systemctl --user list-units 'hermes-*'
```

---

## Étape 7 — Système de logging unifié

Avant le dashboard, on met en place un système de logging commun à tous les agents.

### 7.1 Architecture

```
~/Bureau/flotte/
├── scripts/
│   ├── fleet_logger.py       ← Logger thread-safe (JSONL, rotation quotidienne)
│   ├── log_wrapper.py        ← Wrapper avec loggers pré-instanciés par agent
│   └── log_retention.py      ← Script de rétention (cron quotidien)
└── logs/
    ├── orchestrateur/        ← orchestrateur_2026-07-14.jsonl
    ├── eclaireur/            ← eclaireur_2026-07-14.jsonl
    ├── scribe/               ← scribe_2026-07-14.jsonl
    ├── porteur/              ← porteur_2026-07-14.jsonl
    ├── developpeur/          ← developpeur_2026-07-14.jsonl
    └── system/               ← logs système (rétention, erreurs)
```

### 7.2 Niveaux de log

| Niveau | Usage |
|--------|-------|
| `TASK` | Tâche reçue ou complétée (avec durée, succès/échec) |
| `TOOL` | Appel d'outil Hermes (nom, paramètres, durée) |
| `METRIC` | Métrique (tokens, coût) |
| `ERROR` / `WARN` | Erreurs et avertissements |
| `INFO` | Session start/end, infos générales |

### 7.3 Utilisation dans le code

```python
import sys
sys.path.insert(0, '/home/hermes/Bureau/flotte/scripts')
from fleet_logger import AgentLogger

log = AgentLogger('eclaireur')
log.session_start('session_123')
log.task_received('task_42', 'Recherche actualités IA', 'orchestrateur')
log.tool_called('web_search', 'GPT-5 announcement', 320)
log.task_completed('task_42', 3200, True, '3 sources trouvées')
log.metric('tokens', 1250, 'tokens')
log.session_end('session_123', 1250, 3500)
```

### 7.4 Rétention automatique

```bash
# Nettoyer les logs de +30 jours
python3 ~/Bureau/flotte/scripts/log_retention.py

# Via cron (tous les jours à 3h)
developpeur cron create "0 3 * * *" \
  --name "log-retention" \
  --script "~/Bureau/flotte/scripts/log_retention.py" \
  --no_agent
```

---

## Étape 8 — Tableau de bord Mission Control

### 8.1 Le dashboard

Un dashboard web en lecture seule (port 9191) affiche :
- **Statut des agents** : en ligne/hors ligne, tokens consommés (via `pgrep` + logs)
- **Métriques VPS** : CPU, RAM, disque, uptime (via `top`, `free`, `df`)
- **Journal temps réel** : 15 dernières entrées du fleet_logger
- **Vue 3D des bureaux** : visualisation Three.js avec 5 desks + hub central
- **Compteur de tokens** : par agent et total (agrégé depuis les logs)

### 8.2 Endpoints API

| Endpoint | Description |
|----------|-------------|
| `GET /` ou `/index.html` | Dashboard HTML complet |
| `GET /health` | Health check (`{"status": "ok"}`) |
| `GET /api/metrics` | Statut agents + VPS + logs récents |
| `GET /api/logs/summary` | Résumé agrégé (tâches, erreurs, tokens par agent) |
| `GET /api/logs/errors` | Erreurs du jour |
| `GET /api/logs/storage` | Statistiques de stockage des logs |
| `GET /api/logs/tail?agent=eclaireur&limit=20` | Dernières entrées filtrées |

### 8.3 Lancement

```bash
cd ~/Bureau/tutoriel-flotte-ia/dashboard
python3 metrics-api.py
# → http://localhost:9191
```

### 8.4 Service systemd

Fichier : `~/.config/systemd/user/mission-control.service`

```ini
[Unit]
Description=Mission Control Dashboard
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=%h/Bureau/tutoriel-flotte-ia/dashboard
ExecStart=%h/mon_env/bin/python metrics-api.py
Restart=on-failure
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=default.target
```

```bash
cp ~/Bureau/tutoriel-flotte-ia/systemd/mission-control.service ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable mission-control
systemctl --user start mission-control
```

### 8.5 Vérification

```bash
curl http://localhost:9191/health
# → {"status": "ok"}

curl http://localhost:9191/api/metrics | jq
# → agents, vps, logs
```

---

## Étape 9 — Tâches cron planifiées

### 9.1 Vue d'ensemble

| Job | Agent | Schedule | Description |
|-----|-------|----------|-------------|
| `briefing-quotidien-orchestrateur` | Orchestrateur | Tous les jours 8h | Briefing quotidien : Éclaireur → Scribe → Porteur |
| `veille-eclaireur-6h` | Éclaireur | Toutes les 6h | Veille IA, cybersécurité, logiciel libre |
| `rapport-hebdo-orchestrateur` | Orchestrateur | Lundi 9h | Rapport hebdomadaire complet (métriques, tendances) |
| `maintenance-hebdo-developpeur` | Développeur | Dimanche 3h | Vérification VPS + nettoyage |
| `retention-logs-flotte` | Script (no-agent) | Tous les jours 4h | Suppression logs > 30 jours |

### 9.2 Création des crons

```bash
# Briefing quotidien (Orchestrateur, 8h)
hermes cron create "0 8 * * *" \
  --name "briefing-quotidien-orchestrateur" \
  --prompt "Génère le briefing quotidien de la flotte.
1. Demande à l'Éclaireur (via delegate_task) les 5 actualités les plus importantes
2. Demande au Scribe de les mettre en forme
3. Demande au Porteur de préparer les posts réseaux sociaux
4. Synthétise le tout dans un message concis" \
  --deliver "local"

# Veille IA (Éclaireur, toutes les 6h)
hermes cron create "0 */6 * * *" \
  --name "veille-eclaireur-6h" \
  --prompt "Effectue une veille sur : IA (nouveaux modèles, recherche), cybersécurité (vulnérabilités, attaques), logiciel libre (nouveaux outils). Pour chaque sujet : top 3, titre + source + 1 phrase. Format compact." \
  --deliver "local"

# Rapport hebdomadaire (Orchestrateur, lundi 9h)
hermes cron create "0 9 * * 1" \
  --name "rapport-hebdo-orchestrateur" \
  --prompt "Génère un rapport hebdomadaire : consulte les logs (~/Bureau/flotte/logs/), extrais les métriques (tokens, tâches, erreurs), vérifie l'état du VPS. Format : sections par agent, métriques clés, tendances vs semaine précédente." \
  --deliver "local"

# Maintenance VPS (Développeur, dimanche 3h)
hermes cron create "0 3 * * 0" \
  --name "maintenance-hebdo-developpeur" \
  --prompt "Vérifie l'état du VPS : espace disque (df -h), RAM (free -h), processus zombies, mises à jour disponibles (apt list --upgradable). Nettoie les logs de plus de 30 jours. Rapport concis." \
  --deliver "local"

# Rétention logs (script no-agent, tous les jours 4h)
cp ~/Bureau/flotte/scripts/log_retention.py ~/.hermes/scripts/
hermes cron create "0 4 * * *" \
  --name "retention-logs-flotte" \
  --script "log_retention.py" \
  --no_agent \
  --deliver "local"
```

### 9.3 Épingler le modèle

Pour éviter les erreurs de dérive de config, épingler le modèle sur chaque cron :

```bash
hermes cron edit <job_id> --model "deepseek-v4-pro:cloud"
```

### 9.4 Vérification

```bash
hermes cron list
# → 5 jobs actifs avec prochaines exécutions programmées

# Note : le gateway doit tourner pour que les crons s'exécutent
hermes gateway status
```

---

## Étape 10 — Accès distant sécurisé (Tailscale)

### 10.1 Installer Tailscale

```bash
curl -fsSL https://tailscale.com/install.sh | sudo bash
sudo tailscale up
```

Suivez le lien d'authentification dans le navigateur. Une fois connecté, votre machine
reçoit un hostname Tailscale (ex: `kali.tail1234.ts.net`).

### 10.2 Vérifier la connexion

```bash
tailscale status
# → kali  mozy@github  linux  active; direct <IP>, tx/rx ...
tailscale ip -4
# → 100.x.y.z (IP Tailscale)
```

### 10.3 Accéder au dashboard

```bash
# Depuis n'importe quel appareil connecté à votre Tailnet :
# https://<hostname>:9191
# Exemple : https://kali.tail1234.ts.net:9191
```

### 10.4 Certificat HTTPS (optionnel)

```bash
# Tailscale fournit des certificats TLS automatiquement
sudo tailscale cert \
  --cert-file=/tmp/mission-control.crt \
  --key-file=/tmp/mission-control.key \
  <votre-hostname>.ts.net
```

Puis modifier `metrics-api.py` pour utiliser ces certificats :

```python
import ssl
# Dans main() :
ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
ctx.load_cert_chain('/tmp/mission-control.crt', '/tmp/mission-control.key')
server = HTTPServer(("0.0.0.0", port), MetricsHandler)
server.socket = ctx.wrap_socket(server.socket, server_side=True)
```

### 10.5 Alternative : Cloudflare Tunnel

```bash
curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o cloudflared
chmod +x cloudflared
sudo mv cloudflared /usr/local/bin/
cloudflared tunnel login
cloudflared tunnel create mission-control
cloudflared tunnel route dns mission-control dashboard.votredomaine.com
cloudflared tunnel run --url http://localhost:9191 mission-control
```

### 10.6 État actuel

- Gateway : actif (PID 583289)
- Dashboard : actif sur port 9191 (systemd)
- Tailscale : connecté — `kali.tail649d6e.ts.net` (IP 100.73.157.127)
- Dashboard distant : `http://kali.tail649d6e.ts.net:9191` ✓

---

## Étape 10 — Orchestration multi-agents

### 10.1 Délégation de tâches

L'Orchestrateur utilise `delegate_task` pour dispatcher le travail :

```python
# Exemple de flux orchestrateur
delegate_task(
    goal="Recherche les 5 dernières avancées en IA générative",
    context="Sources prioritaires : arXiv, TechCrunch, The Verge. Format : titre + source + résumé 2 phrases.",
    role="leaf"
)
# → L'Éclaireur travaille en arrière-plan

delegate_task(
    goal="Rédige un article de 800 mots sur les avancées IA",
    context="Public : développeurs. Ton : technique mais accessible. Structure : intro, 3 sections, conclusion.",
    role="leaf"
)
# → Le Scribe travaille en parallèle
```

### 10.2 Workflow type

```
Utilisateur: "Fais une analyse du marché des LLM open-source"
    │
    ▼
ORCHESTRATEUR
    │
    ├─→ ÉCLAIREUR : "Recherche les principaux LLM open-source,
    │                 leurs performances, licences, communauté"
    │
    ├─→ SCRIBE : "Prépare un rapport structuré avec les données
    │             que l'Éclaireur va fournir"
    │
    └─→ PORTEUR : "Prépare un thread X/Twitter de 5 posts
                  pour résumer l'analyse"
    │
    ▼
ORCHESTRATEUR : Consolide → Livre le rapport + thread
```

### 10.3 Communication inter-agents

Les agents communiquent via l'Orchestrateur, jamais directement :

```
ÉCLAIREUR → résultat → ORCHESTRATEUR → contexte → SCRIBE
SCRIBE → brouillon → ORCHESTRATEUR → validation → PORTEUR
PORTEUR → posts → ORCHESTRATEUR → livraison → UTILISATEUR
```

---

## 🔧 Maintenance et supervision

### Commandes utiles

```bash
# Statut de tous les agents
systemctl --user status 'hermes-*'

# Logs en direct
journalctl --user -u 'hermes-*' -f --since "10 minutes ago"

# Redémarrer un agent
systemctl --user restart hermes-eclaireur

# Consommation de ressources
htop
systemd-cgtop  # par service

# Nettoyage des sessions anciennes
orchestrateur sessions prune --older-than 30
eclaireur sessions prune --older-than 30
# ... pour chaque agent

# Mise à jour d'Hermes
hermes update
# Redémarrer tous les agents après mise à jour
systemctl --user restart 'hermes-*'
```

### Monitoring des tokens

```bash
# Dashboard → http://localhost:9191
# Ou via l'API :
watch -n 5 'curl -s http://localhost:9191/api/metrics | jq ".agents"'
```

### Sauvegarde

```bash
# Sauvegarder les profils
tar -czf hermes-backup-$(date +%Y%m%d).tar.gz ~/.hermes/profiles/

# Automatiser avec cron
echo "0 2 * * * tar -czf ~/backups/hermes-$(date +\%Y\%m\%d).tar.gz ~/.hermes/profiles/" | crontab -
```

---

## 🩺 Dépannage

### Un agent ne répond pas sur Telegram

```bash
# Vérifier les logs
journalctl --user -u hermes-orchestrateur -n 50

# Vérifier le token
grep TELEGRAM_BOT_TOKEN ~/.hermes/profiles/orchestrateur/.env

# Tester la connectivité Telegram
curl -s "https://api.telegram.org/bot<VOTRE_TOKEN>/getMe"

# Redémarrer l'agent
systemctl --user restart hermes-orchestrateur
```

### Erreur "Gateway port already in use"

Chaque agent doit avoir un port gateway différent. Vérifiez :

```bash
# Dans chaque config.yaml de profil :
grep "gateway_port\|api_server" ~/.hermes/profiles/*/config.yaml

# Ou laissez Hermes gérer les ports automatiquement
# (chaque processus gateway utilise un port aléatoire par défaut)
```

### Mémoire insuffisante

```bash
# Réduire le nombre d'agents simultanés
systemctl --user stop hermes-porteur
systemctl --user stop hermes-developpeur

# Utiliser des modèles plus légers
hermes config set model.default "openai/gpt-4o-mini" --profile eclaireur

# Ou un modèle local Ollama
hermes config set model.provider ollama --profile eclaireur
hermes config set model.default "qwen3.5:cloud" --profile eclaireur
```

### Dashboard inaccessible

```bash
# Vérifier que le service tourne
systemctl --user status mission-control

# Vérifier le port
ss -tlnp | grep 9191

# Tester localement
curl http://localhost:9191/health
```

### Linger ne fonctionne pas (services s'arrêtent au logout)

```bash
# Vérifier
loginctl show-user $USER | grep Linger

# Activer
sudo loginctl enable-linger $USER

# Vérifier à nouveau
loginctl show-user $USER | grep Linger
# Doit afficher: Linger=yes
```

---

## 📁 Fichiers du projet

```
tutoriel-flotte-ia/
├── README.md                          ← Ce tutoriel
├── dashboard/
│   ├── mission-control.html           ← Dashboard HTML/JS/Three.js
│   └── metrics-api.py                 ← API Python (métriques + serveur web)
├── systemd/
│   ├── hermes-orchestrateur.service   ← Service systemd Orchestrateur
│   ├── hermes-eclaireur.service       ← Service systemd Éclaireur
│   ├── hermes-scribe.service          ← Service systemd Scribe
│   ├── hermes-porteur.service         ← Service systemd Porteur
│   ├── hermes-developpeur.service     ← Service systemd Développeur
│   └── mission-control.service        ← Service systemd Dashboard
└── scripts/
    └── deploy.sh                      ← Script de déploiement automatisé
```

---

## 🚀 Déploiement rapide

```bash
# 1. Cloner le projet
cd ~/Bureau
# (les fichiers sont déjà créés)

# 2. Lancer le déploiement
cd tutoriel-flotte-ia/scripts
chmod +x deploy.sh
./deploy.sh

# 3. Vérifier
systemctl --user status 'hermes-*'
curl http://localhost:9191/health
```

---

## 📊 Coût estimé

| Ressource | Coût mensuel |
|-----------|-------------|
| VPS 4 Go RAM (Hetzner CX22) | ~6 € |
| OpenRouter API (usage modéré) | ~10-20 € |
| Tailscale (gratuit) | 0 € |
| Telegram Bot API (gratuit) | 0 € |
| **Total** | **~16-26 €/mois** |

Avec un modèle local Ollama sur le VPS, le coût API tombe à 0 € (mais nécessite plus de RAM/GPU).

---

## 🔮 Extensions possibles

- **Kanban multi-agent** : utiliser le système Kanban intégré d'Hermes pour un tableau de tâches partagé
- **Voix** : ajouter la synthèse vocale (TTS) pour que les agents parlent
- **MCP servers** : connecter des outils externes (bases de données, APIs)
- **Webhooks** : déclencher des actions depuis des événements externes
- **Profils supplémentaires** : ajouter un agent Designer, Data Scientist, etc.
- **Multi-utilisateurs** : chaque utilisateur a son Orchestrateur dédié

---

*Tutoriel créé avec Hermes Agent — framework open-source par Nous Research.*
*Documentation officielle : https://hermes-agent.nousresearch.com/docs/*
