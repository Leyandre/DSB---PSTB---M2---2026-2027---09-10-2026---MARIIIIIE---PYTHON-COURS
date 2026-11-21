import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

class Cleaning:
    def __init__(self, df: pd.DataFrame, primary_key: str):
        self.df = df
        self.primary_key = primary_key
        self.print_all_info()
        self.missing_values()
        print(self.df.shape)
        self.drop_doublons()
        print(self.df.shape)
        self.outlayers()
        print(self.df.shape)


    def get_df(self):
        return self.df

    def print_all_info(self):
        print("===== DESCRIPTION =====")
        print(self.df.describe().to_string())

        print("===== SHAPE =====")
        print(self.df.shape)
        
        print("===== HEAD =====")
        print(self.df.head().to_string())

        print("===== COLONNES =====")
        print(list(self.df.columns))

        print("===== INFO =====")
        self.df.info()

# etape 3 : identifier les problèmes les valeurs manquantes
    def missing_values(self):
        unkown_values = self.df.isna().sum()
        print("Nombre de valeurs manquantes :",unkown_values)

# etape 3 : identifier les problèmes les doublons
    def drop_doublons(self):

        doublons = self.df[self.primary_key].duplicated().sum()
        print(f"Nombre de doublons : {doublons}")
        if doublons >= 1:
            self.df = self.df.drop_duplicates(subset=[self.primary_key])
        else:
            print("no doublons")

#MAJ quantiles 
    def maj_quantiles(self, col: str):
        self.Q1 = self.df[col].quantile(0.25)
        self.Q3 = self.df[col].quantile(0.75)
        self.IQR = self.Q3 - self.Q1

# etape 4 : valeurs abérrantes 
    def outlayers(self):
        for col in self.df.select_dtypes(include=['float64', 'int64']).columns:
            if col == self.primary_key:
                continue
            else:
                self.maj_quantiles(col)
                lower_bound = self.Q1 - 1.5 * self.IQR
                upper_bound = self.Q3 + 1.5 * self.IQR
                outliers = self.df[(self.df[col] < lower_bound) | (self.df[col] > upper_bound)]
                print(f"Nombre de valeurs aberrantes dans la colonne {col} : {len(outliers)}")

#etape 4 : valeurs aberrantes et boxplot sur une colonne 
    def outlayers_col(self, col: str):

        # Boxplot
        plt.figure(figsize=(8, 4))
        plt.boxplot(self.df[col].dropna())
        plt.title(f"Boxplot de {col}")
        plt.show()

        # Calcul IQR
        self.maj_quantiles(col)

        borne_inf = self.Q1 - 1.5 * self.IQR
        borne_sup = self.Q3 + 1.5 * self.IQR

        outliers = self.df[
            (self.df[col] < borne_inf) |
            (self.df[col] > borne_sup)
        ]

        return outliers

    #supprimer les colonnes inutiles
    def drop_col(self, cols: list):
        for col in cols:
            if col in self.df.columns:
                self.df = self.df.drop(columns=[col])
                print(f"Colonne '{col}' supprimée.")
            else:
                print(f"Colonne '{col}' non trouvée dans le DataFrame.")
        return self.df