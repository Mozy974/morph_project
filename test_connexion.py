"""
Script de test de connexion Mistral API.
"""

import os

try:
    from mistralai import Mistral
    api_key = os.environ.get("MISTRAL_API_KEY")
    if not api_key:
        print("MISTRAL_API_KEY non définie.")
    else:
        client = Mistral(api_key=api_key)
        response = client.chat.complete(model="mistral-small-latest", messages=[{"role": "user", "content": "Ping"}])
        print("Connexion réussie !")
except ImportError:
    print("Package 'mistralai' non installé.")
except Exception as e:
    print(f"Erreur de connexion : {e}")