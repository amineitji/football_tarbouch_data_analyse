"""
PlayerAnalyzer - Classe pour analyser et visualiser les stats d'un joueur unique
Génère des graphiques et des insights détaillés
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from typing import List, Dict, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')


class PlayerAnalyzer:
    """
    Analyseur de joueur unique
    Génère des visualisations et des insights sur les performances
    """
    
    def __init__(self, player_name: str = None, position: str = None):
        """
        Initialise l'analyseur
        
        Args:
            player_name: Nom du joueur
            position: Position du joueur (MF, FW, DF, GK)
        """
        self.player_name = player_name or "Joueur"
        self.position = position or "Unknown"
        self.df = None
        
        # Configuration des graphiques
        plt.style.use('default')
        sns.set_palette("husl")
        
        # Catégories de stats par type
        self.stat_categories = {
            'Shooting': ['Goals', 'Shots Total', 'Shots on Target', 'xG', 'npxG'],
            'Passing': ['Passes Completed', 'Assists', 'Key Passes', 'xAG', 'xA'],
            'Defense': ['Tackles', 'Interceptions', 'Blocks', 'Clearances'],
            'Possession': ['Touches', 'Carries', 'Take-Ons Attempted', 'Successful Take-Ons'],
            'Progression': ['Progressive Carries', 'Progressive Passes', 'Carries into Final Third'],
            'Creation': ['Shot-Creating Actions', 'Goal-Creating Actions'],
            'Discipline': ['Yellow Cards', 'Red Cards', 'Fouls Committed', 'Fouls Drawn']
        }
    
    def _log(self, message: str, level: str = "INFO"):
        """Log simple"""
        print(f"[{level}] {message}")
    
    def load_data(self, df: pd.DataFrame):
        """
        Charge les données du joueur
        
        Args:
            df: DataFrame nettoyé avec les stats du joueur
        """
        self.df = df.copy()
        self._log(f"Données chargées : {len(self.df)} statistiques", "SUCCESS")
        
        # Extraire les métadonnées si disponibles
        if hasattr(df, 'attrs'):
            if 'player_name' in df.attrs:
                self.player_name = df.attrs['player_name']
    
    def _get_category_stats(self, category: str) -> pd.DataFrame:
        """
        Extrait les stats d'une catégorie spécifique
        
        Args:
            category: Nom de la catégorie (ex: 'Shooting', 'Passing')
            
        Returns:
            DataFrame filtré sur la catégorie
        """
        if category not in self.stat_categories:
            self._log(f"Catégorie '{category}' inconnue", "WARNING")
            return pd.DataFrame()
        
        keywords = self.stat_categories[category]
        
        # Filtrer les stats contenant les mots-clés
        mask = self.df['Statistic'].apply(
            lambda x: any(keyword.lower() in str(x).lower() for keyword in keywords)
        )
        
        return self.df[mask]
    
    def get_summary_stats(self) -> pd.DataFrame:
        """
        Génère un résumé statistique du joueur
        
        Returns:
            DataFrame avec les stats clés
        """
        if self.df is None:
            self._log("Aucune donnée chargée", "ERROR")
            return pd.DataFrame()
        
        summary = self.df[['Statistic', 'Per_90', 'Percentile']].copy()
        summary.columns = ['Statistique', 'Par 90min', 'Percentile']
        
        return summary
    
    def plot_percentile_radar(self, categories: List[str] = None, 
                             figsize: Tuple[int, int] = (12, 8),
                             save_path: str = None):
        """
        Crée un graphique radar des percentiles par catégorie
        
        Args:
            categories: Liste des catégories à afficher (None = toutes)
            figsize: Taille de la figure
            save_path: Chemin pour sauvegarder le graphique
        """
        if self.df is None:
            self._log("Aucune donnée chargée", "ERROR")
            return
        
        self._log("Création du radar des percentiles...")
        
        # Sélectionner les catégories
        if categories is None:
            categories = list(self.stat_categories.keys())
        
        # Calculer la moyenne des percentiles par catégorie
        category_means = {}
        for cat in categories:
            cat_df = self._get_category_stats(cat)
            if not cat_df.empty and 'Percentile' in cat_df.columns:
                mean_percentile = cat_df['Percentile'].mean()
                category_means[cat] = mean_percentile
        
        if not category_means:
            self._log("Aucune donnée de percentile disponible", "WARNING")
            return
        
        # Créer le radar
        fig = plt.figure(figsize=figsize)
        ax = fig.add_subplot(111, projection='polar')
        
        # Préparer les données
        categories_list = list(category_means.keys())
        values = list(category_means.values())
        
        # Fermer le polygone
        values += values[:1]
        
        # Angles pour chaque catégorie
        angles = np.linspace(0, 2 * np.pi, len(categories_list), endpoint=False).tolist()
        angles += angles[:1]
        
        # Tracer
        ax.plot(angles, values, 'o-', linewidth=2, label=self.player_name)
        ax.fill(angles, values, alpha=0.25)
        
        # Personnalisation
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(categories_list, size=10)
        ax.set_ylim(0, 100)
        ax.set_yticks([20, 40, 60, 80, 100])
        ax.set_yticklabels(['20', '40', '60', '80', '100'], size=8)
        ax.grid(True)
        
        # Titre
        plt.title(f'{self.player_name} - Profil Radar (Percentiles)\n{self.position}', 
                 size=16, weight='bold', pad=20)
        
        # Légende
        plt.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1))
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            self._log(f"Graphique sauvegardé : {save_path}", "SUCCESS")
        
        plt.show()
    
    def plot_top_stats(self, n: int = 15, metric: str = 'Percentile',
                      figsize: Tuple[int, int] = (12, 8),
                      save_path: str = None):
        """
        Affiche les top N statistiques du joueur
        
        Args:
            n: Nombre de stats à afficher
            metric: Métrique à utiliser ('Percentile' ou 'Per_90')
            figsize: Taille de la figure
            save_path: Chemin pour sauvegarder
        """
        if self.df is None:
            self._log("Aucune donnée chargée", "ERROR")
            return
        
        self._log(f"Création du graphique Top {n} stats...")
        
        # Vérifier que la colonne existe
        if metric not in self.df.columns:
            self._log(f"Colonne '{metric}' introuvable", "ERROR")
            return
        
        # Trier et sélectionner le top N
        top_stats = self.df.nlargest(n, metric)[['Statistic', metric]].copy()
        
        # Créer le graphique
        fig, ax = plt.subplots(figsize=figsize)
        
        # Barplot horizontal
        bars = ax.barh(top_stats['Statistic'], top_stats[metric], 
                       color=plt.cm.viridis(top_stats[metric] / 100))
        
        # Ajouter les valeurs sur les barres
        for i, bar in enumerate(bars):
            width = bar.get_width()
            ax.text(width, bar.get_y() + bar.get_height()/2, 
                   f'{width:.1f}', 
                   ha='left', va='center', fontsize=9, fontweight='bold')
        
        # Personnalisation
        ax.set_xlabel(metric, fontsize=12, weight='bold')
        ax.set_ylabel('Statistique', fontsize=12, weight='bold')
        ax.set_title(f'{self.player_name} - Top {n} Statistiques ({metric})\n{self.position}', 
                    fontsize=16, weight='bold', pad=20)
        
        # Inverser l'ordre (meilleur en haut)
        ax.invert_yaxis()
        
        # Grille
        ax.grid(axis='x', alpha=0.3, linestyle='--')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            self._log(f"Graphique sauvegardé : {save_path}", "SUCCESS")
        
        plt.show()
    
    def plot_category_comparison(self, figsize: Tuple[int, int] = (14, 8),
                                save_path: str = None):
        """
        Compare les performances du joueur par catégorie
        
        Args:
            figsize: Taille de la figure
            save_path: Chemin pour sauvegarder
        """
        if self.df is None:
            self._log("Aucune donnée chargée", "ERROR")
            return
        
        self._log("Création de la comparaison par catégories...")
        
        # Calculer les moyennes par catégorie
        category_data = []
        for cat, keywords in self.stat_categories.items():
            cat_df = self._get_category_stats(cat)
            if not cat_df.empty:
                mean_percentile = cat_df['Percentile'].mean()
                mean_per90 = cat_df['Per_90'].mean()
                category_data.append({
                    'Category': cat,
                    'Mean_Percentile': mean_percentile,
                    'Mean_Per90': mean_per90,
                    'Count': len(cat_df)
                })
        
        if not category_data:
            self._log("Aucune donnée de catégorie disponible", "WARNING")
            return
        
        cat_df = pd.DataFrame(category_data)
        
        # Créer la figure avec 2 subplots
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize)
        
        # Graphique 1 : Percentiles moyens
        bars1 = ax1.bar(cat_df['Category'], cat_df['Mean_Percentile'], 
                       color=plt.cm.RdYlGn(cat_df['Mean_Percentile'] / 100))
        
        ax1.set_ylabel('Percentile Moyen', fontsize=11, weight='bold')
        ax1.set_title('Performance par Catégorie\n(Percentile)', fontsize=13, weight='bold')
        ax1.set_ylim(0, 100)
        ax1.axhline(50, color='red', linestyle='--', alpha=0.5, label='Médiane (50e)')
        ax1.legend()
        ax1.grid(axis='y', alpha=0.3)
        plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45, ha='right')
        
        # Ajouter valeurs sur les barres
        for bar in bars1:
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.1f}',
                    ha='center', va='bottom', fontsize=9, fontweight='bold')
        
        # Graphique 2 : Valeurs par 90
        bars2 = ax2.bar(cat_df['Category'], cat_df['Mean_Per90'], 
                       color=plt.cm.Blues(cat_df['Mean_Per90'] / cat_df['Mean_Per90'].max()))
        
        ax2.set_ylabel('Valeur Moyenne par 90min', fontsize=11, weight='bold')
        ax2.set_title('Quantité par Catégorie\n(Par 90min)', fontsize=13, weight='bold')
        ax2.grid(axis='y', alpha=0.3)
        plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45, ha='right')
        
        # Ajouter valeurs sur les barres
        for bar in bars2:
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.2f}',
                    ha='center', va='bottom', fontsize=9, fontweight='bold')
        
        # Titre principal
        fig.suptitle(f'{self.player_name} - Analyse par Catégories\n{self.position}', 
                    fontsize=16, weight='bold', y=1.00)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            self._log(f"Graphique sauvegardé : {save_path}", "SUCCESS")
        
        plt.show()
    
    def plot_percentile_distribution(self, figsize: Tuple[int, int] = (12, 6),
                                    save_path: str = None):
        """
        Affiche la distribution des percentiles du joueur
        
        Args:
            figsize: Taille de la figure
            save_path: Chemin pour sauvegarder
        """
        if self.df is None or 'Percentile' not in self.df.columns:
            self._log("Aucune donnée de percentile disponible", "ERROR")
            return
        
        self._log("Création de la distribution des percentiles...")
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize)
        
        # Histogramme
        ax1.hist(self.df['Percentile'], bins=20, edgecolor='black', 
                color='skyblue', alpha=0.7)
        ax1.axvline(self.df['Percentile'].mean(), color='red', 
                   linestyle='--', linewidth=2, label=f'Moyenne: {self.df["Percentile"].mean():.1f}')
        ax1.axvline(self.df['Percentile'].median(), color='green', 
                   linestyle='--', linewidth=2, label=f'Médiane: {self.df["Percentile"].median():.1f}')
        ax1.set_xlabel('Percentile', fontsize=11, weight='bold')
        ax1.set_ylabel('Nombre de stats', fontsize=11, weight='bold')
        ax1.set_title('Distribution des Percentiles', fontsize=13, weight='bold')
        ax1.legend()
        ax1.grid(alpha=0.3)
        
        # Boxplot
        ax2.boxplot(self.df['Percentile'], vert=True, patch_artist=True,
                   boxprops=dict(facecolor='lightblue', alpha=0.7),
                   medianprops=dict(color='red', linewidth=2))
        ax2.set_ylabel('Percentile', fontsize=11, weight='bold')
        ax2.set_title('Répartition des Percentiles', fontsize=13, weight='bold')
        ax2.set_xticklabels([self.player_name])
        ax2.grid(axis='y', alpha=0.3)
        
        # Stats textuelles
        stats_text = f"""
        Min: {self.df['Percentile'].min():.1f}
        Q1: {self.df['Percentile'].quantile(0.25):.1f}
        Médiane: {self.df['Percentile'].median():.1f}
        Q3: {self.df['Percentile'].quantile(0.75):.1f}
        Max: {self.df['Percentile'].max():.1f}
        """
        ax2.text(1.15, 50, stats_text, transform=ax2.transData,
                fontsize=10, verticalalignment='center',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
        fig.suptitle(f'{self.player_name} - Analyse des Percentiles\n{self.position}', 
                    fontsize=16, weight='bold', y=0.98)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            self._log(f"Graphique sauvegardé : {save_path}", "SUCCESS")
        
        plt.show()
    
    def generate_full_report(self, output_dir: str = './analysis_output'):
        """
        Génère un rapport complet avec tous les graphiques
        
        Args:
            output_dir: Dossier de sortie pour les graphiques
        """
        import os
        
        if self.df is None:
            self._log("Aucune donnée chargée", "ERROR")
            return
        
        # Créer le dossier de sortie
        os.makedirs(output_dir, exist_ok=True)
        
        self._log("="*80)
        self._log(f"GÉNÉRATION DU RAPPORT COMPLET : {self.player_name}", "START")
        self._log("="*80)
        
        # Générer tous les graphiques
        safe_name = self.player_name.replace(' ', '_').replace('-', '_')
        
        self.plot_percentile_radar(
            save_path=f'{output_dir}/{safe_name}_radar.png'
        )
        
        self.plot_top_stats(
            n=15, 
            save_path=f'{output_dir}/{safe_name}_top_stats.png'
        )
        
        self.plot_category_comparison(
            save_path=f'{output_dir}/{safe_name}_categories.png'
        )
        
        self.plot_percentile_distribution(
            save_path=f'{output_dir}/{safe_name}_distribution.png'
        )
        
        self._log("="*80)
        self._log(f"RAPPORT COMPLET GÉNÉRÉ dans : {output_dir}", "SUCCESS")
        self._log("="*80)
    
    def get_strengths_and_weaknesses(self, top_n: int = 5) -> Dict[str, List]:
        """
        Identifie les forces et faiblesses du joueur
        
        Args:
            top_n: Nombre de stats à retourner
            
        Returns:
            Dictionnaire avec les forces et faiblesses
        """
        if self.df is None or 'Percentile' not in self.df.columns:
            return {'strengths': [], 'weaknesses': []}
        
        strengths = self.df.nlargest(top_n, 'Percentile')[['Statistic', 'Percentile']].to_dict('records')
        weaknesses = self.df.nsmallest(top_n, 'Percentile')[['Statistic', 'Percentile']].to_dict('records')
        
        return {
            'strengths': strengths,
            'weaknesses': weaknesses
        }
    
    def print_player_profile(self):
        """Affiche un profil textuel du joueur"""
        if self.df is None:
            self._log("Aucune donnée chargée", "ERROR")
            return
        
        print("\n" + "="*80)
        print(f"PROFIL JOUEUR : {self.player_name}")
        print("="*80)
        print(f"Position        : {self.position}")
        print(f"Stats analysées : {len(self.df)}")
        
        if 'Percentile' in self.df.columns:
            print(f"\nPercentile moyen : {self.df['Percentile'].mean():.1f}")
            print(f"Percentile médian: {self.df['Percentile'].median():.1f}")
        
        # Forces et faiblesses
        analysis = self.get_strengths_and_weaknesses(5)
        
        print("\n🌟 FORCES (Top 5) :")
        for i, stat in enumerate(analysis['strengths'], 1):
            print(f"  {i}. {stat['Statistic']:<40} → {stat['Percentile']:.0f}e percentile")
        
        print("\n⚠️  FAIBLESSES (Top 5) :")
        for i, stat in enumerate(analysis['weaknesses'], 1):
            print(f"  {i}. {stat['Statistic']:<40} → {stat['Percentile']:.0f}e percentile")
        
        print("="*80)


# Exemple d'utilisation
if __name__ == "__main__":
    # Simuler des données nettoyées
    print("Test du PlayerAnalyzer avec des données simulées...\n")
    
    data = {
        'Statistic': ['Goals', 'Assists', 'Passes Completed', 'Tackles', 'Interceptions',
                     'Shots Total', 'Key Passes', 'Progressive Passes', 'Blocks', 'Touches'],
        'Per_90': [0.5, 0.3, 92.3, 3.9, 0.87, 0.29, 0.58, 6.5, 1.88, 108.2],
        'Percentile': [33, 71, 99, 96, 37, 13, 31, 75, 83, 99]
    }
    
    df = pd.DataFrame(data)
    df.attrs['player_name'] = 'Marco Verratti'
    
    # Créer l'analyseur
    analyzer = PlayerAnalyzer(player_name='Marco Verratti', position='MF')
    analyzer.load_data(df)
    
    # Profil textuel
    analyzer.print_player_profile()
    
    # Graphiques (commentez si pas d'affichage)
    # analyzer.plot_top_stats(n=10)
    # analyzer.plot_percentile_distribution()