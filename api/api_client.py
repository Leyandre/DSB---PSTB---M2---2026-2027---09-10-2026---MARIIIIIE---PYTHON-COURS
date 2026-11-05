import os
import requests
import pandas as pd

from io import BytesIO
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

#Petite fonction pour récupérer les données Vélib et météo via les API publiques.
def fetch_dataset(dataset: str) -> pd.DataFrame:
    """
    Récupère les données d'un jeu de données Vélib ou météo
    et les retourne sous forme de DataFrame pandas.

    La fonction instancie un client APIClient dans un gestionnaire
    de contexte afin de garantir la fermeture de la session HTTP
    après la récupération des données.

    Args:
        dataset (str): Nom du jeu de données à récupérer.
            Valeurs acceptées : "velib" ou "meteo".

    Returns:
        pd.DataFrame: Données récupérées depuis l'API sélectionnée.
            Pour Vélib, les données de disponibilité en temps réel.
            Pour la météo, les observations des stations du département
            75, regroupées dans un seul DataFrame.

    Raises:
        ValueError: Si le nom du jeu de données est inconnu ou si le
            token Météo-France est absent du fichier .env.
        requests.exceptions.RequestException: En cas d'erreur HTTP
            ou de problème lors de la requête réseau.

    Prérequis :
        - Les bibliothèques requests, pandas et python-dotenv installées.
        - Un fichier .env contenant la variable TOKEN pour accéder
          à l'API Météo-France.
        - Une connexion Internet pour interroger les API.
    """
    with APIClient() as client:
        # Récupération des données
        return client.get_dataset(dataset)


#Petite classe pour récupérer les données Vélib et météo via les API publiques.
class APIClient:
    """Client pour récupérer les données Vélib et météo."""

    VELIB_URL = (
        "https://opendata.paris.fr/api/explore/v2.1/"
        "catalog/datasets/velib-disponibilite-en-temps-reel/"
        "exports/csv?use_labels=true"
    )

    METEO_URL = (
        "https://public-api.meteofrance.fr/public/DPPaquetObs/v2/paquet/horaire"
    )

    STATIONS_METEO_URL = (
        "https://public-api.meteofrance.fr/public/DPObs/v2/liste-stations"
    )

    CITY_DEPARTEMENT_CODE = "75"

    # Correspondance entre les champs Météo-France et les noms compréhensibles
    COLONNES_METEO = {
        "geo_id_insee": "identifiant_station",
        "lat": "latitude",
        "lon": "longitude",
        "validity_time": "date_observation",
        "t": "temperature_kelvin",
        "td": "point_rosee_kelvin",
        "u": "humidite_relative_pct",
        "dd": "direction_vent_deg",
        "ff": "vitesse_vent_ms",
        "vv": "visibilite_m",
        "pres": "pression_station_pa",
        "pmer": "pression_mer_pa",
    }

    def __init__(
        self,
        timeout: int = 30,
        backup_dir: str = "data/backup",
    ):
        self.timeout = timeout
        self.session = requests.Session()
        self.token = os.getenv("TOKEN")

        # Dossier de sauvegarde
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    # --------------------------------------------------
    # Gestion des sauvegardes
    # --------------------------------------------------

    def get_backup_path(self, dataset_name: str) -> Path:
        """Retourne le chemin du fichier de sauvegarde."""

        return self.backup_dir / f"{dataset_name}.csv"

    def save_dataset(
        self,
        dataset_name: str,
        dataset: pd.DataFrame,
    ) -> None:
        """Sauvegarde un DataFrame dans un fichier CSV."""

        backup_path = self.get_backup_path(dataset_name)

        dataset.to_csv(
            backup_path,
            index=False,
            encoding="utf-8-sig",
        )

    def load_dataset(
        self,
        dataset_name: str,
    ) -> pd.DataFrame:
        """Charge un DataFrame depuis une sauvegarde."""

        backup_path = self.get_backup_path(dataset_name)

        if not backup_path.exists():
            raise FileNotFoundError(
                f"Aucune sauvegarde trouvée pour {dataset_name}."
            )

        return pd.read_csv(
            backup_path,
            encoding="utf-8-sig",
        )

    def dataset_exists(self, dataset_name: str) -> bool:
        """Vérifie si une sauvegarde existe."""

        return self.get_backup_path(dataset_name).exists()


    # --------------------------------------------------
    # Récupération des données
    # --------------------------------------------------

    def get_velib_dataset(self):
        response = self.session.get(
            self.VELIB_URL,
            timeout=self.timeout,
        )

        response.raise_for_status()

        return pd.read_csv(
            BytesIO(response.content),
            encoding="utf-8-sig",
            sep=None,
            engine="python",
        )

    def get_meteo_dataset(self) -> pd.DataFrame:
        """
        Récupère les observations horaires des stations
        météorologiques d'un département sur 24h.
        """

        if not self.token:
            raise ValueError(
                "TOKEN absent du fichier .env ou non chargé."
            )

        headers = {
            "accept": "*/*",
            "apikey": self.token
        }
        response = requests.get(
            self.METEO_URL,
            params={"id-departement": self.CITY_DEPARTEMENT_CODE, "format": "json"},
            headers=headers,
            timeout=self.timeout
        )

        if response.status_code != 200:
            print("Code HTTP :", response.status_code)
            print("Réponse :", response.text[:1000])

        response.raise_for_status()

        data = response.json()

        if not data:
            return pd.DataFrame()

        return pd.json_normalize(data)

    def keep_only_relevant_columns_and_change_their_names(self, dataset: pd.DataFrame) -> pd.DataFrame:
        """
        Conserve uniquement les colonnes pertinentes pour l'analyse.
        """

        relevant_columns = [
            "geo_id_insee",
            "lat",
            "lon",
            "validity_time",
            "t",
            "td",
            "u",
            "dd",
            "ff",
            "vv",
            "pres",
            "pmer",
        ]

        dataset = dataset[relevant_columns]

        dataset = dataset.rename(columns=self.COLONNES_METEO)

        return dataset

    def change_temperature_unit(self, dataset: pd.DataFrame) -> pd.DataFrame:
        """
        Convertit les colonnes de température de Kelvin à Celsius.
        """

        temperature_columns = ["t", "td", "tx", "tn"]

        for column in temperature_columns:
            if column in dataset.columns:
                dataset[column] = (dataset[column] - 273.15).round(2)

        return dataset


    # --------------------------------------------------
    # Méthode principale
    # --------------------------------------------------

    def get_dataset(
        self,
        dataset_name: str,
        use_cache: bool = True,
    ) -> pd.DataFrame:
        """
        Récupère un dataset.

        Si use_cache=True :
            Charge la sauvegarde si elle existe.

        Si use_cache=False :
            Récupère directement les données via l'API.

        Les données récupérées sont sauvegardées automatiquement.
        """

        # Vérification du nom du dataset
        if dataset_name not in ("velib", "meteo"):
            raise ValueError(
                "Dataset inconnu. Choisissez 'velib' ou 'meteo'."
            )

        # Vérification de la sauvegarde
        if use_cache and self.dataset_exists(dataset_name):

            return self.load_dataset(dataset_name)

        # Récupération via API
        if dataset_name == "velib":
            dataset = self.get_velib_dataset()

        elif dataset_name == "meteo":
            dataset = self.get_meteo_dataset()
            dataset = self.change_temperature_unit(dataset)
            dataset = self.keep_only_relevant_columns_and_change_their_names(dataset)

        # Sauvegarde automatique
        self.save_dataset(dataset_name,dataset)

        return dataset


    # --------------------------------------------------
    # Fermeture de la session
    # --------------------------------------------------

    def close(self) -> None:
        self.session.close()

    def __enter__(self):
        return self

    def __exit__(
        self,
        exc_type,
        exc_value,
        traceback,
    ):
        self.close()