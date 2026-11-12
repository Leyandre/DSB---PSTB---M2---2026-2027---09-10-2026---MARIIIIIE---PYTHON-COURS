# Importation des bibliothèques nécessaires
import pandas as pd

from classes.StationVelib import StationVelib
from classes.Meteo import Meteo

# Fonctions de conversion
def convertir_station_velib(dataframe: pd.DataFrame) -> list[StationVelib]:
    list_stations_velib = []

    for _, ligne in dataframe.iterrows():
        station = StationVelib(
            identifiant_station = int(ligne["id_station"]),
            nom_station = ligne["nom_station"],
            en_fonctionnement = ligne["en_fonctionnement"],
            capacite = int(ligne["capacite"]),
            nb_bornettes_libres = int(ligne["nb_bornettes_libres"]),
            nb_total_velo_dispo = int(ligne["nb_total_velo_dispo"]),
            nb_velo_meca = int(ligne["nb_velo_meca"]),
            nb_velo_elec = int(ligne["nb_velo_elec"]),
            borne_paiement_dispo = ligne["borne_paiement_dispo"],
            retour_velib_possible = ligne["retour_velib_possible"],
            actualisation_donnee = ligne["actualisation_donnee"],
            coordonnees = (float(ligne["latitude"]), float(ligne["longitude"])),
            commune = ligne["commune"],
            code_insee = ligne["code_insee"],
            horaire_ouverture = ligne["horaire_ouverture"]
        )

        list_stations_velib.append(station)

    return list_stations_velib


def convertir_meteo(dataframe: pd.DataFrame) -> list[Meteo]:
    list_meteo = []

    for _, ligne in dataframe.iterrows():
        observation = Meteo(
            identifiant_station = int(ligne["id_station"]),
            latitude = float(ligne["latitude"]),
            longitude = float(ligne["longitude"]),
            date_observation = ligne["date_observation"],
            temperature_celsius = float(ligne["temperature_celsius"]),
            point_rosee_celsius = float(ligne["point_rosee_celsius"]),
            humidite_relative_pct = float(ligne["humidite_relative_pct"]),
            direction_vent_deg = float(ligne["direction_vent_deg"]),
            vitesse_vent_ms = float(ligne["vitesse_vent_ms"]),
            visibilite_m = float(ligne["visibilite_m"]),
            pression_station_pa = float(ligne["pression_station_pa"]),
            pression_mer_pa = float(ligne["pression_mer_pa"])
        )

        list_meteo.append(observation)

    return list_meteo