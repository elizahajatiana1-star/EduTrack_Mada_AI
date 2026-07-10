import os
import sqlite3

DB_NAME = "edutrack.db"

def initialiser_base():
    print("🧹 Nettoyage de l'ancienne base de données...")
    if os.path.exists(DB_NAME):
        try:
            os.remove(DB_NAME)
            print(" -> Fichier edutrack.db supprimé avec succès.")
        except Exception as e:
            print(f"⚠️ Impossible de supprimer le fichier .db : {e}")

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    print("🏗️ Création des tables dans la base SQLite...")
    
    # 1. Table Classes (CORRECTION ICI : annee_scolaire avec deux 'e')
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS classes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nom TEXT NOT NULL,
        niveau TEXT NOT NULL,
        annee_scolaire TEXT
    );
    """)

    # 2. Table Eleves
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS eleves (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nom TEXT NOT NULL,
        prenom TEXT NOT NULL,
        classe_id INTEGER NOT NULL,
        date_naissance TEXT,
        contact_parent TEXT,
        FOREIGN KEY(classe_id) REFERENCES classes(id)
    );
    """)

    # 3. Table Notes
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        eleve_id INTEGER NOT NULL,
        matiere_id INTEGER NOT NULL,
        valeur REAL NOT NULL,
        date_evaluation TEXT NOT NULL,
        trimestre INTEGER NOT NULL,
        FOREIGN KEY(eleve_id) REFERENCES eleves(id)
    );
    """)

    # 4. Table Absences
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS absences (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        eleve_id INTEGER NOT NULL,
        date_absence TEXT NOT NULL,
        justifie INTEGER DEFAULT 0,
        FOREIGN KEY(eleve_id) REFERENCES eleves(id)
    );
    """)

    # 5. Table Alertes
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS alertes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        eleve_id INTEGER NOT NULL,
        score INTEGER NOT NULL,
        niveau_risque TEXT NOT NULL,
        motif TEXT NOT NULL,
        date_creation TEXT NOT NULL,
        FOREIGN KEY(eleve_id) REFERENCES eleves(id)
    );
    """)

    print("🏫 Création de la classe par défaut...")
    # CORRECTION ICI AUSSI : annee_scolaire
    cursor.execute("INSERT INTO classes (nom, niveau, annee_scolaire) VALUES (?, ?, ?)", ("3ème A", "Collège", "2025-2026"))
    classe_id = cursor.lastrowid

    print("👤 Insertion des élèves de test obligatoires...")
    eleves_test = [
        ("Ramananarivo", "Tahina", classe_id, "2012-05-14", "+261 34 00 000 01"),
        ("Rakoto", "Faly", classe_id, "2011-08-22", "+261 33 11 111 11"),
        ("Andria", "Mika", classe_id, "2012-01-10", "+261 32 22 222 22")
    ]
    cursor.executemany("INSERT INTO eleves (nom, prenom, classe_id, date_naissance, contact_parent) VALUES (?, ?, ?, ?, ?)", eleves_test)

    print("📊 Insertion des notes initiales...")
    notes_test = [
        (1, 1, 7.5, "2026-03-01", 3),  # Tahina - Maths - 7.5
        (1, 2, 8.0, "2026-03-05", 3),  # Tahina - Français - 8.0
        (2, 1, 14.5, "2026-03-02", 3), # Faly - Maths - 14.5
        (2, 2, 12.0, "2026-03-06", 3), # Faly - Français - 12.0
        (3, 1, 9.5, "2026-03-02", 3),  # Mika - Maths - 9.5
        (3, 2, 10.5, "2026-03-06", 3)  # Mika - Français - 10.5
    ]
    cursor.executemany("INSERT INTO notes (eleve_id, matiere_id, valeur, date_evaluation, trimestre) VALUES (?, ?, ?, ?, ?)", notes_test)

    conn.commit()
    conn.close()
    print("✅ Base de données EduTrack initialisée avec succès avec les bonnes colonnes !")

if __name__ == "__main__":
    initialiser_base()