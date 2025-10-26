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
        
        # Détection du format "Last 365 Days" (agrégé multi-compétitions)
        is_365_days = False
        if metadata and 'competition' in metadata:
            if 'Last 365 Days' in str(metadata['competition']):
                is_365_days = True
                self._log("⚠️ FORMAT SPÉCIAL DÉTECTÉ: Last 365 Days", "WARNING")
        
        self.cleaning_report['initial_rows'] = len(df)
        self.cleaning_report['initial_cols'] = len(df.columns)
        self._log(f"Dimensions initiales : {df.shape[0]} lignes × {df.shape[1]} colonnes")
        
        df_clean = df.copy()
        
        # 🔧 GESTION SPÉCIALE: Détecter si première ligne contient les vrais headers
        first_row = df_clean.iloc[0].astype(str).tolist()
        if 'Statistic' in first_row or 'Per 90' in first_row or 'Per_90' in first_row:
            self._log("⚠️ Headers détectés en première ligne de données", "WARNING")
            # Remplacer les colonnes par la première ligne
            df_clean.columns = first_row
            # Supprimer la première ligne
            df_clean = df_clean.iloc[1:].reset_index(drop=True)
            self._log("✓ Headers corrigés depuis première ligne", "SUCCESS")
        
        # 1️⃣ Aplatir les MultiIndex
        self._log("\n[1/8] Gestion des MultiIndex...")
        df_clean = self._flatten_multiindex_columns(df_clean)
        
        # 2️⃣ Nettoyage des noms de colonnes
        self._log("\n[2/8] Nettoyage des noms de colonnes...")
        df_clean.columns = df_clean.columns.astype(str).str.strip()
        df_clean.columns = [col.replace(" ", "_") for col in df_clean.columns]
        
        # 3️⃣ Identifier les colonnes
        self._log("\n[3/8] Identification des colonnes...")
        col_names = list(df_clean.columns)
        self._log(f"Colonnes détectées : {col_names[:10]}...")
        
        # Normalisation des colonnes principales
        rename_map = {}
        for col in df_clean.columns:
            col_lower = str(col).lower().strip()
            col_normalized = col_lower.replace("_", "").replace(" ", "").replace("-", "")
            
            # Détection Per 90
            if col_normalized == "per90" or col_lower in ["per 90", "per_90", "per-90"]:
                rename_map[col] = "Per_90"
                self._log(f"✓ Colonne Per90 trouvée : '{col}' -> 'Per_90'")
            
            # Détection Statistic
            elif "statistic" in col_lower:
                rename_map[col] = "Statistic"
                self._log(f"✓ Colonne Statistic trouvée : '{col}' -> 'Statistic'")
        
        # Appliquer renommage
        if rename_map:
            df_clean = df_clean.rename(columns=rename_map)
            self._log(f"Renommage appliqué : {len(rename_map)} colonne(s)")
        else:
            self._log("⚠️ Aucune colonne standard trouvée pour renommage", "WARNING")
        
        # Vérification et fallback
        if "Per_90" not in df_clean.columns:
            self._log("❌ 'Per_90' introuvable après renommage", "ERROR")
            available_cols = list(df_clean.columns)
            self._log(f"Colonnes actuelles: {available_cols[:20]}", "ERROR")
            
            # Fallback 1: chercher colonnes contenant "90"
            per90_candidates = [c for c in df_clean.columns if "90" in str(c)]
            if per90_candidates:
                self._log(f"Candidats '90' trouvés: {per90_candidates}", "WARNING")
                df_clean = df_clean.rename(columns={per90_candidates[0]: "Per_90"})
                self._log(f"✓ Utilisation de '{per90_candidates[0]}' comme Per_90", "SUCCESS")
            else:
                # Fallback 2: pour "Last 365 Days", chercher des colonnes de valeurs numériques
                if is_365_days:
                    self._log("Mode 365 Days: recherche colonne de valeurs...", "WARNING")
                    # Chercher colonne avec des valeurs numériques (pas Statistic ni Percentile)
                    for col in df_clean.columns:
                        if col not in ['Statistic', 'Percentile'] and df_clean[col].dtype in ['float64', 'int64', 'object']:
                            try:
                                pd.to_numeric(df_clean[col], errors='coerce')
                                df_clean = df_clean.rename(columns={col: "Per_90"})
                                self._log(f"✓ Colonne valeurs utilisée: '{col}' -> 'Per_90'", "SUCCESS")
                                break
                            except:
                                continue
                
                # Si toujours pas trouvé
                if "Per_90" not in df_clean.columns:
                    raise KeyError(
                        f"❌ ERREUR FATALE : impossible de trouver la colonne de valeurs.\n"
                        f"Colonnes disponibles : {available_cols}\n"
                        f"Format 365 Days : {is_365_days}"
                    )
        
        # 4️⃣ Supprimer Percentile
        self._log("\n[4/8] Suppression du Percentile...")
        if "Percentile" in df_clean.columns:
            df_clean = df_clean.drop(columns=["Percentile"])
            self.cleaning_report["removed_percentiles"] = True
            self._log("Colonne Percentile supprimée ✓", "SUCCESS")
        
        # 5️⃣ Supprimer les lignes vides / headers
        self._log("\n[5/8] Suppression des lignes de catégories vides...")
        initial_len = len(df_clean)
        df_clean = df_clean[df_clean["Per_90"].notna()]
        df_clean = df_clean[df_clean["Per_90"].astype(str).str.strip() != ""]
        df_clean = df_clean[df_clean["Statistic"] != "Statistic"]
        removed = initial_len - len(df_clean)
        if removed > 0:
            self._log(f"Supprimé {removed} ligne(s) vide(s) ✓", "SUCCESS")
            self.cleaning_report["removed_empty"] = removed
        
        # 6️⃣ Supprimer les stats composées
        self._log("\n[6/8] Suppression des stats composées...")
        initial_len = len(df_clean)
        mask = df_clean["Statistic"].apply(lambda x: not self._is_composite_stat(str(x)))
        df_clean = df_clean[mask]
        removed_composites = initial_len - len(df_clean)
        self.cleaning_report["removed_composites"] = removed_composites
        if removed_composites > 0:
            self._log(f"Supprimé {removed_composites} stat(s) composée(s) ✓", "SUCCESS")
        
        # 7️⃣ Format horizontal
        self._log("\n[7/8] Transformation en format horizontal...")
        df_clean["Per_90"] = pd.to_numeric(df_clean["Per_90"], errors="coerce")
        df_horizontal = pd.DataFrame([df_clean["Per_90"].values], columns=df_clean["Statistic"].values)
        
        if metadata:
            for key, value in metadata.items():
                df_horizontal.insert(0, key, value)
        
        # 8️⃣ Nettoyage final
        self._log("\n[8/8] Nettoyage final des colonnes...")
        df_horizontal = self._remove_percentage_and_duplicate_columns(df_horizontal)
        
        # Rapport final
        self.cleaning_report["final_rows"] = len(df_horizontal)
        self.cleaning_report["final_cols"] = len(df_horizontal.columns)
        
        self._log("\n" + "="*80)
        self._log("NETTOYAGE TERMINÉ", "SUCCESS")
        self._log("="*80)
        self._log(f"Format : HORIZONTAL (1 ligne = 1 joueur)")
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
