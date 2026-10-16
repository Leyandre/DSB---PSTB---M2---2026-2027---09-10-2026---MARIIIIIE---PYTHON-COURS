from datetime import date, datetime

class StationVelib():
    # Constructeur de la classe
    def __init__(self,
                id: int,
                nom: str = None,
                en_fonctionnement: bool = False,
                nb_bornettes_libres: int = None,
                nb_total_velo_dispo: int = None,
                nb_velo_meca: int = None,
                nb_velo_elec: int = None,
                capacite: int = None,
                borne_paiement_dispo: bool = False,
                retour_velib_possible: bool = False,
                actualisation_donnee: datetime = None,
                coordonnees: (float, float) = None,
                commune: str = None,
                code_insee: str = None,
                horaire_ouverture: str = None
                ):

        self.id = id
        self.nom = nom
        self.en_fonctionnement = en_fonctionnement
        self.nb_bornettes_libres = nb_bornettes_libres
        self.nb_total_velo_dispo = nb_total_velo_dispo
        self.nb_velo_meca = nb_velo_meca
        self.nb_velo_elec = nb_velo_elec
        self.capacite = capacite
        self.borne_paiement_dispo = borne_paiement_dispo
        self.retour_velib_possible = retour_velib_possible
        self.actualisation_donnee = actualisation_donnee
        self.coordonnees = coordonnees
        self.commune = commune
        self.code_insee = code_insee
        self.horaire_ouverture = horaire_ouverture

    # Methodes de la classe

    # toString : méthode permettant d'afficher ce string quand on print l'instance de l'objet
    def __str__(self):
        return f"Station {self.nom} située à {self.commune} a été actualisée pour la dernière fois le {self.actualisation_donnee}"