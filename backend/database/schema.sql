-- ============================================================
-- EduTrack Madagascar AI — Schéma de base de données
-- Compatible SQLite. Notes de portage PostgreSQL en commentaire.
-- ============================================================

PRAGMA foreign_keys = ON;

-- ---------------- CLASSES ----------------
CREATE TABLE IF NOT EXISTS classes (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,   -- PostgreSQL: SERIAL PRIMARY KEY
    nom           TEXT NOT NULL UNIQUE,                 -- ex : "6e A"
    niveau        TEXT NOT NULL,                         -- ex : "6e"
    annee_scolaire TEXT NOT NULL                          -- ex : "2025-2026"
);

-- ---------------- MATIERES ----------------
CREATE TABLE IF NOT EXISTS matieres (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    nom           TEXT NOT NULL UNIQUE                  -- ex : "Mathématiques"
);

-- ---------------- ELEVES ----------------
CREATE TABLE IF NOT EXISTS eleves (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    nom             TEXT NOT NULL,
    prenom          TEXT NOT NULL,
    date_naissance  DATE,
    classe_id       INTEGER NOT NULL,
    contact_parent  TEXT,                                 -- téléphone ou email du responsable
    date_creation   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (classe_id) REFERENCES classes(id) ON DELETE RESTRICT
);

-- ---------------- UTILISATEURS ----------------
-- Comptes applicatifs : enseignant, parent, administrateur
CREATE TABLE IF NOT EXISTS utilisateurs (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    nom_complet     TEXT NOT NULL,
    email           TEXT NOT NULL UNIQUE,
    mot_de_passe TEXT NOT NULL,
    role            TEXT NOT NULL CHECK (role IN ('enseignant','parent','admin')),
    eleve_id        INTEGER,                              -- renseigné uniquement si role = 'parent'
    FOREIGN KEY (eleve_id) REFERENCES eleves(id) ON DELETE SET NULL
);

-- ---------------- ENSEIGNANT_CLASSE (association) ----------------
CREATE TABLE IF NOT EXISTS enseignant_classe (
    enseignant_id   INTEGER NOT NULL,
    classe_id       INTEGER NOT NULL,
    matiere_id      INTEGER NOT NULL,
    PRIMARY KEY (enseignant_id, classe_id, matiere_id),
    FOREIGN KEY (enseignant_id) REFERENCES utilisateurs(id) ON DELETE CASCADE,
    FOREIGN KEY (classe_id) REFERENCES classes(id) ON DELETE CASCADE,
    FOREIGN KEY (matiere_id) REFERENCES matieres(id) ON DELETE CASCADE
);

-- ---------------- NOTES ----------------
CREATE TABLE IF NOT EXISTS notes (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    eleve_id      INTEGER NOT NULL,
    matiere_id    INTEGER NOT NULL,
    valeur        REAL NOT NULL CHECK (valeur >= 0 AND valeur <= 20),
    date_evaluation DATE NOT NULL,
    trimestre     INTEGER CHECK (trimestre IN (1,2,3)),
    commentaire   TEXT,
    FOREIGN KEY (eleve_id) REFERENCES eleves(id) ON DELETE CASCADE,
    FOREIGN KEY (matiere_id) REFERENCES matieres(id) ON DELETE CASCADE
);

-- ---------------- ABSENCES ----------------
CREATE TABLE IF NOT EXISTS absences (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    eleve_id      INTEGER NOT NULL,
    date_absence  DATE NOT NULL,
    justifiee     INTEGER NOT NULL DEFAULT 0,             -- 0 = non, 1 = oui (PostgreSQL: BOOLEAN)
    motif         TEXT,
    FOREIGN KEY (eleve_id) REFERENCES eleves(id) ON DELETE CASCADE
);

-- ---------------- ALERTES ----------------
-- Générées automatiquement par le moteur de scoring
CREATE TABLE IF NOT EXISTS alertes (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    eleve_id        INTEGER NOT NULL,
    date_creation   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    niveau_risque   TEXT NOT NULL CHECK (niveau_risque IN ('stable','a_surveiller','risque_eleve')),
    score           INTEGER NOT NULL,
    motif           TEXT NOT NULL,
    statut          TEXT NOT NULL DEFAULT 'ouverte' CHECK (statut IN ('ouverte','traitee')),
    FOREIGN KEY (eleve_id) REFERENCES eleves(id) ON DELETE CASCADE
);

-- ---------------- RECOMMANDATIONS ----------------
CREATE TABLE IF NOT EXISTS recommandations (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    eleve_id        INTEGER NOT NULL,
    matiere_id      INTEGER,                              -- NULL si recommandation générale
    texte           TEXT NOT NULL,
    date_creation   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (eleve_id) REFERENCES eleves(id) ON DELETE CASCADE,
    FOREIGN KEY (matiere_id) REFERENCES matieres(id) ON DELETE SET NULL
);

-- ---------------- HISTORIQUE SCOLAIRE ----------------
-- Une ligne par élève et par période (ex : par trimestre), pour suivre la progression
CREATE TABLE IF NOT EXISTS historique_scolaire (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    eleve_id          INTEGER NOT NULL,
    annee_scolaire    TEXT NOT NULL,
    trimestre         INTEGER CHECK (trimestre IN (1,2,3)),
    classe            TEXT NOT NULL,
    moyenne_generale  REAL,
    total_absences    INTEGER DEFAULT 0,
    FOREIGN KEY (eleve_id) REFERENCES eleves(id) ON DELETE CASCADE
);

-- ---------------- INDEX ----------------
CREATE INDEX IF NOT EXISTS idx_notes_eleve ON notes(eleve_id);
CREATE INDEX IF NOT EXISTS idx_absences_eleve ON absences(eleve_id);
CREATE INDEX IF NOT EXISTS idx_alertes_eleve ON alertes(eleve_id);
CREATE INDEX IF NOT EXISTS idx_recommandations_eleve ON recommandations(eleve_id);
CREATE INDEX IF NOT EXISTS idx_eleves_classe ON eleves(classe_id);
