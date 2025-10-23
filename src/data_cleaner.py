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
            'removed_composites': [],
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
        # Convertir en string pour éviter les erreurs
        row_str = row.astype(str)
        
        # Si le premier élément n'est pas vide mais les autres sont vides
        if row_str.iloc[0] and row_str.iloc[0] not in ['nan', 'NaN', '']:
            # Vérifier que les autres colonnes sont vides
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
        
        # D'abord supprimer les colonnes dupliquées par position
        # Cela évite le problème de df[col] qui retourne un DataFrame
        self._log("Suppression des colonnes dupliquées par nom...")
        df_dedup = df.loc[:, ~df.columns.duplicated(keep='first')]
        duplicates_removed = len(df.columns) - len(df_dedup.columns)
        if duplicates_removed > 0:
            self._log(f"Supprimé {duplicates_removed} colonne(s) dupliquée(s) par nom ✓", "SUCCESS")
        
        # Maintenant analyser les colonnes restantes
        for col in df_dedup.columns:
            # Supprimer les colonnes avec % dans le nom
            if '%' in str(col) or 'Percentage' in str(col):
                columns_to_drop.append(col)
                continue
            
            # Supprimer les colonnes vides (vérifier que toutes les valeurs sont NaN ou vides)
            # Maintenant df_dedup[col] est toujours une Series car pas de doublons
            if df_dedup[col].isna().all():
                columns_to_drop.append(col)
                continue
            
            # Vérifier si la colonne est entièrement composée de chaînes vides
            col_str = df_dedup[col].astype(str)
            if (col_str == '').all() or (col_str == 'nan').all():
                columns_to_drop.append(col)
        
        # Supprimer les colonnes identifiées
        df_clean = df_dedup.drop(columns=columns_to_drop, errors='ignore')
        
        removed = initial_cols - len(df_clean.columns)
        if removed > 0:
            self._log(f"Supprimé {removed} colonne(s) au total (doublons + % vides) ✓", "SUCCESS")
            if self.verbose and columns_to_drop:
                self._log(f"Exemples de colonnes supprimées : {columns_to_drop[:5]}...")
        
        return df_clean
    
    def clean(self, df: pd.DataFrame, metadata: Dict = None) -> pd.DataFrame:
        """
        Applique tous les nettoyages et transforme en format horizontal
        
        Args:
            df: DataFrame brut vertical (stats en lignes)
            metadata: Métadonnées du joueur
            
        Returns:
            DataFrame horizontal (stats en colonnes, 1 ligne = 1 joueur)
        """
        self._log("="*80)
        self._log("DÉBUT DU NETTOYAGE", "START")
        self._log("="*80)
        
        self.cleaning_report['initial_rows'] = len(df)
        self.cleaning_report['initial_cols'] = len(df.columns)
        
        self._log(f"Dimensions initiales : {df.shape[0]} lignes × {df.shape[1]} colonnes")
        
        df_clean = df.copy()
        
        # 1. Aplatir les MultiIndex
        self._log("\n[1/8] Gestion des MultiIndex...")
        df_clean = self._flatten_multiindex_columns(df_clean)
        
        # 2. Nettoyer les noms de colonnes
        self._log("\n[2/8] Nettoyage des noms de colonnes...")
        df_clean.columns = df_clean.columns.astype(str).str.strip()
        
        # 3. Identifier les colonnes (Statistic, Per 90, Percentile)
        self._log("\n[3/8] Identification des colonnes...")
        
        # Les colonnes sont souvent : [Statistic, Per 90, Percentile]
        col_names = list(df_clean.columns)
        self._log(f"Colonnes détectées : {col_names}")
        
        # Renommer pour standardiser
        if len(col_names) >= 2:
            df_clean.columns = ['Statistic', 'Per_90'] + col_names[2:]
        
        # 4. Supprimer la colonne Percentile (contexte temporel)
        self._log("\n[4/8] Suppression du Percentile...")
        if 'Percentile' in df_clean.columns or len(df_clean.columns) > 2:
            if len(df_clean.columns) > 2:
                df_clean = df_clean.iloc[:, :2]  # Garder seulement Statistic et Per_90
                self._log("Colonne Percentile supprimée ✓", "SUCCESS")
                self.cleaning_report['removed_percentiles'] = True
        
        # 5. Supprimer les lignes vides de catégories
        self._log("\n[5/8] Suppression des lignes de catégories vides...")
        initial_len = len(df_clean)
        
        # Méthode 1: Supprimer les lignes où Per_90 est vide
        df_clean = df_clean[df_clean['Per_90'].notna()]
        df_clean = df_clean[df_clean['Per_90'].astype(str) != '']
        
        # Méthode 2: Supprimer les lignes qui sont des headers
        df_clean = df_clean[df_clean['Statistic'] != 'Statistic']
        
        removed = initial_len - len(df_clean)
        if removed > 0:
            self._log(f"Supprimé {removed} ligne(s) vide(s) de catégories ✓", "SUCCESS")
            self.cleaning_report['removed_empty'] = removed
        
        # 6. Supprimer les stats composées
        self._log("\n[6/8] Suppression des stats composées...")
        initial_len = len(df_clean)
        mask = df_clean['Statistic'].apply(lambda x: not self._is_composite_stat(str(x)))
        df_clean = df_clean[mask]
        
        removed_composites = initial_len - len(df_clean)
        if removed_composites > 0:
            self._log(f"Supprimé {removed_composites} stat(s) composée(s) ✓", "SUCCESS")
        
        # 7. Transformer en format horizontal (PIVOT)
        self._log("\n[7/8] Transformation en format horizontal...")
        
        # Nettoyer les valeurs Per_90
        df_clean['Per_90'] = pd.to_numeric(df_clean['Per_90'], errors='coerce')
        
        # Créer un DataFrame horizontal
        # Statistiques deviennent les colonnes, valeurs = Per_90
        df_horizontal = pd.DataFrame([df_clean['Per_90'].values], columns=df_clean['Statistic'].values)
        
        # Ajouter les métadonnées au début
        if metadata:
            for key, value in metadata.items():
                df_horizontal.insert(0, key, value)
        
        # 8. Supprimer les colonnes % vides et doublons
        self._log("\n[8/8] Suppression des colonnes % vides et doublons...")
        df_horizontal = self._remove_percentage_and_duplicate_columns(df_horizontal)
        
        self.cleaning_report['final_rows'] = len(df_horizontal)
        self.cleaning_report['final_cols'] = len(df_horizontal.columns)
        
        self._log("\n" + "="*80)
        self._log("NETTOYAGE TERMINÉ", "SUCCESS")
        self._log("="*80)
        self._log(f"Format : HORIZONTAL (stats en colonnes)")
        self._log(f"Dimensions finales : {df_horizontal.shape[0]} ligne × {df_horizontal.shape[1]} colonnes")
        self._log(f"Stats conservées : {df_horizontal.shape[1] - len(metadata or {})} statistiques")
        
        return df_horizontal
    
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
        print(f"  • Stats composées         : {len(report['removed_composites'])}")
        
        print(f"\n✅ Avantages du format horizontal :")
        print(f"  • 1 ligne = 1 joueur")
        print(f"  • Facilite les comparaisons entre joueurs")
        print(f"  • Compatible avec les algorithmes ML")
        print(f"  • Pas de contexte temporel (Percentile supprimé)")
        
        print("="*80)


# Exemple d'utilisation
if __name__ == "__main__":
    print("Test du DataCleaner V2...\n")
    
    # Simuler des données FBref
    data = {
        'Statistic': ['Goals', 'Assists', 'Goals + Assists', 'Passes Completed', 
                      'Passing', '', 'Tackles', 'Statistic'],
        'Per 90': ['0.50', '0.30', '0.80', '92.3', '', '', '3.2', 'Per 90'],
        'Percentile': ['33', '71', '51', '99', '', '', '96', 'Percentile']
    }
    
    df = pd.DataFrame(data)
    
    metadata = {
        'name': 'Marco Verratti',
        'age': 30,
        'position': 'MF',
        'height_cm': 165
    }
    
    print("DataFrame BRUT (format vertical) :")
    print(df)
    print("\n" + "="*80)
    
    # Nettoyer
    cleaner = DataCleaner(verbose=True)
    df_clean = cleaner.clean(df, metadata)
    
    print("\nDataFrame NETTOYÉ (format horizontal) :")
    print(df_clean)
    
    # Rapport
    cleaner.print_cleaning_report()