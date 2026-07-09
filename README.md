# ProjetFinAnn-
projet fin d'année

# EduTrack Madagascar AI
> **Plateforme intelligente de suivi scolaire** *Sujet 8*

## 1. Présentation du projet
### 1.1 Contexte
À Madagascar, de nombreux établissements scolaires suivent encore les notes, les absences et la progression des élèves de manière manuelle ou dispersée (cahiers, fichiers isolés). Cette gestion fragmentée rend difficile la détection précoce des élèves en difficulté et complique la communication entre les enseignants et les parents.

**EduTrack Madagascar AI** centralise ces informations et y intègre un moteur d'analyse automatisé capable de repérer les élèves à risque d'échec scolaire pour permettre une intervention pédagogique rapide.

### 1.2 Objectifs
* **Centraliser** les données scolaires (notes, absences, progression) dans une base de données unique.
* **Faciliter** le suivi partagé entre les enseignants et les familles.
* **Détecter** automatiquement les élèves en difficulté grâce à un système de scoring.
* **Proposer** des recommandations pédagogiques adaptées à chaque profil.
* **Réduire** le risque de décrochage scolaire grâce à un système d'alerte précoce.

## 2. Périmètre & Fonctionnalités
### 2.1 Acteurs du système
**Enseignant** Saisit les notes et absences, consulte le tableau de bord et les alertes de sa classe, valide les recommandations.
**Parent** Consulte le suivi scolaire de son enfant (notes, absences, recommandations) en **lecture seule**.
**Administrateur** Gère les comptes, les classes, les matières, et supervise l'ensemble des données.
**Module d'analyse (IA)** Calcule automatiquement les scores de risque et génère les recommandations.

### 2.2 Fonctionnalités principales
* **Gestion des élèves :** Profil complet (nom, classe, contact parent), création, modification et suppression.
* **Suivi académique :** Enregistrement des notes (par matière et date) et des absences (justifiées ou non).
* **Calculateur automatique :** Gestion automatique des moyennes par matière et de la moyenne générale.
* **Tableau de bord :** Vue synthétique pour les enseignants (nombre d'élèves, répartition par niveau de risque, liste de priorité).
* **Module d'alerte et de recommandation :** Génération d'actions concrètes (révisions, alertes, rendez-vous famille) basées sur l'absentéisme et les notes faibles.
* **Historique scolaire :** Suivi de l'évolution des performances au fil du temps pour observer les tendances de l'élève.

## 3. Spécifications Techniques

### 4.1 Architecture générale
L'application repose sur une architecture client-serveur en trois couches :
1. **Couche Présentation :** Interface Web simple (ou interface de bureau via **Tkinter** pour les zones à connectivité limitée).
2. **Couche Métier :** API REST développée en **Python** (Flask ou FastAPI) embarquant le moteur de scoring.
3. **Couche Données :** Base de données relationnelle (**SQLite** pour le développement, compatible **PostgreSQL** pour la production).

### 4.2 Technologies utilisées
* **Langage principal :** Python
* **Framework API :** Flask (ou FastAPI)
* **Traitement de données :** Pandas
* **Base de données :** SQLite / PostgreSQL
* **Échange de données :** REST API (Format JSON)
* **Moteur d'analyse :** Algorithme de scoring basé sur des règles (évolutif vers un modèle Machine Learning léger type Régression Logistique).

### 4.3 Structure de la Base de Données
Le schéma relationnel (`schema.sql`) comprend les tables suivantes :
* `eleves` : Informations personnelles de l'élève.
* `classes` : Liste des classes de l'établissement.
* `matieres` : Liste des matières enseignées.
* `notes` : Évaluations chiffrées liées à une matière et une date.
* `absences` : Registre des absences et assiduité.
* `utilisateurs` : Comptes d'accès (Enseignants, Parents, Admin).
* `alertes` : Alertes actives de décrochage générées par le système.
* `recommandations` : Actions pédagogiques suggérées.

## 4. Aperçu de l'API REST
| Méthode | Endpoint | Description |
| --- | --- | --- |
| `GET` | `/api/eleves` | Liste tous les élèves |
| `POST` | `/api/eleves` | Créer une nouvelle fiche élève |
| `PUT` | `/api/eleves/{id}` | Modifier les informations d'un élève |
| `DELETE` | `/api/eleves/{id}` | Supprimer un élève |
| `POST` | `/api/notes` | Ajouter une note |
| `POST` | `/api/absences` | Ajouter une absence |
| `GET` | `/api/eleves/{id}/score` | Obtenir le score de risque d'un élève |
| `GET` | `/api/alertes` | Liste des alertes de décrochage actives |
| `GET` | `/api/eleves/{id}/recommandations` | Obtenir les recommandations personnalisées |

## 5. Algorithme de Scoring (Moteur d'analyse)
Le système calcule un score de risque cumulatif sur **6 points maximum** basé sur deux critères transparents et explicables :

### 1. Critère de la Moyenne Générale (sur 20)
* Moyenne $< 8 \rightarrow$ **3 points**
* Moyenne entre 8 et 10 $\rightarrow$ **2 points**
* Moyenne entre 10 et 12 $\rightarrow$ **1 point**
* Moyenne $\ge 12 \rightarrow$ **0 point**

### 2. Critère d'Absentéisme
* 8 absences ou plus $\rightarrow$ **3 points**
* Entre 4 et 7 absences $\rightarrow$ **2 points**
* Entre 2 et 3 absences $\rightarrow$ **1 point**
* Moins de 2 absences $\rightarrow$ **0 point**

### Niveau de risque final
| Score Total | Niveau de risque | Action Système |
| --- | --- | --- |
| **4 points ou plus** | 🔴 **Risque élevé** | Alerte immédiate et plan de soutien prioritaire |
| **2 à 3 points** | 🟡 **À surveiller** | Suivi renforcé par l'enseignant |
| **0 à 1 point** | 🟢 **Stable** | Situation normale |

## 6. Contraintes non fonctionnelles
* **Sécurité & Confidentialité :** Authentification obligatoire. Restriction stricte des accès selon le rôle (un parent possède un accès unique et exclusif en lecture seule aux données de son propre enfant).
* **Simplicité d'usage :** Interface ergonomique, pensée pour des utilisateurs peu familiarisés avec les outils informatiques.
* **Performance :** Temps de réponse de l'API inférieur à 1 seconde pour l'ensemble des requêtes courantes.
* **Portabilité & Mode Hors-ligne :** Capacité à fonctionner localement sur un ordinateur (SQLite + Tkinter) pour pallier les problèmes de connectivité internet dans certaines régions.

## 7. Organisation du Projet & Livrables
### 7.1 Répartition de l'équipe (5 personnes)
1. **Modélisation & BDD :** Schéma SQL, création des tables, données de test (`schema.sql`, `models.py`).
2. **Backend & API :** Développement des routes REST, validation et sérialisation JSON (`app.py`).
3. **Moteur de scoring :** Algorithme de risque, recommandations et tests unitaires (`scoring.py`).
4. **Interface Utilisateur :** UI Web ou Tkinter connectée à l'API.
5. **Intégration & QA :** Tests globaux, documentation générale et gestion du dépôt.