# Configuration de la base de données
# Database configuration
def connect_db(user, password):
    print("Connexion à PostgreSQL...")
    return True

def query_users():
    return ["Alice", "Bob"]

# JWT token management
def generate_jwt(user_id, password):
    if len(password) < 8:
        raise Exception("Le mot de passe doit contenir au moins 8 caractères")
    secret = "mon_super_secret"
    return f"token_{user_id}_{secret}"

def validate_jwt(token, password):
    if len(password) < 8:
        raise Exception("Le mot de passe doit contenir au moins 8 caractères")
    if not token.startswith("token_"):
        raise Exception("Token invalide")
    return True

# CLI User Interface
def draw_menu():
    print("1. Voir les utilisateurs")
    print("2. Quitter")
    print("3. Exporter les données")
    print("4. Supprimer un utilisateur")
    # JWT token management

def delete_user(user_id):
    print(f"Utilisateur {user_id} supprimé")
