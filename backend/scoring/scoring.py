def calculer_moyenne(liste_notes):
    if not liste_notes:
        return 0
    return round(sum(liste_notes) / len(liste_notes), 2)

def calculer_taux_absenteisme(absences, total_cours):
    if total_cours <= 0:
        return 0
    return round((absences / total_cours) * 100, 2)

def detecter_risque(moyenne, taux_abs):
    score = 0
    if moyenne < 8:
        score += 50
    elif moyenne < 10:
        score += 25
    if taux_abs > 20:
        score += 50
    return min(score, 100)

def generer_recommandations(score, moyenne, taux_abs):
    recos = []
    if score >= 50:
        recos.append("Alerte : Risque élevé.")
    if moyenne < 10:
        recos.append("Soutien nécessaire.")
    if taux_abs > 10:
        recos.append("Assiduité à renforcer.")
    return recos

# --- TEST ---
if __name__ == "__main__":
    notes = [7, 9, 8]
    absences = 5
    total = 20
    
    m = calculer_moyenne(notes)
    t = calculer_taux_absenteisme(absences, total)
    s = detecter_risque(m, t)
    r = generer_recommandations(s, m, t)
    
    print(f"Moyenne : {m}, Score : {s}, Conseils : {r}")