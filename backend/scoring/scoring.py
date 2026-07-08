"""
Moteur de Scoring - EduTrack Madagascar AI
Conforme à la section 5 du cahier des charges.
"""

def calculer_points_moyenne(moyenne):
    """Calcule les points selon la moyenne (Section 5.1)."""
    if moyenne < 8: return 3
    if 8 <= moyenne < 10: return 2
    if 10 <= moyenne < 12: return 1
    return 0

def calculer_points_absences(nb_absences):
    """Calcule les points selon les absences (Section 5.2)."""
    if nb_absences >= 8: return 3
    if 4 <= nb_absences <= 7: return 2
    if 2 <= nb_absences <= 3: return 1
    return 0

def evaluer_niveau_risque(moyenne, nb_absences):
    """Calcule le risque total (Section 5.3)."""
    pts_m = calculer_points_moyenne(moyenne)
    pts_a = calculer_points_absences(nb_absences)
    total = pts_m + pts_a
    
    if total >= 4: return "Risque élevé"
    if 2 <= total <= 3: return "À surveiller"
    return "Stable"

def generer_recommandations(niveau_risque):
    """Génère les recommandations basées sur le risque."""
    if niveau_risque == "Risque élevé":
        return ["Urgent : Entretien avec les parents", "Soutien scolaire intensif"]
    elif niveau_risque == "À surveiller":
        return ["Renforcer le suivi pédagogique", "Discuter avec l'élève"]
    return ["Aucune action urgente"]


if __name__ == "__main__":
   
    test_moyenne = 7
    test_absences = 9
    
    risque = evaluer_niveau_risque(test_moyenne, test_absences)
    recos = generer_recommandations(risque)
    
    print(f"--- Rapport de test ---")
    print(f"Moyenne: {test_moyenne}, Absences: {test_absences}")
    print(f"Niveau de risque: {risque}")
    print(f"Recommandations: {recos}")
    
 