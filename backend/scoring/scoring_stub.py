"""
scoring_stub.py — REMPLACE-MOI par le fichier de la Personne 3 !
------------------------------------------------------------------
Tant que la Personne 3 (Scoring) ne t'a pas livré son vrai
`scoring.py`, ce module te permet de développer et tester tes
routes /api/eleves/{id}/score, /api/alertes et
/api/eleves/{id}/recommandations sans être bloqué.

Quand tu recevras le vrai fichier, il te suffira de :
  1. Copier scoring.py de la Personne 3 dans ce dossier.
  2. Dans app.py, remplacer :
         from scoring_stub import calculer_score, generer_recommandations
     par :
         from scoring import calculer_score, generer_recommandations
  3. Vérifier que les noms de fonctions et les paramètres correspondent
     (à convenir ensemble — c'est aussi un "contrat", comme le JSON).

IMPORTANT : mets-toi d'accord avec la Personne 3 sur la signature
exacte de ces fonctions (quels arguments, quel format de retour),
pour que le remplacement se fasse sans rien casser dans app.py.
"""

from typing import List


def calculer_score(notes: List[float], nb_absences_non_justifiees: int) -> dict:
    """
    Calcule un score de risque simplifié à partir des notes et absences.
    Logique factice, juste pour pouvoir tester la route en attendant P3.

    Retourne un dict : {"score": int, "niveau_risque": str, "motif": str}
    """
    moyenne = sum(notes) / len(notes) if notes else 20  # pas de note = pas de souci pour l'instant
    score = 0
    motifs = []

    if moyenne < 8:
        score += 3
        motifs.append("moyenne générale très basse")
    elif moyenne < 10:
        score += 2
        motifs.append("moyenne générale insuffisante")

    if nb_absences_non_justifiees >= 5:
        score += 3
        motifs.append("nombreuses absences non justifiées")
    elif nb_absences_non_justifiees >= 2:
        score += 1
        motifs.append("quelques absences non justifiées")

    if score >= 4:
        niveau = "risque_eleve"
    elif score >= 2:
        niveau = "a_surveiller"
    else:
        niveau = "stable"

    motif_texte = ", ".join(motifs) if motifs else "aucun signal préoccupant"
    return {"score": score, "niveau_risque": niveau, "motif": motif_texte}


def generer_recommandations(score_result: dict) -> list[str]:
    """
    Génère une liste de conseils pédagogiques simples à partir du score.
    Logique factice — à remplacer par celle de la Personne 3.
    """
    if score_result["niveau_risque"] == "risque_eleve":
        return [
            "Organiser un entretien avec l'élève et les parents",
            "Mettre en place un soutien scolaire ciblé",
        ]
    elif score_result["niveau_risque"] == "a_surveiller":
        return ["Suivre l'évolution des notes sur le prochain trimestre"]
    return ["Aucune action particulière requise"]
