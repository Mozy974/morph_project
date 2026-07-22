import os
import sys
import subprocess
import argparse

# --- Palette de couleurs ---
CYAN = '\033[96m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
RESET = '\033[0m'

def run_command(command_list):
    """Exécute une commande de manière sécurisée."""
    try:
        subprocess.run(command_list, check=True)
    except subprocess.CalledProcessError:
        print(f"\n{RED}❌ Erreur lors de l'exécution. Arrêt du pipeline.{RESET}")
        sys.exit(1)
    except KeyboardInterrupt:
        print(f"\n{RED}🛑 Annulé par l'utilisateur.{RESET}")
        sys.exit(0)

def main():
    # 1. Configuration des arguments en ligne de commande
    parser = argparse.ArgumentParser(description="MORPH PIPELINE : Agent IA")
    parser.add_argument("instruction", nargs="?", help="L'instruction de modification")
    parser.add_argument("file", nargs="?", help="Le fichier cible")
    parser.add_argument("-k", "--keyword", help="Mot-clé optionnel pour WarpGrep")
    parser.add_argument("-y", "--yes", action="store_true", help="Valider automatiquement la modification sans demander")
    
    args = parser.parse_args()

    print(f"{CYAN}{'='*60}")
    print("🚀 MORPH PIPELINE V3")
    print(f"{'='*60}{RESET}")

    # 2. Choix du mode (Express ou Interactif)
    if args.instruction and args.file:
        print(f"{GREEN}⚡ Mode Express activé !{RESET}")
        instruction = args.instruction
        target_file = args.file
        keyword = args.keyword or ""
        auto_confirm = args.yes
    else:
        # Mode Interactif (si aucun argument n'est passé)
        instruction = input(f"\n{YELLOW}1. Que voulez-vous coder/modifier ?{RESET}\n> ")
        if not instruction.strip(): sys.exit(0)

        keyword = input(f"\n{YELLOW}2. Mot-clé de recherche (ou Entrée pour ignorer) :{RESET}\n> ")

        print(f"\n{CYAN}--- 🎯 CIBLE ---{RESET}")
        raw_target = input(f"{YELLOW}Quel fichier modifier ? (Glissez-déposez ici){RESET}\n> ")
        target_file = raw_target.strip().strip("'").strip('"').strip()
        
        if not target_file: sys.exit(0)
        auto_confirm = False

    # 3. Vérification de sécurité
    if not os.path.exists(target_file):
        print(f"{RED}❌ Le fichier '{target_file}' est introuvable.{RESET}")
        sys.exit(1)

    # 4. Éxécution du pipeline
    if keyword.strip():
        print(f"\n{CYAN}--- 🔍 RECHERCHE (WarpGrep) ---{RESET}")
        run_command(["python", "warp_grep_local.py", instruction, "-k", keyword])

    print(f"\n{CYAN}--- 🗜️ ANALYSE DU CONTEXTE (Compact) ---{RESET}")
    run_command(["python", "morph_compact.py", target_file, "-q", instruction])

    print(f"\n{CYAN}--- 🚀 MODIFICATION (Fast Apply) ---{RESET}")
    
    # 5. Confirmation finale
    if auto_confirm:
        confirm = "o"
        print(f"{YELLOW}Validation automatique activée (-y). Application en cours...{RESET}")
    else:
        confirm = input(f"{YELLOW}Prêt à modifier {target_file} ? (Entrée = Oui, n = Non){RESET}\n> ")
    
    if confirm.lower() != 'n':
        run_command(["python", "morph_mistral.py", target_file, "-i", instruction])
        print(f"\n{GREEN}🎉 TERMINÉ ! Votre fichier a été mis à jour.{RESET}")
    else:
        print(f"{RED}Modification annulée.{RESET}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{RED}🛑 Sortie rapide.{RESET}")
        sys.exit(0)