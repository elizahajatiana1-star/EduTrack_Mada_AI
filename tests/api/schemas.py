"""
schemas.py — Le "contrat" JSON de l'API EduTrack
--------------------------------------------------
Ce fichier définit à quoi doivent ressembler les données envoyées
et reçues par l'API. C'est ce document (une fois figé) que tu dois
partager avec la Personne 4 (Interface) : il décrit exactement les
champs attendus dans chaque requête et chaque réponse.

Pydantic valide automatiquement les données entrantes : si un champ
obligatoire manque, ou si un type est faux (ex: texte au lieu de
nombre), FastAPI renvoie automatiquement une erreur 422 claire,
sans que tu aies à écrire ce contrôle toi-même.
"""

from pydantic import BaseModel, Field
from datetime import date, datetime
from typing import Optional


# ============================================================
# CLASSES / MATIERES (lecture seule pour l'instant, gérées par P1)
# ============================================================
class ClasseOut(BaseModel):
    id: int
    nom: str
    niveau: str
    annee_scolaire: str

    class Config:
        from_attributes = True  # permet de créer ce schéma depuis un objet SQLAlchemy


class MatiereOut(BaseModel):
    id: int
    nom: str

    class Config:
        from_attributes = True


# ============================================================
# ELEVES
# ============================================================
class EleveBase(BaseModel):
    nom: str = Field(..., min_length=1, description="Nom de l'élève, ne peut pas être vide")
    prenom: str = Field(..., min_length=1, description="Prénom de l'élève, ne peut pas être vide")
    date_naissance: Optional[date] = None
    classe_id: int
    contact_parent: Optional[str] = None


class EleveCreate(EleveBase):
    """Corps attendu pour POST /api/eleves"""
    pass


class EleveUpdate(BaseModel):
    """Corps attendu pour PUT /api/eleves/{id} (tous les champs optionnels)"""
    nom: Optional[str] = Field(None, min_length=1)
    prenom: Optional[str] = Field(None, min_length=1)
    date_naissance: Optional[date] = None
    classe_id: Optional[int] = None
    contact_parent: Optional[str] = None


class EleveOut(EleveBase):
    """Réponse renvoyée pour un élève"""
    id: int
    date_creation: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============================================================
# NOTES
# ============================================================
class NoteCreate(BaseModel):
    eleve_id: int
    matiere_id: int
    valeur: float = Field(..., ge=0, le=20, description="Note comprise entre 0 et 20")
    date_evaluation: date
    trimestre: Optional[int] = Field(None, ge=1, le=3)
    commentaire: Optional[str] = None


class NoteOut(NoteCreate):
    id: int

    class Config:
        from_attributes = True


# ============================================================
# ABSENCES
# ============================================================
class AbsenceCreate(BaseModel):
    eleve_id: int
    date_absence: date
    justifiee: bool = False
    motif: Optional[str] = None


class AbsenceOut(BaseModel):
    id: int
    eleve_id: int
    date_absence: date
    justifiee: bool
    motif: Optional[str] = None

    class Config:
        from_attributes = True


# ============================================================
# SCORING / ALERTES / RECOMMANDATIONS
# ============================================================
class ScoreOut(BaseModel):
    eleve_id: int
    score: int
    niveau_risque: str  # "stable" | "a_surveiller" | "risque_eleve"
    motif: str


class AlerteOut(BaseModel):
    id: int
    eleve_id: int
    niveau_risque: str
    score: int
    motif: str
    statut: str
    date_creation: Optional[datetime] = None

    class Config:
        from_attributes = True


class RecommandationOut(BaseModel):
    id: int
    eleve_id: int
    matiere_id: Optional[int] = None
    texte: str
    date_creation: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============================================================
# ERREURS
# ============================================================
class ErrorResponse(BaseModel):
    error: str
