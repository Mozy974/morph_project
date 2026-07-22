import sqlite3
import json

# Liste des 100 questions (remplacez par votre liste si besoin)
def load_questions_from_file(file_path):
    with open(file_path, 'r') as f:
        return [line.strip() for line in f if line.strip()]

questions = load_questions_from_file("~/Bureau/flotte/scripts/100_questions.txt")
# Chemin vers votre base de données state.db
DB_PATH = "~/Bureau/state.db"  # Ajustez si nécessaire

def create_table_if_not_exists(conn):
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()

def insert_questions(conn, questions):
    cursor = conn.cursor()
    for question in questions:
        cursor.execute("INSERT INTO questions (question) VALUES (?)", (question,))
    conn.commit()
    print(f"✅ {len(questions)} questions insérées avec succès.")

def main():
    try:
        # Connexion à la base de données (le ~ est converti en chemin absolu)
        db_path = os.path.expanduser(DB_PATH)
        conn = sqlite3.connect(db_path)

        # Création de la table si elle n'existe pas
        create_table_if_not_exists(conn)

        # Insertion des questions
        insert_questions(conn, questions)

    except Exception as e:
        print(f"❌ Erreur : {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    import os
    main()
