"""
app.py — API EduTrack Madagascar AI (Personne 2 : Backend/API)
------------------------------------------------------------------
Framework : FastAPI (choisi car requirements.txt de la Personne 1
le prévoyait déjà, et parce qu'il génère la doc interactive tout seul
sur /docs).

Pour lancer l'API en local :
    uvicorn app:app --reload

Puis ouvrir : http://127.0.0.1:8000/docs (doc interactive Swagger)
"""

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session as SQLASession
from sqlalchemy import func
from typing import List

from models import Session, Eleve, Note, Absence, Alerte, Recommandation, Classe
import schemas
from scoring_stub import calculer_score, generer_recommandations
# Quand la Personne 3 livre son fichier, remplace la ligne au-dessus par :
# from scoring import calculer_score, generer_recommandations

app = FastAPI(
    title="EduTrack Madagascar AI — API",
    description="API de suivi scolaire (élèves, notes, absences, alertes)",
    version="0.1.0",
)

# Permet à l'interface (Personne 4), servie sur un autre port, d'appeler l'API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # à restreindre en production
    allow_methods=["*"],
    allow_headers=["*"],
)


# ------------------------------------------------------------------
# Dépendance : une session de BDD par requête
# ------------------------------------------------------------------
def get_db():
    db = Session()
    try:
        yield db
    finally:
        db.close()


# ------------------------------------------------------------------
# Sécurité simplifiée (Étape 4 - optionnelle)
# ------------------------------------------------------------------
# Démo simple : le "rôle" et l'"eleve_id autorisé" sont passés en en-têtes
# HTTP par l'interface. Un vrai système utiliserait des tokens JWT liés
# à la table `utilisateurs`, mais son schéma diffère encore de models.py
# (voir README, section "Point d'attention") donc on reste simple ici.
def role_actuel(x_role: str = "enseignant", x_eleve_autorise: int | None = None):
    return {"role": x_role, "eleve_autorise": x_eleve_autorise}


def verifier_acces_eleve(eleve_id: int, auth=Depends(role_actuel)):
    if auth["role"] == "parent" and auth["eleve_autorise"] != eleve_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Un parent ne peut consulter que la fiche de son propre enfant",
        )
    return auth


# ------------------------------------------------------------------
# Utilitaire : récupérer un élève ou lever une 404 propre
# ------------------------------------------------------------------
def get_eleve_ou_404(db: SQLASession, eleve_id: int) -> Eleve:
    eleve = db.query(Eleve).filter(Eleve.id == eleve_id).first()
    if eleve is None:
        raise HTTPException(status_code=404, detail="Élève non trouvé")
    return eleve


# ==================================================================
# CRUD ELEVES
# ==================================================================
@app.get("/api/eleves", response_model=List[schemas.EleveOut])
def lister_eleves(db: SQLASession = Depends(get_db)):
    return db.query(Eleve).all()


@app.get("/api/eleves/{eleve_id}", response_model=schemas.EleveOut)
def obtenir_eleve(eleve_id: int, db: SQLASession = Depends(get_db)):
    return get_eleve_ou_404(db, eleve_id)


@app.post("/api/eleves", response_model=schemas.EleveOut, status_code=201)
def creer_eleve(payload: schemas.EleveCreate, db: SQLASession = Depends(get_db)):
    classe = db.query(Classe).filter(Classe.id == payload.classe_id).first()
    if classe is None:
        raise HTTPException(status_code=400, detail="classe_id invalide : cette classe n'existe pas")

    eleve = Eleve(**payload.model_dump())
    db.add(eleve)
    db.commit()
    db.refresh(eleve)
    return eleve


@app.put("/api/eleves/{eleve_id}", response_model=schemas.EleveOut)
def modifier_eleve(eleve_id: int, payload: schemas.EleveUpdate, db: SQLASession = Depends(get_db)):
    eleve = get_eleve_ou_404(db, eleve_id)
    donnees = payload.model_dump(exclude_unset=True)
    for champ, valeur in donnees.items():
        setattr(eleve, champ, valeur)
    db.commit()
    db.refresh(eleve)
    return eleve


@app.delete("/api/eleves/{eleve_id}", status_code=204)
def supprimer_eleve(eleve_id: int, db: SQLASession = Depends(get_db)):
    eleve = get_eleve_ou_404(db, eleve_id)
    db.delete(eleve)
    db.commit()
    return None


# ==================================================================
# NOTES
# ==================================================================
@app.post("/api/notes", response_model=schemas.NoteOut, status_code=201)
def ajouter_note(payload: schemas.NoteCreate, db: SQLASession = Depends(get_db)):
    get_eleve_ou_404(db, payload.eleve_id)  # vérifie que l'élève existe
    # payload.valeur est déjà validé entre 0 et 20 par schemas.NoteCreate (Field ge=0, le=20)
    note = Note(**payload.model_dump())
    db.add(note)
    db.commit()
    db.refresh(note)
    return note


# ==================================================================
# ABSENCES
# ==================================================================
@app.post("/api/absences", response_model=schemas.AbsenceOut, status_code=201)
def ajouter_absence(payload: schemas.AbsenceCreate, db: SQLASession = Depends(get_db)):
    get_eleve_ou_404(db, payload.eleve_id)
    absence = Absence(
        eleve_id=payload.eleve_id,
        date_absence=payload.date_absence,
        justifiee=1 if payload.justifiee else 0,
        motif=payload.motif,
    )
    db.add(absence)
    db.commit()
    db.refresh(absence)
    # on reconvertit 0/1 en booléen pour respecter AbsenceOut
    return schemas.AbsenceOut(
        id=absence.id,
        eleve_id=absence.eleve_id,
        date_absence=absence.date_absence,
        justifiee=bool(absence.justifiee),
        motif=absence.motif,
    )


# ==================================================================
# SCORING (intégration avec la Personne 3)
# ==================================================================
@app.get("/api/eleves/{eleve_id}/score", response_model=schemas.ScoreOut)
def obtenir_score(eleve_id: int, db: SQLASession = Depends(get_db), auth=Depends(verifier_acces_eleve)):
    eleve = get_eleve_ou_404(db, eleve_id)

    notes = [n.valeur for n in eleve.notes]
    nb_absences_non_justifiees = sum(1 for a in eleve.absences if not a.justifiee)

    resultat = calculer_score(notes, nb_absences_non_justifiees)

    # On enregistre l'alerte en BDD si le niveau de risque n'est pas "stable"
    if resultat["niveau_risque"] != "stable":
        alerte = Alerte(
            eleve_id=eleve_id,
            niveau_risque=resultat["niveau_risque"],
            score=resultat["score"],
            motif=resultat["motif"],
            statut="ouverte",
        )
        db.add(alerte)
        db.commit()

    return schemas.ScoreOut(eleve_id=eleve_id, **resultat)


@app.get("/api/alertes", response_model=List[schemas.AlerteOut])
def lister_alertes(db: SQLASession = Depends(get_db)):
    return (
        db.query(Alerte)
        .filter(Alerte.statut == "ouverte")
        .order_by(Alerte.score.desc())
        .all()
    )


@app.get("/api/eleves/{eleve_id}/recommandations", response_model=List[str])
def obtenir_recommandations(eleve_id: int, db: SQLASession = Depends(get_db)):
    eleve = get_eleve_ou_404(db, eleve_id)
    notes = [n.valeur for n in eleve.notes]
    nb_absences_non_justifiees = sum(1 for a in eleve.absences if not a.justifiee)
    resultat = calculer_score(notes, nb_absences_non_justifiees)
    return generer_recommandations(resultat)


# ==================================================================
# Racine (pratique pour vérifier que l'API tourne)
# ==================================================================
@app.get("/")
def racine():
    return {"message": "API EduTrack en ligne. Voir /docs pour la documentation interactive."}
