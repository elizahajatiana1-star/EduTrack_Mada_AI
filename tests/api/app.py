from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime

# --- CONFIGURATION BASE DE DONNÉES ---
DATABASE_URL = "sqlite:///./edutrack.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- MODÈLES ORM SQLALCHEMY ---
class Classe(Base):
    __tablename__ = "classes"
    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String, nullable=False)
    niveau = Column(String, nullable=False)
    # ✅ FIXATION : Alignement strict sur ton fichier .db existant (un seul 'e')
    anne_scolaire = Column(String, nullable=True)

class Eleve(Base):
    __tablename__ = "eleves"
    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String, nullable=False)
    prenom = Column(String, nullable=False)
    classe_id = Column(Integer, ForeignKey("classes.id"), nullable=False)
    date_naissance = Column(String, nullable=True)
    contact_parent = Column(String, nullable=True)

class Note(Base):
    __tablename__ = "notes"
    id = Column(Integer, primary_key=True, index=True)
    eleve_id = Column(Integer, ForeignKey("eleves.id"), nullable=False)
    matiere_id = Column(Integer, nullable=False)  # 1 = Mathématiques, 2 = Français
    valeur = Column(Float, nullable=False)
    date_evaluation = Column(String, nullable=False)
    trimestre = Column(Integer, nullable=False)

class Absence(Base):
    __tablename__ = "absences"
    id = Column(Integer, primary_key=True, index=True)
    eleve_id = Column(Integer, ForeignKey("eleves.id"), nullable=False)
    date_absence = Column(String, nullable=False)
    justifie = Column(Integer, default=0)

class Alerte(Base):
    __tablename__ = "alertes"
    id = Column(Integer, primary_key=True, index=True)
    eleve_id = Column(Integer, ForeignKey("eleves.id"), nullable=False)
    score = Column(Integer, nullable=False)
    niveau_risque = Column(String, nullable=False)
    motif = Column(String, nullable=False)
    date_creation = Column(String, nullable=False)

# Création des tables manquantes si nécessaire (sans écraser l'existant)
Base.metadata.create_all(bind=engine)

# --- APPLICATIONS FASTAPI & CORS ---
app = FastAPI(title="EduTrack Madagascar AI API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dépendance de session BDD
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- SCHÉMAS PYDANTIC (VALIDATION DES DONNÉES COUCHE WEB) ---
class EleveCreate(BaseModel):
    nom: str
    prenom: str
    classe_id: int
    date_naissance: Optional[str] = None
    contact_parent: Optional[str] = None

class NoteCreate(BaseModel):
    eleve_id: int
    matiere_id: int
    valeur: float
    date_evaluation: str
    trimestre: int

# --- API ENDPOINTS ---

# 1. Obtenir tous les élèves
@app.get("/api/eleves")
def obtenir_eleves(db: Session = Depends(get_db)):
    return db.query(Eleve).all()

# 2. Ajouter un élève
@app.post("/api/eleves")
def ajouter_eleve(eleve: EleveCreate, db: Session = Depends(get_db)):
    db_eleve = Eleve(
        nom=eleve.nom,
        prenom=eleve.prenom,
        classe_id=eleve.classe_id,
        date_naissance=eleve.date_naissance,
        contact_parent=eleve.contact_parent
    )
    db.add(db_eleve)
    db.commit()
    db.refresh(db_eleve)
    return db_eleve

# 3. Supprimer un élève
@app.delete("/api/eleves/{eleve_id}")
def supprimer_eleve(eleve_id: int, db: Session = Depends(get_db)):
    db_eleve = db.query(Eleve).filter(Eleve.id == eleve_id).first()
    if not db_eleve:
        raise HTTPException(status_code=404, detail="Élève non trouvé")
    
    # Nettoyer les notes, absences et alertes liées à cet élève avant suppression
    db.query(Note).filter(Note.eleve_id == eleve_id).delete()
    db.query(Absence).filter(Absence.eleve_id == eleve_id).delete()
    db.query(Alerte).filter(Alerte.eleve_id == eleve_id).delete()
    
    db.delete(db_eleve)
    db.commit()
    return {"message": "Élève supprimé avec succès"}

# 4. Obtenir les notes d'un élève spécifique
@app.get("/api/eleves/{eleve_id}/notes")
def obtenir_notes_eleve(eleve_id: int, db: Session = Depends(get_db)):
    return db.query(Note).filter(Note.eleve_id == eleve_id).all()

# 5. Obtenir les absences d'un élève spécifique
@app.get("/api/eleves/{eleve_id}/absences")
def obtenir_absences_eleve(eleve_id: int, db: Session = Depends(get_db)):
    return db.query(Absence).filter(Absence.eleve_id == eleve_id).all()

# 6. Ajouter une note
@app.post("/api/notes")
def ajouter_note(note: NoteCreate, db: Session = Depends(get_db)):
    db_note = Note(
        eleve_id=note.eleve_id,
        matiere_id=note.matiere_id,
        valeur=note.valeur,
        date_evaluation=note.date_evaluation,
        trimestre=note.trimestre
    )
    db.add(db_note)
    db.commit()
    db.refresh(db_note)
    return db_note

# 7. Obtenir toutes les alertes de l'IA active
@app.get("/api/alertes")
def obtenir_alertes(db: Session = Depends(get_db)):
    return db.query(Alerte).all()

# 8. MOTEUR IA : Calcul prédictif automatique du score de risque
@app.get("/api/eleves/{eleve_id}/score")
def calculer_score_ia(eleve_id: int, db: Session = Depends(get_db)):
    notes = db.query(Note).filter(Note.eleve_id == eleve_id).all()
    absences = db.query(Absence).filter(Absence.eleve_id == eleve_id).all()
    
    score = 0
    motifs = []
    
    # Règle d'alerte IA 1 : Moyenne globale insuffisante
    if notes:
        moyenne = sum([n.valeur for n in notes]) / len(notes)
        if moyenne < 10:
            score += 3
            motifs.append(f"Moyenne générale critique : {moyenne:.2f}/20")
    else:
        moyenne = 10.0  # Par défaut stable si pas encore de notes
        
    # Règle d'alerte IA 2 : Mauvaise note ciblée par matière
    for n in notes:
        if n.valeur < 8.0:
            score += 1
            nom_mat = "Mathématiques" if n.matiere_id == 1 else "Français"
            motifs.append(f"Note alarmante en {nom_mat} ({n.valeur}/20)")
            
    # Règle d'alerte IA 3 : Absentéisme non justifié
    abs_non_justifiees = len([a for a in absences if a.justifie == 0])
    if abs_non_justifiees > 2:
        score += 2
        motifs.append(f"Décrochage : {abs_non_justifiees} absences injustifiées")

    # Détermination du niveau de risque final
    niveau_risque = "stable"
    if score >= 4:
        niveau_risque = "risque_eleve"
    elif score >= 2:
        niveau_risque = "a_surveiller"

    # Enregistrement ou mise à jour automatique de l'alerte calculée dans SQLite
    if score > 0:
        db_alerte = db.query(Alerte).filter(Alerte.eleve_id == eleve_id).first()
        motif_final = " | ".join(motifs)
        if db_alerte:
            db_alerte.score = score
            db_alerte.niveau_risque = niveau_risque
            db_alerte.motif = motif_final
            db_alerte.date_creation = datetime.now().strftime("%Y-%m-%d")
        else:
            db_alerte = Alerte(
                eleve_id=eleve_id,
                score=score,
                niveau_risque=niveau_risque,
                motif=motif_final,
                date_creation=datetime.now().strftime("%Y-%m-%d")
            )
            db.add(db_alerte)
        db.commit()

    return {"eleve_id": eleve_id, "score": score, "niveau_risque": niveau_risque, "moyenne": moyenne}