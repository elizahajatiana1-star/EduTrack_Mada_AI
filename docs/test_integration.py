"""
Tests d'INTÉGRATION 
Ces tests vérifient que
PLUSIEURS modules fonctionnent bien ENSEMBLE :
  - la base de données (models.py, Personne 1)
  - le moteur de scoring (scoring.py, Personne 3)

Ils utilisent une base SQLite TEMPORAIRE (fichier séparé), pour ne jamais
toucher à edutrack.db, la vraie base de démonstration.
"""

import os
import sys
import pytest
from datetime import date

# Permet d'importer les modules situés dans backend/database et backend/scoring
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "backend", "database"))
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "backend", "scoring"))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Classe, Eleve, Matiere, Note, Absence, Alerte, Recommandation
from scoring import evaluate_student, compute_score

# Fixture : base de données de test, recréée à chaque test

@pytest.fixture
def session():
    """Crée une base SQLite en mémoire, isolée, détruite après chaque test."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    TestSession = sessionmaker(bind=engine)
    s = TestSession()
    yield s
    s.close()

@pytest.fixture
def eleve_en_difficulte(session):
    """Crée un élève avec de mauvaises notes et beaucoup d'absences."""
    classe = Classe(nom="6e A", niveau="6e", annee_scolaire="2025-2026")
    session.add(classe)
    session.commit()

    maths = Matiere(nom="Mathématiques")
    francais = Matiere(nom="Français")
    session.add_all([maths, francais])
    session.commit()

    eleve = Eleve(nom="Rakoto", prenom="Faniry", classe_id=classe.id)
    session.add(eleve)
    session.commit()

    session.add_all([
        Note(eleve_id=eleve.id, matiere_id=maths.id, valeur=6, date_evaluation=date(2026, 6, 1), trimestre=3),
        Note(eleve_id=eleve.id, matiere_id=francais.id, valeur=7, date_evaluation=date(2026, 6, 1), trimestre=3),
    ])
    for i in range(6):
        session.add(Absence(eleve_id=eleve.id, date_absence=date(2026, 6, i + 1), justifiee=0))
    session.commit()

    return eleve

@pytest.fixture
def eleve_stable(session):
    """Crée un élève avec de bonnes notes et peu d'absences."""
    classe = Classe(nom="5e B", niveau="5e", annee_scolaire="2025-2026")
    session.add(classe)
    session.commit()

    maths = Matiere(nom="Mathématiques")
    session.add(maths)
    session.commit()

    eleve = Eleve(nom="Andria", prenom="Voahangy", classe_id=classe.id)
    session.add(eleve)
    session.commit()

    session.add(Note(eleve_id=eleve.id, matiere_id=maths.id, valeur=16, date_evaluation=date(2026, 6, 1), trimestre=3))
    session.commit()

    return eleve

# TESTS

def test_creation_eleve_en_base(session):
    """Un élève créé doit être retrouvable en base avec les bonnes infos."""
    classe = Classe(nom="4e C", niveau="4e", annee_scolaire="2025-2026")
    session.add(classe)
    session.commit()

    eleve = Eleve(nom="Rasoa", prenom="Nirina", classe_id=classe.id)
    session.add(eleve)
    session.commit()

    resultat = session.query(Eleve).filter_by(prenom="Nirina").first()
    assert resultat is not None
    assert resultat.nom == "Rasoa"
    assert resultat.classe.nom == "4e C"


def test_calcul_moyenne_depuis_la_base(eleve_en_difficulte):
    """La moyenne calculée par le modèle doit correspondre aux notes insérées."""
    eleve = eleve_en_difficulte
    # notes : 6 et 7 -> moyenne attendue 6.5
    assert eleve.moyenne_generale == 6.5


def test_scoring_sur_eleve_en_difficulte(eleve_en_difficulte):
    """
    Test d'intégration clé : les données de la base (notes + absences)
    doivent produire, une fois passées dans le moteur de scoring,
    un niveau de risque élevé.
    """
    eleve = eleve_en_difficulte
    grades_by_subject = {n.matiere.nom: n.valeur for n in eleve.notes}

    resultat = evaluate_student(grades_by_subject, eleve.nombre_absences)

    assert resultat["moyenne"] == 6.5
    assert resultat["niveau_risque"] == "risque_eleve"
    assert resultat["motif"] is not None
    assert len(resultat["recommandations"]) > 0


def test_scoring_sur_eleve_stable(eleve_stable):
    """Un élève avec de bonnes notes et peu d'absences doit être 'stable'."""
    eleve = eleve_stable
    grades_by_subject = {n.matiere.nom: n.valeur for n in eleve.notes}

    resultat = evaluate_student(grades_by_subject, eleve.nombre_absences)

    assert resultat["niveau_risque"] == "stable"
    assert resultat["motif"] is None


def test_alerte_peut_etre_enregistree_en_base(session, eleve_en_difficulte):
    """
    Vérifie que le résultat du moteur de scoring peut être stocké
    dans la table 'alertes' sans erreur (test bout-en-bout complet).
    """
    eleve = eleve_en_difficulte
    grades_by_subject = {n.matiere.nom: n.valeur for n in eleve.notes}
    resultat = evaluate_student(grades_by_subject, eleve.nombre_absences)

    alerte = Alerte(
        eleve_id=eleve.id,
        niveau_risque=resultat["niveau_risque"],
        score=resultat["score"],
        motif=resultat["motif"],
    )
    session.add(alerte)
    session.commit()

    alerte_en_base = session.query(Alerte).filter_by(eleve_id=eleve.id).first()
    assert alerte_en_base is not None
    assert alerte_en_base.niveau_risque == "risque_eleve"


def test_recommandations_peuvent_etre_enregistrees_en_base(session, eleve_en_difficulte):
    """Les recommandations générées doivent pouvoir être liées à l'élève en base."""
    eleve = eleve_en_difficulte
    grades_by_subject = {n.matiere.nom: n.valeur for n in eleve.notes}
    resultat = evaluate_student(grades_by_subject, eleve.nombre_absences)

    for texte in resultat["recommandations"]:
        session.add(Recommandation(eleve_id=eleve.id, texte=texte))
    session.commit()

    recos = session.query(Recommandation).filter_by(eleve_id=eleve.id).all()
    assert len(recos) == len(resultat["recommandations"])


def test_seuils_de_score_coherents():
    """Test rapide des seuils bruts du moteur de scoring (sans passer par la base)."""
    _, niveau_bon = compute_score(moyenne=15, nb_absences=0)
    _, niveau_moyen = compute_score(moyenne=9, nb_absences=3)
    _, niveau_mauvais = compute_score(moyenne=6, nb_absences=10)

    assert niveau_bon == "stable"
    assert niveau_moyen == "a_surveiller"
    assert niveau_mauvais == "risque_eleve"
