import os
import requests
import pandas as pd

from io import BytesIO
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


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


class APIClient:
    """Client pour récupérer les données Vélib et météo."""

    VELIB_URL = (
        "https://opendata.paris.fr/api/explore/v2.1/"
        "catalog/datasets/velib-disponibilite-en-temps-reel/"
        "exports/csv?use_labels=true"
    )

    METEO_URL = (
        "https://public-api.meteofrance.fr/public/DPObs/v2/"
        "station/infrahoraire-6m?id_station="
    )

    STATIONS_METEO_URL = (
        "https://public-api.meteofrance.fr/public/DPObs/v2/liste-stations"
    )

    CITY_DEPARTEMENT_CODE = "75"

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

    def save_city_stations_id(self, stations_id: pd.Series) -> None:
            """Sauvegarde les identifiants des stations météo dans un fichier CSV."""
    
            backup_path = self.get_backup_path("stations_id")
    
            stations_id.to_csv(
                backup_path,
                index=False,
                header=True,
                encoding="utf-8-sig",
            )

    def load_city_stations_id(self) -> pd.Series:
        """Charge les identifiants des stations météo depuis une sauvegarde."""

        backup_path = self.get_backup_path("stations_id")

        # Récupère et sauvegarde les identifiants si la sauvegarde n'existe pas
        if not backup_path.exists():
            self.get_city_stations_id()

        return pd.read_csv(
            backup_path,
            encoding="utf-8-sig",
        )["Id_station"]

    def city_stations_id_exists(self) -> bool:
        """Vérifie si une sauvegarde des identifiants des stations météo existe."""

        return self.get_backup_path("stations_id").exists()


    # --------------------------------------------------
    # Récupération des données
    # --------------------------------------------------

    def get_city_stations_id(self):
        response = self.session.get(
            self.STATIONS_METEO_URL,
            headers={
                "accept": "*/*",
                "apikey": self.token,
            },
            timeout=self.timeout,
        )

        stations_df = pd.read_csv(
            BytesIO(response.content),
            encoding="utf-8-sig",
            sep=None,
            engine="python",
            dtype={"Id_station": str},
        )
        
        id_stations_df = stations_df[
            stations_df["Id_station"].str.startswith(
                self.CITY_DEPARTEMENT_CODE,
                na=False,
            )
        ]["Id_station"]

        self.save_city_stations_id(id_stations_df)

        return id_stations_df

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

    def get_meteo_dataset(self):
        if not self.token:
            raise ValueError(
                "TOKEN absent du fichier .env ou non chargé."
            )

        # Récupération des identifiants des stations météo du département
        if self.city_stations_id_exists():
            list_stations_id = pd.read_csv(
                self.get_backup_path("stations_id"),
                encoding="utf-8-sig",
            )["Id_station"]
        else:
            list_stations_id = self.get_city_stations_id()

        # Liste qui récupérera les DataFrames de chaque station
        dataframes = []

        for station in list_stations_id:

            url = f"{self.METEO_URL}{station}&format=json"

            response = self.session.get(
                url,
                headers={
                    "accept": "*/*",
                    "apikey": self.token,
                },
                timeout=self.timeout,
            )

            response.raise_for_status()
            data = pd.json_normalize(response.json())

            dataframes.append(data)

        if dataframes:
            return pd.concat(dataframes, ignore_index=True)

        return pd.DataFrame()


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

        # Sauvegarde automatique
        self.save_dataset(
            dataset_name,
            dataset,
        )

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