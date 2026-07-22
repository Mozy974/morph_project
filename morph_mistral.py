import os
import sys
import re
import argparse
import json
import urllib.request
from urllib.error import HTTPError, URLError

def clean_markdown(text: str) -> str:
    text = re.sub(r"^```[a-zA-Z]*\n", "", text, flags=re.MULTILINE)
    text = re.sub(r"```$", "", text, flags=re.MULTILINE)
    return text.strip()

def fast_apply(original_content: str, edit_snippet: str) -> str:
    original = original_content.replace("\r\n", "\n")
    snippet = edit_snippet.replace("\r\n", "\n")

    marker_regex = re.compile(r"^(?:\s*//|\s*#|\s*<!--)\s*\.\.\.\s*existing code\s*\.\.\.(?:\s*-->)?\s*$", re.MULTILINE)
    blocks = marker_regex.split(snippet)
    blocks = [b.strip("\n") for b in blocks if b.strip("\n")]

    if not blocks:
        print("⚠️ Aucun marqueur valide trouvé dans la réponse du modèle.")
        return original

    result = original

    for i, block in enumerate(blocks):
        lines = block.split("\n")
        valid_lines = [l for l in lines if l.strip()]
        
        if not valid_lines:
            continue
            
        # 1. Chercher la PREMIÈRE ligne du bloc qui existe dans le code original
        start_idx = -1
        anchor_start = None
        for line in valid_lines:
            idx = result.find(line.strip())
            if idx != -1:
                start_idx = idx
                anchor_start = line.strip()
                break
                
        # 2. Chercher la DERNIÈRE ligne du bloc qui existe dans le code original
        end_idx = -1
        anchor_end = None
        for line in reversed(valid_lines):
            idx = result.rfind(line.strip())
            if idx != -1 and (start_idx == -1 or idx >= start_idx):
                end_idx = idx
                anchor_end = line.strip()
                break

        clean_block = block.strip('\n')

        # Cas A : Aucune ligne de contexte trouvée -> C'est un nouvel ajout pur
        if start_idx == -1 and end_idx == -1:
            print(f"⚠️ Bloc {i+1} : Aucun contexte trouvé. Ajout automatique à la fin du fichier.")
            if not result.endswith("\n"):
                result += "\n"
            result += "\n" + clean_block + "\n"
            continue

        # Cas B : On a trouvé des ancres, on fait le remplacement propre
        line_start_idx = result.rfind('\n', 0, start_idx)
        line_start_idx = line_start_idx + 1 if line_start_idx != -1 else 0
        
        replace_end_idx = end_idx + len(anchor_end)
        
        result = result[:line_start_idx] + clean_block + result[replace_end_idx:]
        print(f"✅ Bloc {i+1} fusionné avec succès !")

    return result

def main():
    parser = argparse.ArgumentParser(description="Édite un fichier via l'API Mistral (Fast Apply).")
    parser.add_argument("file", help="Chemin vers le fichier à modifier")
    parser.add_argument("-i", "--instruction", required=True, help="Instruction de modification (ex: 'Ajoute la TVA')")
    args = parser.parse_args()

    api_key = os.environ.get("MISTRAL_API_KEY")
    if not api_key:
        print("❌ Erreur : La variable d'environnement MISTRAL_API_KEY n'est pas définie.")
        sys.exit(1)

    filepath = args.file
    if not os.path.exists(filepath):
        print(f"❌ Erreur : Le fichier {filepath} n'existe pas.")
        sys.exit(1)

    with open(filepath, "r", encoding="utf-8") as f:
        original_code = f.read()

    print(f"🚀 Analyse de {filepath} en cours...")
    
    # System prompt renforcé pour obliger le modèle à donner du contexte
    system_prompt = """You are a coding assistant. Your task is to edit the provided code based on the user's instructions.
CRITICAL: You must NEVER rewrite the entire file. You must ONLY output the modified sections using the following lazy-edit format:

# ... existing code ...
[at least 2 lines of existing code before]
[your modifications]
[at least 2 lines of existing code after]
# ... existing code ...

Use the correct comment syntax for the language (e.g., // for JS, # for Python).
Do not output any explanations or conversational text."""

    user_prompt = f"<instruction>{args.instruction}</instruction>\n\n<code>\n{original_code}\n</code>"

    # --- Appel API Direct via urllib ---
    url = "https://api.mistral.ai/v1/chat/completions"
    data = {
        "model": "codestral-latest",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    }
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    req = urllib.request.Request(url, data=json.dumps(data).encode("utf-8"), headers=headers, method="POST")
    
    try:
        with urllib.request.urlopen(req) as response:
            response_data = json.loads(response.read().decode("utf-8"))
            raw_response = response_data["choices"][0]["message"]["content"]
    except HTTPError as e:
        print(f"❌ Erreur API HTTP {e.code} : {e.read().decode('utf-8')}")
        sys.exit(1)
    except URLError as e:
        print(f"❌ Erreur de connexion : {e.reason}")
        sys.exit(1)
    # -----------------------------------

    print("\n--- Réponse brute du modèle ---")
    print(raw_response)
    print("-------------------------------\n")

    clean_snippet = clean_markdown(raw_response)
    new_code = fast_apply(original_code, clean_snippet)

    if new_code != original_code:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(new_code)
        print(f"🎉 Modification appliquée et sauvegardée dans {filepath} !")
    else:
        print("⚠️ Aucune modification n'a pu être appliquée au fichier.")

if __name__ == "__main__":
    main()