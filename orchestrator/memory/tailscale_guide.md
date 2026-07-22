# 🔒 Guide d'Accès Distant Réseau Mesh Tailscale — SuperAgent Morph

Votre machine Linux est directement enregistrée sur le réseau Mesh **Tailscale** sous le nœud **`kali`** avec l'adresse IP privée sécurisée **`100.73.157.127`**.

---

## 🚀 URLs d'Accès Distants (Via le Réseau Mesh Tailscale)

Depuis n'importe quel appareil connecté à votre compte Tailscale (Smartphone, Tablette, PC distant) :

- **Streamlit Control Center** : `http://100.73.157.127:8501`
- **FastAPI Web Service** : `http://100.73.157.127:8000`
- **Grafana Mission Control** : `http://100.73.157.127:3001`
- **Prometheus Observability** : `http://100.73.157.127:9091`

---

## 🔐 Partage Public HTTPS Sécurisé (Tailscale Funnel / Serve)

Pour exposer temporairement l'interface Streamlit avec un certificat TLS HTTPS valide géré par Tailscale :

```bash
# Activation HTTPS sur le port 8501
tailscale serve https / http://localhost:8501
```

Pour arrêter le partage HTTPS :
```bash
tailscale serve reset
```
