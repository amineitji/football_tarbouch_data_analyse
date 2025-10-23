"""
DataCleaner - Classe pour nettoyer et préparer les données FBref
Gère les doublons, les colonnes inutiles, les pourcentages, et les stats composées
"""

import pandas as pd
import numpy as np
import re
from typing import List, Tuple, Optional


class DataCleaner:
    """
    Nettoyeur de données FBref
    Supprime les doublons, stats composées, pourcentages, et prépare les données
    """
    
    def __init__(self, verbose: bool = True):
        """
        Initialise le nettoyeur
        
        Args:
            verbose: Afficher les logs détaillés
        """
        self.verbose = verbose
        self.cleaning_report = {
            'initial_rows': 0,
            'initial_cols': 0,
            'final_rows': 0,
            'final_cols': 0,
            'removed_duplicates': 0,
            'removed_composite': [],
            'removed_percentages': [],
            'removed_empty': []
        }
    
    def _log(self, message: str, level: str = "INFO"):
        """Log si verbose activé"""
        if self.verbose:
            print(f"[{level}] {message}")
    
    def _is_composite_stat(self, stat_name: str) -> bool:
        """
        Détecte si une statistique est composée (somme, différence, ratio)
        
        Exemples de stats composées à supprimer :
        - "Goals + Assists" 
        - "npxG + xAG"
        - "Goals - xG"
        - "Tkl+Int"
        
        Args:
            stat_name: Nom de la statistique
            
        Returns:
            True si c'est une stat composée
        """
        # Patterns de stats composées
        composite_patterns = [
            r'\+',      # Contient un +
            r' - ',     # Contient un - (avec espaces)
            r'\/',      # Contient un /
            r' vs ',    # Contient "vs"
        ]
        
        for pattern in composite_patterns:
            if re.search(pattern, stat_name):
                return True
        
        return False
    
    def _is_percentage_stat(self, stat_name: str) -> bool:
        """
        Détecte si une statistique est un pourcentage
        
        Args:
            stat_name: Nom de la statistique
            
        Returns:
            True si c'est un pourcentage
        """
        percentage_patterns = [
            r'%',
            r'Percentage',
            r'Completion',  # Ex: "Pass Completion %"
        ]
        
        for pattern in percentage_patterns:
            if re.search(pattern, stat_name, re.IGNORECASE):
                return True
        
        return False
    
    def _remove_duplicate_rows(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Supprime les lignes dupliquées (souvent présentes dans les tables FBref)
        
        Args:
            df: DataFrame à nettoyer
            
        Returns:
            DataFrame sans doublons
        """
        initial_len = len(df)
        df_clean = df.drop_duplicates()
        removed = initial_len - len(df_clean)
        
        if removed > 0:
            self._log(f"Suppression de {removed} ligne(s) dupliquée(s)", "INFO")
            self.cleaning_report['removed_duplicates'] = removed
        
        return df_clean
    
    def _remove_empty_rows(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Supprime les lignes vides ou avec uniquement des NaN
        
        Args:
            df: DataFrame à nettoyer
            
        Returns:
            DataFrame sans lignes vides
        """
        initial_len = len(df)
        
        # Supprimer les lignes où toutes les valeurs sont NaN
        df_clean = df.dropna(how='all')
        
        # Supprimer les lignes où la colonne 'Statistic' est vide
        if 'Statistic' in df_clean.columns:
            df_clean = df_clean[df_clean['Statistic'].notna()]
            df_clean = df_clean[df_clean['Statistic'] != '']
        
        removed = initial_len - len(df_clean)
        
        if removed > 0:
            self._log(f"Suppression de {removed} ligne(s) vide(s)", "INFO")
            self.cleaning_report['removed_empty'].append(removed)
        
        return df_clean
    
    def _remove_composite_stats(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Supprime les statistiques composées (sommes, différences, ratios)
        
        Args:
            df: DataFrame à nettoyer
            
        Returns:
            DataFrame sans stats composées
        """
        if 'Statistic' not in df.columns:
            self._log("Colonne 'Statistic' introuvable, skip composite removal", "WARNING")
            return df
        
        initial_len = len(df)
        
        # Filtrer les stats composées
        mask = df['Statistic'].apply(lambda x: not self._is_composite_stat(str(x)))
        df_clean = df[mask]
        
        removed = initial_len - len(df_clean)
        
        if removed > 0:
            removed_stats = df[~mask]['Statistic'].tolist()
            self._log(f"Suppression de {removed} statistique(s) composée(s)", "INFO")
            self.cleaning_report['removed_composite'] = removed_stats
            
            if self.verbose:
                print("  Stats composées supprimées :")
                for stat in removed_stats[:10]:  # Afficher max 10
                    print(f"    - {stat}")
                if len(removed_stats) > 10:
                    print(f"    ... et {len(removed_stats) - 10} autres")
        
        return df_clean
    
    def _remove_percentage_stats(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Supprime les statistiques en pourcentage
        
        Args:
            df: DataFrame à nettoyer
            
        Returns:
            DataFrame sans pourcentages
        """
        if 'Statistic' not in df.columns:
            self._log("Colonne 'Statistic' introuvable, skip percentage removal", "WARNING")
            return df
        
        initial_len = len(df)
        
        # Filtrer les pourcentages
        mask = df['Statistic'].apply(lambda x: not self._is_percentage_stat(str(x)))
        df_clean = df[mask]
        
        removed = initial_len - len(df_clean)
        
        if removed > 0:
            removed_stats = df[~mask]['Statistic'].tolist()
            self._log(f"Suppression de {removed} statistique(s) en pourcentage", "INFO")
            self.cleaning_report['removed_percentages'] = removed_stats
            
            if self.verbose:
                print("  Stats en pourcentage supprimées :")
                for stat in removed_stats[:10]:
                    print(f"    - {stat}")
                if len(removed_stats) > 10:
                    print(f"    ... et {len(removed_stats) - 10} autres")
        
        return df_clean
    
    def _clean_column_names(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Nettoie les noms de colonnes (espaces, caractères spéciaux)
        Gère les MultiIndex en les aplatissant
        
        Args:
            df: DataFrame à nettoyer
            
        Returns:
            DataFrame avec colonnes nettoyées
        """
        # Gérer les MultiIndex (cas des tables FBref)
        if isinstance(df.columns, pd.MultiIndex):
            # Aplatir le MultiIndex en prenant le dernier niveau non-vide
            df.columns = [col[-1] if col[-1] else col[0] for col in df.columns]
        
        # Nettoyer les noms de colonnes
        df.columns = df.columns.astype(str).str.strip()
        df.columns = df.columns.str.replace(r'\s+', '_', regex=True)
        df.columns = df.columns.str.replace(r'[^\w\s]', '', regex=True)
        
        self._log(f"Noms de colonnes nettoyés : {list(df.columns)}", "DEBUG")
        
        return df
    
    def _convert_numeric_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Convertit les colonnes numériques en float
        
        Args:
            df: DataFrame à nettoyer
            
        Returns:
            DataFrame avec types corrects
        """
        # Colonnes à convertir (exclure 'Statistic')
        numeric_cols = [col for col in df.columns if col != 'Statistic']
        
        for col in numeric_cols:
            try:
                # Supprimer les caractères non numériques (sauf . et -)
                df[col] = df[col].astype(str).str.replace(r'[^\d.\-]', '', regex=True)
                df[col] = pd.to_numeric(df[col], errors='coerce')
            except Exception as e:
                self._log(f"Erreur conversion colonne '{col}' : {e}", "WARNING")
        
        self._log("Colonnes converties en numérique", "INFO")
        
        return df
    
    def _remove_header_duplicates(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Supprime les lignes qui sont en fait des headers répétés
        (FBref répète parfois les headers dans le milieu des tables)
        
        Args:
            df: DataFrame à nettoyer
            
        Returns:
            DataFrame sans headers dupliqués
        """
        if 'Statistic' not in df.columns:
            return df
        
        # Supprimer les lignes où 'Statistic' == 'Statistic' (header répété)
        initial_len = len(df)
        df_clean = df[df['Statistic'] != 'Statistic']
        removed = initial_len - len(df_clean)
        
        if removed > 0:
            self._log(f"Suppression de {removed} header(s) dupliqué(s)", "INFO")
        
        return df_clean
    
    def clean(self, df: pd.DataFrame, 
              remove_composites: bool = True,
              remove_percentages: bool = True,
              remove_duplicates: bool = True,
              remove_empty: bool = True) -> pd.DataFrame:
        """
        Applique tous les nettoyages sur le DataFrame
        
        Args:
            df: DataFrame brut à nettoyer
            remove_composites: Supprimer les stats composées (x+y, x-y)
            remove_percentages: Supprimer les pourcentages
            remove_duplicates: Supprimer les doublons
            remove_empty: Supprimer les lignes vides
            
        Returns:
            DataFrame nettoyé
        """
        self._log("="*80)
        self._log("DÉBUT DU NETTOYAGE", "START")
        self._log("="*80)
        
        # Enregistrer les stats initiales
        self.cleaning_report['initial_rows'] = len(df)
        self.cleaning_report['initial_cols'] = len(df.columns)
        
        self._log(f"Dimensions initiales : {df.shape[0]} lignes × {df.shape[1]} colonnes")
        
        # Créer une copie pour ne pas modifier l'original
        df_clean = df.copy()
        
        # 1. Nettoyer les noms de colonnes
        self._log("\n[1/7] Nettoyage des noms de colonnes...")
        df_clean = self._clean_column_names(df_clean)
        
        # 2. Supprimer les headers dupliqués
        self._log("\n[2/7] Suppression des headers dupliqués...")
        df_clean = self._remove_header_duplicates(df_clean)
        
        # 3. Supprimer les lignes vides
        if remove_empty:
            self._log("\n[3/7] Suppression des lignes vides...")
            df_clean = self._remove_empty_rows(df_clean)
        else:
            self._log("\n[3/7] Suppression des lignes vides... SKIP")
        
        # 4. Supprimer les doublons
        if remove_duplicates:
            self._log("\n[4/7] Suppression des doublons...")
            df_clean = self._remove_duplicate_rows(df_clean)
        else:
            self._log("\n[4/7] Suppression des doublons... SKIP")
        
        # 5. Supprimer les stats composées
        if remove_composites:
            self._log("\n[5/7] Suppression des statistiques composées...")
            df_clean = self._remove_composite_stats(df_clean)
        else:
            self._log("\n[5/7] Suppression des statistiques composées... SKIP")
        
        # 6. Supprimer les pourcentages
        if remove_percentages:
            self._log("\n[6/7] Suppression des pourcentages...")
            df_clean = self._remove_percentage_stats(df_clean)
        else:
            self._log("\n[6/7] Suppression des pourcentages... SKIP")
        
        # 7. Convertir en numérique
        self._log("\n[7/7] Conversion des colonnes numériques...")
        df_clean = self._convert_numeric_columns(df_clean)
        
        # Enregistrer les stats finales
        self.cleaning_report['final_rows'] = len(df_clean)
        self.cleaning_report['final_cols'] = len(df_clean.columns)
        
        self._log("\n" + "="*80)
        self._log("NETTOYAGE TERMINÉ", "SUCCESS")
        self._log("="*80)
        self._log(f"Dimensions finales : {df_clean.shape[0]} lignes × {df_clean.shape[1]} colonnes")
        self._log(f"Réduction : {self.cleaning_report['initial_rows'] - self.cleaning_report['final_rows']} lignes supprimées")
        
        return df_clean
    
    def get_cleaning_report(self) -> dict:
        """
        Retourne un rapport détaillé du nettoyage
        
        Returns:
            Dictionnaire avec les statistiques de nettoyage
        """
        return self.cleaning_report
    
    def print_cleaning_report(self):
        """Affiche un rapport détaillé du nettoyage"""
        print("\n" + "="*80)
        print("RAPPORT DE NETTOYAGE")
        print("="*80)
        
        report = self.cleaning_report
        
        print(f"\nDimensions initiales : {report['initial_rows']} lignes × {report['initial_cols']} colonnes")
        print(f"Dimensions finales   : {report['final_rows']} lignes × {report['final_cols']} colonnes")
        print(f"\nRéduction totale : {report['initial_rows'] - report['final_rows']} lignes supprimées")
        
        print(f"\nDétails :")
        print(f"  - Doublons supprimés        : {report['removed_duplicates']}")
        print(f"  - Stats composées           : {len(report['removed_composite'])}")
        print(f"  - Pourcentages              : {len(report['removed_percentages'])}")
        print(f"  - Lignes vides              : {sum(report['removed_empty'])}")
        
        if report['removed_composite']:
            print(f"\n  Exemples de stats composées supprimées :")
            for stat in report['removed_composite'][:5]:
                print(f"    • {stat}")
        
        if report['removed_percentages']:
            print(f"\n  Exemples de pourcentages supprimés :")
            for stat in report['removed_percentages'][:5]:
                print(f"    • {stat}")
        
        print("="*80)


# Exemple d'utilisation
if __name__ == "__main__":
    # Charger des données test
    print("Test du DataCleaner avec des données d'exemple...\n")
    
    # Simuler des données FBref
    data = {
        'Statistic': ['Goals', 'Assists', 'Goals + Assists', 'Pass Completion %', 
                      'Shots', 'xG: Expected Goals', 'Goals - xG', 'Statistic', 
                      'Tackles', '', 'Interceptions'],
        'Per 90': ['0.50', '0.30', '0.80', '85.5%', '2.1', '0.45', '0.05', 'Per 90', '3.2', '', '1.5'],
        'Percentile': ['75', '60', '70', '90', '55', '50', '48', 'Percentile', '88', '', '65']
    }
    
    df = pd.DataFrame(data)
    
    print("DataFrame BRUT :")
    print(df)
    print("\n" + "="*80)
    
    # Nettoyer
    cleaner = DataCleaner(verbose=True)
    df_clean = cleaner.clean(df)
    
    print("\nDataFrame NETTOYÉ :")
    print(df_clean)
    
    # Rapport
    cleaner.print_cleaning_report()