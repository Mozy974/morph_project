cat << 'EOF' > morph_mistral.py
import os
import sys
import re
import argparse
from mistralai.client import MistralClient
from mistralai.models.chat_completion import ChatMessage

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
        
        if len(valid_lines) < 2:
            continue
            
        anchor_start = valid_lines[0].strip()
        anchor_end = valid_lines[-1].strip()
        
        start_idx = result.find(anchor_start)
        if start_idx == -1:
            print(f"❌ Échec bloc {i+1} : Ancre de début introuvable -> '{anchor_start}'")
            continue
            
        line_start_idx = result.rfind('\n', 0, start_idx)
        line_start_idx = line_start_idx + 1 if line_start_idx != -1 else 0
            
        search_offset = start_idx + len(anchor_start)
        end_idx = result.find(anchor_end, search_offset)
        
        if end_idx == -1:
            print(f"❌ Échec bloc {i+1} : Ancre de fin introuvable -> '{anchor_end}'")
            continue
            
        replace_end_idx = end_idx + len(anchor_end)
        clean_block = block.strip('\n')
        
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
    
    system_prompt = """You are a coding assistant. Your task is to edit the provided code based on the user's instructions.
CRITICAL: You must NEVER rewrite the entire file. You must ONLY output the modified sections using the following lazy-edit format:

# ... existing code ...
[your modified lines with context]
# ... existing code ...

Use the correct comment syntax for the language (e.g., // for JS, # for Python).
Do not output any explanations or conversational text."""

    user_prompt = f"<instruction>{args.instruction}</instruction>\n\n<code>\n{original_code}\n</code>"

    client = MistralClient(api_key=api_key)
    try:
        response = client.chat(
            model="codestral-latest",
            messages=[
                ChatMessage(role="system", content=system_prompt),
                ChatMessage(role="user", content=user_prompt)
            ]
        )
    except Exception as e:
        print(f"❌ Erreur lors de l'appel à l'API Mistral : {e}")
        sys.exit(1)

    raw_response = response.choices[0].message.content
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
EOF