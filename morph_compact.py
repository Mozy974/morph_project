import os
import sys
import argparse
import json
import urllib.request
from urllib.error import HTTPError, URLError

def main():
    parser = argparse.ArgumentParser(description="Compresseur de contexte (Compact clone) via Mistral.")
    parser.add_argument("file", help="Fichier à compresser")
    parser.add_argument("-q", "--query", required=True, help="Requête pour cibler la compression")
    args = parser.parse_args()

    api_key = os.environ.get("MISTRAL_API_KEY")
    if not api_key:
        print("❌ Erreur : La variable MISTRAL_API_KEY n'est pas définie.")
        sys.exit(1)

    filepath = args.file
    if not os.path.exists(filepath):
        print(f"❌ Erreur : Le fichier {filepath} n'existe pas.")
        sys.exit(1)

    with open(filepath, "r", encoding="utf-8") as f:
        original_text = f.read()

    print(f"🗜️ 1. Analyse et compression de '{filepath}' en cours...")
    
    system_prompt = """You are 'Compact', a context compression sub-agent.
Your task is to shrink the provided file by keeping ONLY the lines relevant to the user's specific query.

RULES:
1. KEEP relevant lines byte-for-byte identical to the original.
2. DROP entirely any classes, functions, configurations, or text that do not relate to the query.
3. DO NOT summarize, paraphrase, or explain anything.
4. DO NOT wrap your output in markdown code blocks (like ```python). Just output the raw lines."""

    user_prompt = f"QUERY: {args.query}\n\nFILE CONTENT:\n{original_text}"
    url = "https://api.mistral.ai/v1/chat/completions"
    data = {
        "model": "codestral-latest",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.0
    }
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    req = urllib.request.Request(url, data=json.dumps(data).encode("utf-8"), headers=headers, method="POST")
    
    try:
        with urllib.request.urlopen(req) as response:
            response_data = json.loads(response.read().decode("utf-8"))
            compressed_text = response_data["choices"][0]["message"]["content"]
    except HTTPError as e:
        print(f"❌ Erreur API HTTP {e.code} : {e.read().decode('utf-8')}")
        sys.exit(1)
    except URLError as e:
        print(f"❌ Erreur de connexion : {e.reason}")
        sys.exit(1)

    compressed_text = compressed_text.replace("```python\n", "").replace("```\n", "").replace("```", "").strip()

    original_len = len(original_text)
    new_len = len(compressed_text)
    ratio = (1 - (new_len / original_len)) * 100 if original_len > 0 else 0

    print("\n" + "="*50)
    print("🗜️ RÉSULTAT COMPRESSÉ :")
    print("="*50)
    print(compressed_text)
    print("="*50)
    
    print(f"\n📊 Statistiques de compression :")
    print(f"- Avant : {original_len} caractères")
    print(f"- Après : {new_len} caractères")
    print(f"- Réduction de la taille du contexte : {ratio:.1f} %")

if __name__ == "__main__":
    main()
