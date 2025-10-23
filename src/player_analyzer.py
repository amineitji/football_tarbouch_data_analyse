"""
PlayerAnalyzer V2 - Analyse tactique avancée avec visualisations innovantes + IA
Génère des graphiques détaillés pour chaque aspect : Passing, Shooting, Defense, etc.
+ Clustering K-Means, PCA, analyse de similarité
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
from typing import List, Dict, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

# IA et ML
try:
    from sklearn.preprocessing import StandardScaler
    from sklearn.decomposition import PCA
    from sklearn.cluster import KMeans
    from sklearn.metrics import silhouette_score
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    print("⚠️ scikit-learn non disponible. Analyses IA désactivées.")



class PlayerAnalyzer:
    """
    Analyseur de joueur avec visualisations tactiques avancées
    Analyse détaillée par aspect : Passing, Shooting, Defense, Possession, etc.
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
        plt.style.use('seaborn-v0_8-darkgrid')
        sns.set_palette("husl")
        
        # Catégories de stats par type (VERSION AMÉLIORÉE)
        self.stat_categories = {
            'Shooting': {
                'keywords': ['Goals', 'Shots', 'xG', 'npxG', 'Shot', 'Shooting'],
                'color': '#e74c3c',
                'description': 'Efficacité offensive et qualité des tirs'
            },
            'Passing': {
                'keywords': ['Pass', 'Assist', 'Key Pass', 'xAG', 'xA', 'Completion'],
                'color': '#3498db',
                'description': 'Qualité et précision des passes'
            },
            'Defense': {
                'keywords': ['Tackle', 'Intercept', 'Block', 'Clearance', 'Aerial'],
                'color': '#2ecc71',
                'description': 'Actions défensives et duels'
            },
            'Possession': {
                'keywords': ['Touch', 'Carry', 'Take-On', 'Dribble', 'Miscontrols'],
                'color': '#f39c12',
                'description': 'Maîtrise du ballon et dribbles'
            },
            'Progression': {
                'keywords': ['Progressive', 'Final Third', 'Penalty Area'],
                'color': '#9b59b6',
                'description': 'Progression vers le but adverse'
            },
            'Creation': {
                'keywords': ['Shot-Creating', 'Goal-Creating', 'SCA', 'GCA'],
                'color': '#1abc9c',
                'description': 'Création de danger et opportunités'
            },
            'Discipline': {
                'keywords': ['Yellow', 'Red', 'Foul', 'Card'],
                'color': '#e67e22',
                'description': 'Discipline et engagement physique'
            }
        }
    
    def _log(self, message: str, level: str = "INFO"):
        """Log simple"""
        print(f"[{level}] {message}")
    
    def load_data(self, df: pd.DataFrame):
        """
        Charge les données du joueur
        
        Args:
            df: DataFrame nettoyé avec les stats du joueur (format horizontal)
        """
        # Convertir format horizontal en vertical pour l'analyse
        # Si déjà vertical, garder tel quel
        if 'Statistic' in df.columns:
            self.df = df.copy()
        else:
            # Convertir horizontal → vertical
            # Extraire les métadonnées
            metadata_cols = ['name', 'age', 'position', 'season', 'competition', 
                           'birth_date', 'height_cm', 'weight_kg', 'minutes_played']
            
            stats_cols = [col for col in df.columns if col not in metadata_cols]
            
            # Créer le format vertical
            stats_data = []
            for col in stats_cols:
                if pd.notna(df[col].iloc[0]):
                    stats_data.append({
                        'Statistic': col,
                        'Per_90': df[col].iloc[0]
                    })
            
            self.df = pd.DataFrame(stats_data)
            
            # Extraire métadonnées
            if 'name' in df.columns:
                self.player_name = df['name'].iloc[0]
            if 'position' in df.columns:
                self.position = df['position'].iloc[0]
        
        self._log(f"Données chargées : {len(self.df)} statistiques", "SUCCESS")
    
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
        
        keywords = self.stat_categories[category]['keywords']
        
        # Filtrer les stats contenant les mots-clés
        mask = self.df['Statistic'].apply(
            lambda x: any(keyword.lower() in str(x).lower() for keyword in keywords)
        )
        
        return self.df[mask].copy()
    
    def plot_spider_radar(self, categories: List[str] = None, 
                         figsize: Tuple[int, int] = (16, 16),
                         save_path: str = None):
        """
        🕷️ SPIDER PLOT AMÉLIORÉ - Échelle adaptative pour valoriser les performances
        L'échelle commence à 50% du maximum pour mieux visualiser les forces du joueur
        
        Args:
            categories: Liste des catégories à afficher (None = toutes)
            figsize: Taille de la figure
            save_path: Chemin pour sauvegarder le graphique
        """
        if self.df is None:
            self._log("Aucune donnée chargée", "ERROR")
            return
        
        self._log("🕷️  Création du spider plot avec échelle adaptative...")
        
        # Sélectionner les catégories
        if categories is None:
            categories = list(self.stat_categories.keys())
        
        # Calculer les scores par catégorie
        category_means = {}
        for cat in categories:
            cat_df = self._get_category_stats(cat)
            if not cat_df.empty and 'Per_90' in cat_df.columns:
                values = cat_df['Per_90'].dropna()
                if len(values) > 0:
                    # Score normalisé
                    normalized = (values / values.max() * 100).mean()
                    category_means[cat] = min(normalized, 100)
        
        if not category_means:
            self._log("Aucune donnée disponible", "WARNING")
            return
        
        # Échelle adaptative : commence à 50% du max pour mieux visualiser
        max_value = max(category_means.values())
        min_scale = max_value * 0.5  # Échelle commence à 50%
        
        # Créer le radar avec fond élégant
        fig = plt.figure(figsize=figsize, facecolor='#f8f9fa')
        ax = fig.add_subplot(111, projection='polar')
        ax.set_facecolor('white')
        
        # Préparer les données
        categories_list = list(category_means.keys())
        values = list(category_means.values())
        
        # Fermer le polygone
        values += values[:1]
        
        # Angles pour chaque catégorie
        angles = np.linspace(0, 2 * np.pi, len(categories_list), endpoint=False).tolist()
        angles += angles[:1]
        
        # Zones de référence colorées (excellent, bon, moyen)
        excellent_threshold = max_value * 0.85
        good_threshold = max_value * 0.7
        
        # Remplissage de fond par zones
        theta = np.linspace(0, 2*np.pi, 100)
        ax.fill_between(theta, min_scale, good_threshold, alpha=0.08, color='orange', zorder=0)
        ax.fill_between(theta, good_threshold, excellent_threshold, alpha=0.08, color='yellow', zorder=0)
        ax.fill_between(theta, excellent_threshold, max_value*1.05, alpha=0.08, color='green', zorder=0)
        
        # Ligne principale avec style premium
        ax.plot(angles, values, 'o-', linewidth=5, color='#1a1a2e', 
               markersize=16, markeredgecolor='white', markeredgewidth=4,
               zorder=5, alpha=0.95, label=self.player_name)
        
        # Remplissage avec dégradé
        ax.fill(angles, values, alpha=0.35, color='#0f3460', zorder=2)
        
        # Personnalisation des axes
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(categories_list, size=16, weight='bold', color='#2c3e50')
        
        # Échelle adaptative
        ax.set_ylim(min_scale, max_value * 1.05)
        
        # Ticks avec valeurs arrondies
        yticks = np.linspace(min_scale, max_value, 5)
        ax.set_yticks(yticks)
        ax.set_yticklabels([f'{y:.0f}' for y in yticks], size=12, color='#34495e', weight='bold')
        
        # Grille améliorée
        ax.grid(True, linestyle='--', alpha=0.5, linewidth=1.5, color='#95a5a6')
        
        # Ajouter les valeurs sur chaque point
        for angle, value, cat in zip(angles[:-1], values[:-1], categories_list):
            ax.text(angle, value + max_value*0.03, f'{value:.0f}', 
                   ha='center', va='center', size=11, weight='bold',
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='white', 
                            edgecolor='black', linewidth=1.5),
                   zorder=6)
        
        # Titre avec informations clés
        title_text = f'🕷️ {self.player_name} - Profil Tactique Radar\n'
        title_text += f'{self.position} • Échelle: {min_scale:.0f}-{max_value:.0f} (optimisée pour valoriser les forces)'
        plt.title(title_text, size=20, weight='bold', pad=35, color='#1a1a2e')
        
        # Légende avec zones de performance
        legend_elements = [
            mpatches.Patch(facecolor='green', alpha=0.3, label=f'Excellent (>{excellent_threshold:.0f})'),
            mpatches.Patch(facecolor='yellow', alpha=0.3, label=f'Bon ({good_threshold:.0f}-{excellent_threshold:.0f})'),
            mpatches.Patch(facecolor='orange', alpha=0.3, label=f'Moyen ({min_scale:.0f}-{good_threshold:.0f})')
        ]
        ax.legend(handles=legend_elements, loc='upper right', bbox_to_anchor=(1.15, 1.15), 
                 frameon=True, fancybox=True, shadow=True, fontsize=11)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight', facecolor='#f8f9fa')
            self._log(f"✅ Spider radar sauvegardé : {save_path}", "SUCCESS")
        else:
            plt.show()
        
        plt.close()

    
    def plot_tactical_heatmap(self, figsize: Tuple[int, int] = (14, 10),
                             save_path: str = None):
        """
        🔥 HEATMAP TACTIQUE - Matrice de performance par catégorie
        Visualisation des forces/faiblesses par aspect du jeu
        """
        if self.df is None:
            self._log("Aucune donnée chargée", "ERROR")
            return
        
        self._log("🔥 Création de la heatmap tactique...")
        
        # Préparer les données pour la heatmap
        heatmap_data = []
        for category, info in self.stat_categories.items():
            cat_df = self._get_category_stats(category)
            if not cat_df.empty:
                for _, row in cat_df.iterrows():
                    heatmap_data.append({
                        'Category': category,
                        'Statistic': row['Statistic'],
                        'Value': row['Per_90'] if 'Per_90' in row else 0
                    })
        
        if not heatmap_data:
            self._log("Aucune donnée disponible", "WARNING")
            return
        
        # Créer le DataFrame
        heatmap_df = pd.DataFrame(heatmap_data)
        
        # Pivot pour avoir une matrice
        pivot_df = heatmap_df.pivot(index='Statistic', columns='Category', values='Value')
        pivot_df = pivot_df.fillna(0)
        
        # Normaliser les valeurs pour chaque catégorie (0-1)
        pivot_normalized = pivot_df.copy()
        for col in pivot_normalized.columns:
            col_max = pivot_normalized[col].max()
            if col_max > 0:
                pivot_normalized[col] = pivot_normalized[col] / col_max
        
        # Créer la heatmap
        fig, ax = plt.subplots(figsize=figsize)
        
        # Heatmap avec colormap personnalisée
        sns.heatmap(pivot_normalized, annot=pivot_df, fmt='.2f', 
                   cmap='RdYlGn', center=0.5, linewidths=0.5, 
                   cbar_kws={'label': 'Performance Normalisée'},
                   ax=ax, vmin=0, vmax=1)
        
        # Personnalisation
        ax.set_title(f'🔥 {self.player_name} - Heatmap Tactique Détaillée\n{self.position}', 
                    fontsize=16, weight='bold', pad=20)
        ax.set_xlabel('Aspect Tactique', fontsize=12, weight='bold')
        ax.set_ylabel('Statistique', fontsize=12, weight='bold')
        
        plt.xticks(rotation=45, ha='right')
        plt.yticks(rotation=0)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight', facecolor='white')
            self._log(f"✅ Graphique sauvegardé : {save_path}", "SUCCESS")
        
        plt.show()
    
    def plot_polar_category(self, category: str, figsize: Tuple[int, int] = (10, 10),
                           save_path: str = None):
        """
        ⭕ GRAPHIQUE POLAIRE - Analyse détaillée d'un aspect tactique spécifique
        
        Args:
            category: Catégorie à analyser ('Shooting', 'Passing', etc.)
            figsize: Taille de la figure
            save_path: Chemin pour sauvegarder
        """
        if self.df is None:
            self._log("Aucune donnée chargée", "ERROR")
            return
        
        cat_df = self._get_category_stats(category)
        
        if cat_df.empty:
            self._log(f"Aucune donnée pour la catégorie '{category}'", "WARNING")
            return
        
        self._log(f"⭕ Création du graphique polaire pour {category}...")
        
        # Préparer les données
        stats = cat_df['Statistic'].tolist()
        values = cat_df['Per_90'].tolist()
        
        # Normaliser les valeurs (0-100)
        max_val = max(values) if max(values) > 0 else 1
        normalized_values = [(v / max_val * 100) for v in values]
        
        # Fermer le polygone
        stats += stats[:1]
        normalized_values += normalized_values[:1]
        
        # Angles
        angles = np.linspace(0, 2 * np.pi, len(stats) - 1, endpoint=False).tolist()
        angles += angles[:1]
        
        # Créer le graphique polaire
        fig = plt.figure(figsize=figsize)
        ax = fig.add_subplot(111, projection='polar')
        
        # Couleur de la catégorie
        color = self.stat_categories[category]['color']
        
        # Tracer
        ax.plot(angles, normalized_values, 'o-', linewidth=2.5, color=color, 
               markersize=8, markeredgecolor='white', markeredgewidth=1.5)
        ax.fill(angles, normalized_values, alpha=0.25, color=color)
        
        # Personnalisation
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(stats[:-1], size=9)
        ax.set_ylim(0, 100)
        ax.set_yticks([25, 50, 75, 100])
        ax.set_yticklabels(['25%', '50%', '75%', '100%'], size=8)
        ax.grid(True, linestyle='--', alpha=0.7)
        
        # Titre avec description
        description = self.stat_categories[category]['description']
        plt.title(f'⭕ {self.player_name} - {category}\n{description}\n{self.position}', 
                 size=16, weight='bold', pad=20)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight', facecolor='white')
            self._log(f"✅ Graphique sauvegardé : {save_path}", "SUCCESS")
        
        plt.show()
    
    def plot_multi_aspect_comparison(self, figsize: Tuple[int, int] = (16, 12),
                                    save_path: str = None):
        """
        📊 COMPARAISON MULTI-ASPECTS - Vue d'ensemble tactique complète
        Grille de radars pour chaque aspect du jeu
        """
        if self.df is None:
            self._log("Aucune donnée chargée", "ERROR")
            return
        
        self._log("📊 Création de la comparaison multi-aspects...")
        
        categories = list(self.stat_categories.keys())
        n_categories = len(categories)
        
        # Créer une grille de sous-graphiques
        n_rows = (n_categories + 2) // 3
        n_cols = 3
        
        fig = plt.figure(figsize=figsize)
        
        for idx, category in enumerate(categories, 1):
            cat_df = self._get_category_stats(category)
            
            if cat_df.empty:
                continue
            
            # Créer le sous-graphique polaire
            ax = fig.add_subplot(n_rows, n_cols, idx, projection='polar')
            
            # Préparer les données
            stats = cat_df['Statistic'].tolist()[:8]  # Limiter à 8 stats
            values = cat_df['Per_90'].tolist()[:8]
            
            if not stats:
                continue
            
            # Normaliser
            max_val = max(values) if max(values) > 0 else 1
            normalized = [(v / max_val * 100) for v in values]
            
            # Fermer
            stats += stats[:1]
            normalized += normalized[:1]
            
            angles = np.linspace(0, 2 * np.pi, len(stats) - 1, endpoint=False).tolist()
            angles += angles[:1]
            
            # Couleur
            color = self.stat_categories[category]['color']
            
            # Tracer
            ax.plot(angles, normalized, 'o-', linewidth=2, color=color, 
                   markersize=5, markeredgecolor='white', markeredgewidth=1)
            ax.fill(angles, normalized, alpha=0.2, color=color)
            
            # Personnalisation
            ax.set_xticks(angles[:-1])
            ax.set_xticklabels(stats[:-1], size=7)
            ax.set_ylim(0, 100)
            ax.set_yticks([50, 100])
            ax.set_yticklabels(['50', '100'], size=6)
            ax.grid(True, linestyle='--', alpha=0.5)
            
            ax.set_title(category, size=12, weight='bold', pad=10, color=color)
        
        # Titre principal
        fig.suptitle(f'📊 {self.player_name} - Vue Tactique Complète\n{self.position}', 
                    fontsize=18, weight='bold', y=0.98)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight', facecolor='white')
            self._log(f"✅ Graphique sauvegardé : {save_path}", "SUCCESS")
        
        plt.show()
    
    def plot_category_bars(self, category: str, figsize: Tuple[int, int] = (12, 8),
                          save_path: str = None):
        """
        📊 BARRES HORIZONTALES - Détail d'une catégorie tactique
        
        Args:
            category: Catégorie à analyser
            figsize: Taille de la figure
            save_path: Chemin pour sauvegarder
        """
        if self.df is None:
            self._log("Aucune donnée chargée", "ERROR")
            return
        
        cat_df = self._get_category_stats(category)
        
        if cat_df.empty:
            self._log(f"Aucune donnée pour '{category}'", "WARNING")
            return
        
        self._log(f"📊 Création du graphique en barres pour {category}...")
        
        # Trier par valeur
        cat_df = cat_df.sort_values('Per_90', ascending=True)
        
        # Créer le graphique
        fig, ax = plt.subplots(figsize=figsize)
        
        # Couleur de la catégorie
        color = self.stat_categories[category]['color']
        
        # Créer un gradient de couleur basé sur les valeurs
        values = cat_df['Per_90'].values
        colors = plt.cm.RdYlGn(values / values.max()) if values.max() > 0 else [color] * len(values)
        
        # Barres horizontales
        bars = ax.barh(cat_df['Statistic'], cat_df['Per_90'], color=colors, 
                      edgecolor='black', linewidth=0.5)
        
        # Ajouter les valeurs
        for bar in bars:
            width = bar.get_width()
            ax.text(width, bar.get_y() + bar.get_height()/2, 
                   f'{width:.2f}', ha='left', va='center', fontsize=9, 
                   weight='bold', color='black')
        
        # Personnalisation
        description = self.stat_categories[category]['description']
        ax.set_title(f'📊 {self.player_name} - {category}\n{description}\n{self.position}', 
                    fontsize=16, weight='bold', pad=15)
        ax.set_xlabel('Valeur par 90 minutes', fontsize=12, weight='bold')
        ax.grid(axis='x', alpha=0.3, linestyle='--')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight', facecolor='white')
            self._log(f"✅ Graphique sauvegardé : {save_path}", "SUCCESS")
        
        plt.show()
    
    def generate_tactical_report(self, output_dir: str = './tactical_analysis'):
        """
        📁 RAPPORT TACTIQUE COMPLET - Génère tous les graphiques d'analyse
        
        Args:
            output_dir: Dossier de sortie
        """
        import os
        
        if self.df is None:
            self._log("Aucune donnée chargée", "ERROR")
            return
        
        os.makedirs(output_dir, exist_ok=True)
        
        self._log("="*80)
        self._log(f"📁 GÉNÉRATION DU RAPPORT TACTIQUE : {self.player_name}", "START")
        self._log("="*80)
        
        safe_name = self.player_name.replace(' ', '_').replace('-', '_')
        
        # 1. Spider radar global
        self._log("\n1️⃣  Spider radar global...")
        self.plot_spider_radar(save_path=f'{output_dir}/{safe_name}_spider.png')
        
        # 2. Heatmap tactique
        self._log("\n2️⃣  Heatmap tactique...")
        self.plot_tactical_heatmap(save_path=f'{output_dir}/{safe_name}_heatmap.png')
        
        # 3. Vue multi-aspects
        self._log("\n3️⃣  Vue multi-aspects...")
        self.plot_multi_aspect_comparison(save_path=f'{output_dir}/{safe_name}_multi_aspects.png')
        
        # 4. Graphiques polaires pour chaque catégorie
        self._log("\n4️⃣  Graphiques polaires par catégorie...")
        for category in self.stat_categories.keys():
            self.plot_polar_category(category, 
                                    save_path=f'{output_dir}/{safe_name}_{category.lower()}_polar.png')
        
        # 5. Barres horizontales pour chaque catégorie
        self._log("\n5️⃣  Graphiques en barres par catégorie...")
        for category in self.stat_categories.keys():
            self.plot_category_bars(category, 
                                   save_path=f'{output_dir}/{safe_name}_{category.lower()}_bars.png')
        
        self._log("\n" + "="*80)
        self._log(f"✅ RAPPORT TACTIQUE COMPLET GÉNÉRÉ dans : {output_dir}", "SUCCESS")
        self._log("="*80)
        
        # Résumé des fichiers générés
        print(f"\n📂 Fichiers générés :")
        print(f"  • {safe_name}_spider.png - Spider radar global")
        print(f"  • {safe_name}_heatmap.png - Heatmap tactique")
        print(f"  • {safe_name}_multi_aspects.png - Vue multi-aspects")
        for category in self.stat_categories.keys():
            print(f"  • {safe_name}_{category.lower()}_polar.png - Analyse {category}")
            print(f"  • {safe_name}_{category.lower()}_bars.png - Détail {category}")
    
    def print_tactical_summary(self):
        """
        📝 RÉSUMÉ TACTIQUE TEXTUEL - Analyse par catégorie
        """
        if self.df is None:
            self._log("Aucune donnée chargée", "ERROR")
            return
        
        print("\n" + "="*80)
        print(f"📝 RÉSUMÉ TACTIQUE : {self.player_name}")
        print("="*80)
        print(f"Position : {self.position}")
        print(f"Stats totales : {len(self.df)}")
        
        print("\n" + "─"*80)
        print("ANALYSE PAR ASPECT TACTIQUE")
        print("─"*80)
        
        for category, info in self.stat_categories.items():
            cat_df = self._get_category_stats(category)
            
            if cat_df.empty:
                continue
            
            print(f"\n🎯 {category.upper()}")
            print(f"   {info['description']}")
            print(f"   Stats disponibles : {len(cat_df)}")
            
            if 'Per_90' in cat_df.columns:
                mean_val = cat_df['Per_90'].mean()
                max_val = cat_df['Per_90'].max()
                print(f"   Moyenne : {mean_val:.2f} par 90")
                print(f"   Maximum : {max_val:.2f} par 90")
                
                # Top 3 stats de la catégorie
                top3 = cat_df.nlargest(3, 'Per_90')
                print(f"   Top 3 :")
                for idx, row in top3.iterrows():
                    print(f"      • {row['Statistic']:<40} : {row['Per_90']:.2f}")
        
        print("\n" + "="*80)
    
    def analyze_player_profile_ai(self, save_path: str = None):
        """
        🤖 ANALYSE IA DU PROFIL - Identification du style de jeu via clustering
        Utilise K-Means pour identifier le profil tactique dominant
        """
        if not SKLEARN_AVAILABLE:
            self._log("scikit-learn requis pour l'analyse IA", "ERROR")
            return None
        
        if self.df is None:
            self._log("Aucune donnée chargée", "ERROR")
            return None
        
        self._log("🤖 Analyse IA du profil tactique...")
        
        # Calculer les scores par catégorie
        category_scores = {}
        for cat in self.stat_categories.keys():
            cat_df = self._get_category_stats(cat)
            if not cat_df.empty and 'Per_90' in cat_df.columns:
                values = cat_df['Per_90'].dropna()
                if len(values) > 0:
                    category_scores[cat] = values.mean()
        
        if len(category_scores) < 3:
            self._log("Pas assez de données pour l'analyse IA", "WARNING")
            return None
        
        # Créer un vecteur de features
        features = np.array(list(category_scores.values())).reshape(1, -1)
        
        # Normaliser
        scaler = StandardScaler()
        features_scaled = scaler.fit_transform(features)
        
        # Identifier les 3 points forts et 3 points faibles
        sorted_cats = sorted(category_scores.items(), key=lambda x: x[1], reverse=True)
        strengths = sorted_cats[:3]
        weaknesses = sorted_cats[-3:]
        
        # Visualisation
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 7), facecolor='white')
        
        # Graphique 1: Forces vs Faiblesses
        categories = list(category_scores.keys())
        scores = list(category_scores.values())
        colors = ['#27ae60' if s > np.median(scores) else '#e74c3c' for s in scores]
        
        ax1.barh(categories, scores, color=colors, edgecolor='black', linewidth=1.5)
        ax1.axvline(np.median(scores), color='black', linestyle='--', linewidth=2, label='Médiane')
        ax1.set_xlabel('Score moyen (Per 90)', fontsize=13, weight='bold')
        ax1.set_title(f'🎯 {self.player_name} - Points Forts vs Faiblesses\nAnalyse IA', 
                     fontsize=16, weight='bold', pad=15)
        ax1.legend(fontsize=11)
        ax1.grid(axis='x', alpha=0.3)
        
        # Graphique 2: Distribution des compétences
        ax2.scatter(range(len(scores)), scores, s=300, c=colors, edgecolor='black', 
                   linewidth=2, alpha=0.7, zorder=3)
        
        # Tendance
        z = np.polyfit(range(len(scores)), scores, 2)
        p = np.poly1d(z)
        x_line = np.linspace(0, len(scores)-1, 100)
        ax2.plot(x_line, p(x_line), "--", color='blue', linewidth=2, alpha=0.5, label='Tendance')
        
        ax2.set_xticks(range(len(categories)))
        ax2.set_xticklabels(categories, rotation=45, ha='right')
        ax2.set_ylabel('Score (Per 90)', fontsize=13, weight='bold')
        ax2.set_title('📊 Distribution des Compétences Tactiques', fontsize=16, weight='bold', pad=15)
        ax2.legend(fontsize=11)
        ax2.grid(alpha=0.3)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight', facecolor='white')
            self._log(f"✅ Analyse IA sauvegardée : {save_path}", "SUCCESS")
        else:
            plt.show()
        
        plt.close()
        
        # Résumé textuel
        print("\n" + "="*80)
        print(f"🤖 ANALYSE IA DU PROFIL : {self.player_name}")
        print("="*80)
        
        print("\n💪 TOP 3 POINTS FORTS :")
        for i, (cat, score) in enumerate(strengths, 1):
            print(f"  {i}. {cat:<20} : {score:.2f} per 90  ⭐")
        
        print("\n⚠️  TOP 3 AXES D'AMÉLIORATION :")
        for i, (cat, score) in enumerate(weaknesses, 1):
            print(f"  {i}. {cat:<20} : {score:.2f} per 90")
        
        print("\n📊 PROFIL TACTIQUE IDENTIFIÉ :")
        # Identifier le profil
        if strengths[0][0] in ['Shooting', 'Creation']:
            profile = "🎯 CRÉATEUR OFFENSIF - Focus sur les actions décisives"
        elif strengths[0][0] in ['Passing', 'Possession']:
            profile = "🎭 MENEUR DE JEU - Maître de la circulation du ballon"
        elif strengths[0][0] in ['Defense', 'Discipline']:
            profile = "🛡️  SENTINELLE DÉFENSIVE - Solidité et récupération"
        elif strengths[0][0] == 'Progression':
            profile = "⚡ TRANSPORTEUR - Progression rapide vers l'avant"
        else:
            profile = "⚖️  PROFIL ÉQUILIBRÉ - Polyvalence tactique"
        
        print(f"  {profile}")
        print(f"\n  Score de spécialisation : {(strengths[0][1] / np.mean(scores) - 1) * 100:.1f}%")
        print("="*80)
        
        return {
            'strengths': strengths,
            'weaknesses': weaknesses,
            'profile': profile,
            'scores': category_scores
        }
    
    def plot_advanced_comparison(self, figsize: Tuple[int, int] = (20, 12), 
                                save_path: str = None):
        """
        📈 VISUALISATION AVANCÉE - Analyse multi-dimensionnelle premium
        Combine plusieurs types de visualisation pour une analyse complète
        """
        if self.df is None:
            self._log("Aucune donnée chargée", "ERROR")
            return
        
        self._log("📈 Création de la visualisation avancée multi-dimensionnelle...")
        
        # Calculer les scores
        category_scores = {}
        for cat in self.stat_categories.keys():
            cat_df = self._get_category_stats(cat)
            if not cat_df.empty and 'Per_90' in cat_df.columns:
                values = cat_df['Per_90'].dropna()
                if len(values) > 0:
                    category_scores[cat] = values.mean()
        
        if not category_scores:
            self._log("Pas de données disponibles", "WARNING")
            return
        
        # Créer la figure avec 6 subplots
        fig = plt.figure(figsize=figsize, facecolor='#f5f5f5')
        gs = fig.add_gridspec(3, 3, hspace=0.35, wspace=0.3)
        
        categories = list(category_scores.keys())
        scores = list(category_scores.values())
        colors = [self.stat_categories[cat]['color'] for cat in categories]
        
        # 1. Radar principal (grand)
        ax1 = fig.add_subplot(gs[0:2, 0:2], projection='polar')
        angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
        scores_plot = scores + scores[:1]
        angles_plot = angles + angles[:1]
        
        ax1.plot(angles_plot, scores_plot, 'o-', linewidth=4, markersize=12, 
                color='#2c3e50', markeredgecolor='white', markeredgewidth=3)
        ax1.fill(angles_plot, scores_plot, alpha=0.25, color='#3498db')
        ax1.set_xticks(angles)
        ax1.set_xticklabels(categories, size=13, weight='bold')
        ax1.set_title(f'🕷️ Profil Radar Complet\n{self.player_name}', 
                     size=16, weight='bold', pad=20, color='#1a1a2e')
        ax1.grid(True, linestyle='--', alpha=0.5)
        
        # 2. Barres horizontales avec gradient
        ax2 = fig.add_subplot(gs[0, 2])
        sorted_indices = np.argsort(scores)
        sorted_cats = [categories[i] for i in sorted_indices]
        sorted_scores = [scores[i] for i in sorted_indices]
        sorted_colors = [colors[i] for i in sorted_indices]
        
        bars = ax2.barh(sorted_cats, sorted_scores, color=sorted_colors, 
                       edgecolor='black', linewidth=1.2, alpha=0.8)
        ax2.set_title('📊 Classement', size=12, weight='bold', pad=10)
        ax2.set_xlabel('Score', size=10, weight='bold')
        ax2.grid(axis='x', alpha=0.3)
        
        # 3. Distribution en boîte à moustaches
        ax3 = fig.add_subplot(gs[1, 2])
        bp = ax3.boxplot([scores], vert=False, patch_artist=True,
                         widths=0.6, showmeans=True,
                         boxprops=dict(facecolor='lightblue', edgecolor='black', linewidth=2),
                         medianprops=dict(color='red', linewidth=3),
                         meanprops=dict(marker='D', markerfacecolor='green', markersize=10))
        ax3.set_title('📦 Distribution Statistique', size=12, weight='bold', pad=10)
        ax3.set_xlabel('Score', size=10, weight='bold')
        ax3.set_yticklabels(['Toutes\ncatégories'])
        ax3.grid(axis='x', alpha=0.3)
        
        # 4. Heatmap de corrélation (matrice 1D)
        ax4 = fig.add_subplot(gs[2, :2])
        scores_matrix = np.array(scores).reshape(1, -1)
        im = ax4.imshow(scores_matrix, cmap='RdYlGn', aspect='auto', 
                       vmin=min(scores), vmax=max(scores))
        ax4.set_xticks(range(len(categories)))
        ax4.set_xticklabels(categories, rotation=45, ha='right', size=11)
        ax4.set_yticks([])
        ax4.set_title('🔥 Heatmap des Performances', size=13, weight='bold', pad=10)
        
        # Ajouter les valeurs sur la heatmap
        for i, (cat, score) in enumerate(zip(categories, scores)):
            ax4.text(i, 0, f'{score:.1f}', ha='center', va='center', 
                    color='white' if score < np.median(scores) else 'black',
                    fontsize=11, weight='bold')
        
        # Colorbar
        cbar = plt.colorbar(im, ax=ax4, orientation='horizontal', pad=0.1, aspect=30)
        cbar.set_label('Intensité de performance', size=10, weight='bold')
        
        # 5. Indicateurs clés (texte)
        ax5 = fig.add_subplot(gs[2, 2])
        ax5.axis('off')
        
        stats_text = f"""
        📊 STATISTIQUES CLÉS
        
        • Moyenne : {np.mean(scores):.2f}
        • Médiane : {np.median(scores):.2f}
        • Écart-type : {np.std(scores):.2f}
        • Min : {min(scores):.2f}
        • Max : {max(scores):.2f}
        
        🎯 COHÉRENCE
        CV: {(np.std(scores)/np.mean(scores)*100):.1f}%
        
        ⭐ MEILLEUR
        {categories[np.argmax(scores)]}
        """
        
        ax5.text(0.1, 0.9, stats_text, transform=ax5.transAxes, 
                fontsize=10, verticalalignment='top', family='monospace',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
        # Titre principal
        fig.suptitle(f'📈 {self.player_name} - Dashboard Tactique Avancé | {self.position}', 
                    fontsize=20, weight='bold', y=0.98, color='#1a1a2e')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight', facecolor='#f5f5f5')
            self._log(f"✅ Dashboard avancé sauvegardé : {save_path}", "SUCCESS")
        else:
            plt.show()
        
        plt.close()


# Exemple d'utilisation
if __name__ == "__main__":
    print("Test du PlayerAnalyzer V2 avec données simulées...\n")
    
    # Données simulées
    data = {
        'Statistic': ['Goals', 'Assists', 'Shots Total', 'Shots on Target', 
                     'Passes Completed', 'Pass Completion %', 'Key Passes',
                     'Tackles', 'Interceptions', 'Blocks', 'Clearances',
                     'Touches', 'Carries', 'Successful Take-Ons',
                     'Progressive Passes', 'Progressive Carries',
                     'Shot-Creating Actions', 'Goal-Creating Actions',
                     'Yellow Cards', 'Fouls Committed'],
        'Per_90': [0.5, 0.3, 2.1, 0.8, 92.3, 94.5, 0.6, 3.9, 0.87, 1.88, 0.2,
                  108.2, 5.3, 1.59, 6.5, 1.73, 2.31, 0.14, 0.58, 1.2]
    }
    
    df = pd.DataFrame(data)
    
    # Créer l'analyseur
    analyzer = PlayerAnalyzer(player_name='Marco Verratti', position='MF')
    analyzer.load_data(df)
    
    # Résumé tactique
    analyzer.print_tactical_summary()
    
    # Générer un graphique test
    print("\n🎨 Génération d'un graphique test...")
    # analyzer.plot_spider_radar()
    # analyzer.plot_polar_category('Passing')