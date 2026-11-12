# Importation des bibliothèques nécessaires
import pandas as pd

from classes.conversion import convertir_station_velib, convertir_meteo

# Chargement du DataFrame
df = pd.read_csv("../../api/data/backup/velib.csv")
df = pd.read_csv("../../api/data/backup/meteo.csv")

# Conversion des lignes du dataframe en objets
stations = convertir_station_velib(df)
meteo_observations = convertir_meteo(df)

# Affichage
print("Liste des stations Velib :\n")
for station in stations:
    print(station)

print("\n--------------------\n")

print("Liste des observations météo :\n")
for observation in meteo_observations:
    print(observation)