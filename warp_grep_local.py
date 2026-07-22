import os
import sys
import subprocess
import json
import urllib.request
from urllib.error import HTTPError, URLError
import argparse

def run_ripgrep(search_term: str, repo_path: str) -> str:
    """Exécute ripgrep et retourne le résultat brut avec numéros de ligne."""
    try:
        # -n = numéros de ligne, -i = insensible à la casse, -I = ignorer les binaires
        result = subprocess.run(
            ["rg", "-n", "-i", "-I", search_term, repo_path], 
            capture_output=True, 
            text=True
        )
        return result.stdout
    except FileNotFoundError:
        print("❌ Erreur : 'ripgrep' (rg) n'est pas installé sur votre système.")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Recherche isolée (WarpGrep clone) via Mistral.")
    parser.add_argument("query", help="Ce que vous cherchez (ex: 'Où est calculée la TVA ?')")
    parser.add_argument("-d", "--dir", default=".", help="Dossier à fouiller (défaut: dossier courant)")
    parser.add_argument("-k", "--keyword", required=True, help="Mot-clé technique strict pour ripgrep (ex: 'tax', 'def ', 'class')")
    args = parser.parse_args()

    api_key = os.environ.get("MISTRAL_API_KEY")
    if not api_key:
        print("❌ Erreur : La variable MISTRAL_API_KEY n'est pas définie.")
        sys.exit(1)

    print(f"🔍 1. Exécution de ripgrep avec le mot-clé : '{args.keyword}'...")
    raw_grep_output = run_ripgrep(args.keyword, args.dir)

    if not raw_grep_output.strip():
        print("⚠️ ripgrep n'a rien trouvé avec ce mot-clé.")
        sys.exit(0)

    # Tronquer si la sortie est vraiment trop massive (sécurité pour l'API)
    max_chars = 40000
    if len(raw_grep_output) > max_chars:
        raw_grep_output = raw_grep_output[:max_chars] + "\n... [TRONQUÉ]"

    print("🧠 2. Analyse isolée par Mistral en cours (filtrage du bruit)...")
    
    system_prompt = """You are WarpGrep, an isolated code search sub-agent.
Your job is to read raw `ripgrep` search results and answer the user's natural language query.
The raw grep output format is `filepath:linenumber: code line`.

RULES:
1. DO NOT explain your reasoning.
2. ONLY output the relevant file paths, the line number spans, and a very brief summary of what is there.
3. If the grep output does not contain the answer to the user's query, output "No relevant matches found."."""

    user_prompt = f"USER QUERY: {args.query}\n\nRAW GREP OUTPUT:\n{raw_grep_output}"

    # --- Appel API Direct ---
    url = "https://api.mistral.ai/v1/chat/completions"
    data = {
        "model": "codestral-latest",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.1 # Basse température pour des faits précis
    }
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    req = urllib.request.Request(url, data=json.dumps(data).encode("utf-8"), headers=headers, method="POST")
    
    try:
        with urllib.request.urlopen(req) as response:
            response_data = json.loads(response.read().decode("utf-8"))
            clean_answer = response_data["choices"][0]["message"]["content"]
    except HTTPError as e:
        print(f"❌ Erreur API HTTP {e.code} : {e.read().decode('utf-8')}")
        sys.exit(1)
    except URLError as e:
        print(f"❌ Erreur de connexion : {e.reason}")
        sys.exit(1)

    print("\n" + "="*50)
    print("🎯 RÉSULTAT PROPRE (à envoyer à l'agent principal) :")
    print("="*50)
    print(clean_answer)
    print("="*50 + "\n")

if __name__ == "__main__":
    main()
