"""
DataCleaner V2 - Nettoyage amélioré
- Supprime le Percentile (contexte temporel)
- Garde uniquement Per 90 (valeurs absolues comparables)
- Format horizontal (1 ligne = 1 joueur)
- Supprime les lignes vides de catégories
"""

import pandas as pd
import numpy as np
import re
from typing import Dict


class DataCleaner:
    """
    Nettoyeur de données FBref version améliorée
    Prépare les données pour comparaison inter-saisons
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
            'removed_percentiles': False,
            'removed_composites': 0,
            'removed_empty': 0,
            'format': 'horizontal'
        }
    
    def _log(self, message: str, level: str = "INFO"):
        """Log si verbose activé"""
        if self.verbose:
            print(f"[{level}] {message}")
    
    def _flatten_multiindex_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Aplatit les MultiIndex en colonnes simples"""
        if isinstance(df.columns, pd.MultiIndex):
            # Prendre le dernier niveau non-vide
            df.columns = [col[-1] if col[-1] else col[0] for col in df.columns]
        return df
    
    def _is_composite_stat(self, stat_name: str) -> bool:
        """Détecte les stats composées (x+y, x-y, x/y)"""
        composite_patterns = [r'\+', r' - ', r'\/', r' vs ']
        for pattern in composite_patterns:
            if re.search(pattern, str(stat_name)):
                return True
        return False
    
    def _is_empty_category_row(self, row: pd.Series) -> bool:
        """
        Détecte les lignes vides qui sont des headers de catégories
        Ex: "Passing", "", "" ou "Defense", "", ""
        """
        row_str = row.astype(str)
        if row_str.iloc[0] and row_str.iloc[0] not in ['nan', 'NaN', '']:
            other_cols = row_str.iloc[1:]
            if all(val in ['', 'nan', 'NaN'] for val in other_cols):
                return True
        return False
    
    def _remove_percentage_and_duplicate_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Supprime les colonnes de pourcentages vides et les doublons de stats
        Ex: "Shots on Target %" (vide) ou stats qui apparaissent 2 fois
        """
        initial_cols = len(df.columns)
        columns_to_drop = []
        
        self._log("Suppression des colonnes dupliquées par nom...")
        df_dedup = df.loc[:, ~df.columns.duplicated(keep='first')]
        duplicates_removed = len(df.columns) - len(df_dedup.columns)
        if duplicates_removed > 0:
            self._log(f"Supprimé {duplicates_removed} colonne(s) dupliquée(s) ✓", "SUCCESS")
        
        for col in df_dedup.columns:
            if '%' in str(col) or 'Percentage' in str(col):
                columns_to_drop.append(col)
                continue
            if df_dedup[col].isna().all():
                columns_to_drop.append(col)
                continue
            col_str = df_dedup[col].astype(str)
            if (col_str == '').all() or (col_str == 'nan').all():
                columns_to_drop.append(col)
        
        df_clean = df_dedup.drop(columns=columns_to_drop, errors='ignore')
        removed = initial_cols - len(df_clean.columns)
        if removed > 0:
            self._log(f"Supprimé {removed} colonne(s) au total (doublons + % vides) ✓", "SUCCESS")
            if self.verbose and columns_to_drop:
                self._log(f"Exemples de colonnes supprimées : {columns_to_drop[:5]}...")
        
        return df_clean
    
    def clean(self, df: pd.DataFrame, metadata: Dict = None) -> pd.DataFrame:
        """
        Nettoyage simple car données déjà en format horizontal (1 ligne = 1 saison)
        
        Args:
            df: DataFrame déjà horizontal (stats en colonnes)
            metadata: Métadonnées du joueur
            
        Returns:
            DataFrame nettoyé avec métadonnées
        """
        self._log("="*80)
        self._log("DÉBUT DU NETTOYAGE", "START")
        self._log("="*80)
        
        self.cleaning_report['initial_rows'] = len(df)
        self.cleaning_report['initial_cols'] = len(df.columns)
        self._log(f"Dimensions initiales : {df.shape[0]} lignes × {df.shape[1]} colonnes")
        
        df_clean = df.copy()
        
        # Ajouter métadonnées si fournies
        if metadata:
            for key, value in metadata.items():
                if key not in df_clean.columns:
                    df_clean.insert(0, key, value)
        
        # Supprimer colonnes de pourcentages vides
        df_clean = self._remove_percentage_and_duplicate_columns(df_clean)
        
        # Supprimer colonnes Percentile si présentes
        if "Percentile" in df_clean.columns:
            df_clean = df_clean.drop(columns=["Percentile"])
            self.cleaning_report["removed_percentiles"] = True
            self._log("Colonne Percentile supprimée ✓", "SUCCESS")
        
        # Rapport final
        self.cleaning_report["final_rows"] = len(df_clean)
        self.cleaning_report["final_cols"] = len(df_clean.columns)
        
        self._log("\n" + "="*80)
        self._log("NETTOYAGE TERMINÉ", "SUCCESS")
        self._log("="*80)
        self._log(f"Format : HORIZONTAL (1 ligne = 1 saison)")
        self._log(f"Dimensions finales : {df_clean.shape[0]} ligne × {df_clean.shape[1]} colonnes")
        
        return df_clean
    
    def get_cleaning_report(self) -> dict:
        """Retourne le rapport de nettoyage"""
        return self.cleaning_report
    
    def print_cleaning_report(self):
        """Affiche un rapport détaillé"""
        print("\n" + "="*80)
        print("RAPPORT DE NETTOYAGE")
        print("="*80)
        report = self.cleaning_report
        print(f"\n📊 Transformation :")
        print(f"  • Format initial  : VERTICAL (stats en lignes)")
        print(f"  • Format final    : HORIZONTAL (stats en colonnes)")
        print(f"\n📏 Dimensions :")
        print(f"  • Avant : {report['initial_rows']} lignes × {report['initial_cols']} colonnes")
        print(f"  • Après : {report['final_rows']} ligne  × {report['final_cols']} colonnes")
        print(f"\n🗑️  Suppressions :")
        print(f"  • Percentile retiré       : {'✓ OUI' if report['removed_percentiles'] else '✗ NON'}")
        print(f"  • Lignes vides/catégories : {report['removed_empty']}")
        print(f"  • Stats composées         : {report['removed_composites']}")
        print(f"\n✅ Avantages du format horizontal :")
        print(f"  • 1 ligne = 1 joueur")
        print(f"  • Comparaisons directes inter-joueurs")
        print(f"  • Compatible avec les algorithmes ML")
        print(f"  • Pas de biais temporel (Percentile supprimé)")
        print("="*80)


# Exemple d'utilisation
if __name__ == "__main__":
    print("Test du DataCleaner V2...\n")
    
    # Exemple minimal pour test
    data = {
        'Statistic': ['Goals', 'Assists', 'Goals + Assists', 'Passes Completed', 'Passing', '', 'Tackles', 'Statistic'],
        'Per 90': ['0.50', '0.30', '0.80', '92.3', '', '', '3.2', 'Per 90'],
        'Percentile': ['33', '71', '51', '99', '', '', '96', 'Percentile']
    }
    
    df = pd.DataFrame(data)
    
    metadata = {'name': 'Marco Verratti', 'season': '2024-2025'}
    
    print("DataFrame BRUT (vertical) :")
    print(df)
    print("\n" + "="*80)
    
    cleaner = DataCleaner(verbose=True)
    df_clean = cleaner.clean(df, metadata)
    
    print("\nDataFrame NETTOYÉ (horizontal) :")
    print(df_clean)
    
    cleaner.print_cleaning_report()