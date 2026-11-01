import os
import requests
import pandas as pd
from io import BytesIO
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

    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.session = requests.Session()
        self.token = os.getenv("TOKEN")

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
        
        id_stations_df = stations_df[stations_df["Id_station"].str.startswith("75", na=False)]["Id_station"]

        return id_stations_df

    def get_velib_dataset(self):
        response = self.session.get(
            self.dataset_url,
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

        list_stations_id = self.get_city_stations_id()

        # Liste qui récupérera les DataFrames de chaque station
        dataframes = []

        for station in list_stations_id:

            url = f"{self.dataset_url}{station}&format=json"

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

    def get_dataset(self, dataset_name: str) -> pd.DataFrame:
        """Récupère les données et les convertit en DataFrame."""

        """Choisit le dataset à récupérer."""
        if dataset_name == "velib":
            self.dataset_url = self.VELIB_URL
            dataset = self.get_velib_dataset()

        elif dataset_name == "meteo":
            self.dataset_url = self.METEO_URL
            dataset = self.get_meteo_dataset()

        else:
            raise ValueError(
                "Dataset inconnu. Choisissez 'velib' ou 'meteo'."
            )

        return dataset

    def close(self) -> None:
        self.session.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()