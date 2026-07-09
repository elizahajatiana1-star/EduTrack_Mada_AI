"""
models.py — EduTrack Madagascar AI
------------------------------------
Ce fichier définit les tables de la base de données sous forme de classes
Python, grâce à SQLAlchemy (ORM). Chaque classe correspond exactement à
une table décrite dans schema.sql.

Utilisation typique par les autres membres de l'équipe :

    from models import Session, Eleve, Note

    session = Session()
    eleves = session.query(Eleve).all()
    for e in eleves:
        print(e.prenom, e.nom, e.notes)
"""

from sqlalchemy import (
    create_engine, Column, Integer, String, Float, Date, DateTime,
    ForeignKey, CheckConstraint, Text, func
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from datetime import datetime

# ------------------------------------------------------------------
# Connexion à la base de données
# ------------------------------------------------------------------
DATABASE_URL = "sqlite:///edutrack.db"

engine = create_engine(DATABASE_URL, echo=False)
Session = sessionmaker(bind=engine)
Base = declarative_base()


# ------------------------------------------------------------------
# CLASSES (classes scolaires : 6e A, 5e B, etc.)
# ------------------------------------------------------------------
class Classe(Base):
    __tablename__ = "classes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nom = Column(String, nullable=False, unique=True)          # ex : "6e A"
    niveau = Column(String, nullable=False)                     # ex : "6e"
    annee_scolaire = Column(String, nullable=False)             # ex : "2025-2026"

    eleves = relationship("Eleve", back_populates="classe")

    def __repr__(self):
        return f"<Classe {self.nom}>"


# ------------------------------------------------------------------
# MATIERES
# ------------------------------------------------------------------
class Matiere(Base):
    __tablename__ = "matieres"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nom = Column(String, nullable=False, unique=True)           # ex : "Mathématiques"

    def __repr__(self):
        return f"<Matiere {self.nom}>"


# ------------------------------------------------------------------
# ELEVES
# ------------------------------------------------------------------
class Eleve(Base):
    __tablename__ = "eleves"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nom = Column(String, nullable=False)
    prenom = Column(String, nullable=False)
    date_naissance = Column(Date)
    classe_id = Column(Integer, ForeignKey("classes.id"), nullable=False)
    contact_parent = Column(String)
    date_creation = Column(DateTime, server_default=func.now()) # Corrigé : unique et utilise le serveur SQL

    classe = relationship("Classe", back_populates="eleves")
    notes = relationship("Note", back_populates="eleve", cascade="all, delete-orphan")
    absences = relationship("Absence", back_populates="eleve", cascade="all, delete-orphan")
    alertes = relationship("Alerte", back_populates="eleve", cascade="all, delete-orphan")
    recommandations = relationship("Recommandation", back_populates="eleve", cascade="all, delete-orphan")
    historique = relationship("HistoriqueScolaire", back_populates="eleve", cascade="all, delete-orphan") # Corrigé : remis à l'intérieur de la classe

    @property
    def moyenne_generale(self):
        """Calcule la moyenne générale à partir des notes en mémoire."""
        if not self.notes:
            return 0
        return round(sum(n.valeur for n in self.notes) / len(self.notes), 2)

    @property
    def nombre_absences(self):
        return len(self.absences)

    def __repr__(self):
        return f"<Eleve {self.prenom} {self.nom}>"


# ------------------------------------------------------------------
# UTILISATEURS (enseignant / parent / admin)
# ------------------------------------------------------------------
class Utilisateur(Base):
    __tablename__ = "utilisateurs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nom_complet = Column(String, unique=True, nullable=False)
    email= Column(String , unique=True , nullable=False)
    mot_de_passe = Column(String, nullable=False)
    role = Column(String, nullable=False)
    
    eleve_id = Column(Integer, ForeignKey("eleve.id"), nullable=True)
    classe = relationship("Classe")

    def __repr__(self):
        return f"<Utilisateur {self.nom_utilisateur} - {self.role}>"


# ------------------------------------------------------------------
# NOTES
# ------------------------------------------------------------------
class Note(Base):
    __tablename__ = "notes"
    __table_args__ = (
        CheckConstraint("valeur >= 0 AND valeur <= 20", name="check_valeur_note"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    eleve_id = Column(Integer, ForeignKey("eleves.id"), nullable=False)
    matiere_id = Column(Integer, ForeignKey("matieres.id"), nullable=False)
    valeur = Column(Float, nullable=False)
    date_evaluation = Column(Date, nullable=False)
    trimestre = Column(Integer)
    commentaire = Column(Text)

    eleve = relationship("Eleve", back_populates="notes")
    matiere = relationship("Matiere")

    def __repr__(self):
        return f"<Note {self.valeur}/20>"


# ------------------------------------------------------------------
# ABSENCES
# ------------------------------------------------------------------
class Absence(Base):
    __tablename__ = "absences"

    id = Column(Integer, primary_key=True, autoincrement=True)
    eleve_id = Column(Integer, ForeignKey("eleves.id"), nullable=False)
    date_absence = Column(Date, nullable=False)
    justifiee = Column(Integer, default=0)   # 0 = non, 1 = oui
    motif = Column(Text)

    eleve = relationship("Eleve", back_populates="absences")

    def __repr__(self):
        return f"<Absence {self.date_absence}>"


# ------------------------------------------------------------------
# ALERTES (générées par le moteur de scoring)
# ------------------------------------------------------------------
class Alerte(Base):
    __tablename__ = "alertes"
    __table_args__ = (
        CheckConstraint(
            "niveau_risque IN ('stable','a_surveiller','risque_eleve')",
            name="check_niveau_risque"
        ),
        CheckConstraint("statut IN ('ouverte','traitee')", name="check_statut_alerte"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    eleve_id = Column(Integer, ForeignKey("eleves.id"), nullable=False)
    date_creation = Column(DateTime, server_default=func.now()) # Mis à jour avec server_default
    niveau_risque = Column(String, nullable=False)
    score = Column(Integer, nullable=False)
    motif = Column(Text, nullable=False)
    statut = Column(String, default="ouverte")

    eleve = relationship("Eleve", back_populates="alertes")

    def __repr__(self):
        return f"<Alerte {self.niveau_risque} - {self.eleve_id}>"


# ------------------------------------------------------------------
# RECOMMANDATIONS
# ------------------------------------------------------------------
class Recommandation(Base):
    __tablename__ = "recommandations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    eleve_id = Column(Integer, ForeignKey("eleves.id"), nullable=False)
    matiere_id = Column(Integer, ForeignKey("matieres.id"), nullable=True)
    texte = Column(Text, nullable=False)
    date_creation = Column(DateTime, server_default=func.now()) # Corrigé : unique et utilise le serveur SQL

    eleve = relationship("Eleve", back_populates="recommandations")
    matiere = relationship("Matiere")

    def __repr__(self):
        return f"<Recommandation eleve={self.eleve_id}>"


# ------------------------------------------------------------------
# HISTORIQUE SCOLAIRE
# ------------------------------------------------------------------
class HistoriqueScolaire(Base):
    __tablename__ = "historique_scolaire"

    id = Column(Integer, primary_key=True, autoincrement=True)
    eleve_id = Column(Integer, ForeignKey("eleves.id"), nullable=False)
    annee_scolaire = Column(String, nullable=False)
    trimestre = Column(Integer)
    classe = Column(String, nullable=False)
    moyenne_generale = Column(Float)
    total_absences = Column(Integer, default=0)

    eleve = relationship("Eleve", back_populates="historique")

    def __repr__(self):
        return f"<Historique {self.eleve_id} - T{self.trimestre}>"


# ------------------------------------------------------------------
# Création des tables si elles n'existent pas encore
# ------------------------------------------------------------------
def init_db():
    """À appeler une seule fois pour créer les tables dans edutrack.db"""
    Base.metadata.create_all(engine)
    print("Tables créées avec succès.")


if __name__ == "__main__":
    init_db()