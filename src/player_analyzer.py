"""
PlayerAnalyzer V5 - Visualisations avec normalisation intelligente
Harmonisation des échelles pour une meilleure lisibilité
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Optional
import warnings
warnings.filterwarnings('ignore')

plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans']
plt.rcParams['figure.facecolor'] = 'white'
plt.rcParams['axes.facecolor'] = '#f8f9fa'


class PlayerAnalyzer:
    """Analyseur tactique avec normalisation intelligente des échelles"""
    
    # Catégories avec stats réelles des données
    CATEGORIES = {
        'Passing': {
            'stats': ['Passes Completed', 'Progressive Passes', 'Passes into Final Third', 'Key Passes', 'xA: Expected Assists'],
            'scales': [100, 10, 10, 2, 0.5]  # Valeurs de référence pour normalisation
        },
        'Shooting': {
            'stats': ['Goals', 'Shots Total', 'Shots on Target', 'xG: Expected Goals', 'npxG: Non-Penalty xG'],
            'scales': [1, 5, 3, 0.5, 0.5]
        },
        'Creation': {
            'stats': ['Assists', 'Shot-Creating Actions', 'Goal-Creating Actions', 'Through Balls', 'Passes into Penalty Area'],
            'scales': [0.5, 5, 1, 0.5, 2]
        },
        'Defense': {
            'stats': ['Tackles', 'Tackles Won', 'Interceptions', 'Blocks', 'Ball Recoveries'],
            'scales': [5, 3, 2, 2, 10]
        },
        'Possession': {
            'stats': ['Touches', 'Carries', 'Progressive Carries', 'Successful Take-Ons', 'Carries into Final Third'],
            'scales': [120, 100, 5, 2, 5]
        }
    }
    
    COLORS = {
        'primary': '#2E86AB',
        'secondary': '#A23B72',
        'success': '#06A77D',
        'warning': '#F18F01',
        'danger': '#C73E1D',
        'gradient': ['#2E86AB', '#06A77D', '#F18F01', '#A23B72', '#C73E1D']
    }
    
    def __init__(self, player_name: str, position: str):
        self.player_name = player_name
        self.position = position
        self.df = None
        self.stats = {}
        
    def load_data(self, df: pd.DataFrame):
        """Charge les données"""
        self.df = df
        # Convertir toutes les colonnes en float si possible
        for col in df.columns:
            try:
                self.stats[col] = float(df[col].iloc[0])
            except:
                self.stats[col] = df[col].iloc[0]
    
    def _get_stat_value(self, stat_name: str) -> float:
        """Récupère la valeur d'une stat (recherche flexible)"""
        # Recherche exacte
        if stat_name in self.stats:
            return self.stats[stat_name]
        
        # Recherche partielle
        stat_lower = stat_name.lower()
        for key, value in self.stats.items():
            if stat_lower in key.lower():
                return value
        
        return 0.0
    
    def _normalize_stat(self, value: float, reference: float) -> float:
        """Normalise une stat sur une échelle 0-100 selon une référence"""
        if reference == 0:
            return 0
        # Normalisation: (valeur / référence) * 100, plafonné à 100
        normalized = (value / reference) * 100
        return min(normalized, 100)
    
    def _get_category_stats_normalized(self, category: str) -> Dict[str, tuple]:
        """Récupère les stats normalisées d'une catégorie"""
        cat_data = self.CATEGORIES.get(category, {})
        stats_list = cat_data.get('stats', [])
        scales = cat_data.get('scales', [])
        
        result = {}
        for stat_name, scale in zip(stats_list, scales):
            raw_value = self._get_stat_value(stat_name)
            normalized = self._normalize_stat(raw_value, scale)
            result[stat_name] = (raw_value, normalized)
        
        return result
    
    def _get_category_average_normalized(self, category: str) -> float:
        """Moyenne normalisée d'une catégorie (0-100)"""
        stats = self._get_category_stats_normalized(category)
        if not stats:
            return 0
        normalized_values = [v[1] for v in stats.values()]
        return np.mean(normalized_values)
    
    def plot_spider_radar(self, save_path: Optional[str] = None):
        """Spider radar NORMALISÉ - Échelle 0-100 pour toutes les catégories"""
        categories = list(self.CATEGORIES.keys())
        values_normalized = [self._get_category_average_normalized(cat) for cat in categories]
        
        angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
        values_normalized += values_normalized[:1]
        angles += angles[:1]
        
        fig = plt.figure(figsize=(12, 12), facecolor='white')
        ax = fig.add_subplot(111, projection='polar', facecolor='#f8f9fa')
        
        # Tracer
        ax.plot(angles, values_normalized, 'o-', linewidth=4, color=self.COLORS['primary'], 
                markersize=14, markeredgecolor='white', markeredgewidth=3, zorder=3)
        ax.fill(angles, values_normalized, alpha=0.35, color=self.COLORS['primary'], zorder=2)
        
        # Échelle fixe 0-100
        ax.set_ylim(0, 100)
        ax.set_yticks([20, 40, 60, 80, 100])
        ax.set_yticklabels(['20', '40', '60', '80', '100'], size=11, color='#666', weight='bold')
        
        # Grille colorée
        for ytick in [20, 40, 60, 80, 100]:
            circle = plt.Circle((0, 0), ytick, transform=ax.transData._b, 
                              fill=False, edgecolor='#ddd', linewidth=2, zorder=1)
            ax.add_artist(circle)
        
        # Labels
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(categories, size=15, weight='bold', color='#333')
        
        # Valeurs sur les points
        for angle, value in zip(angles[:-1], values_normalized[:-1]):
            # Couleur selon performance
            color = self.COLORS['success'] if value >= 70 else self.COLORS['warning'] if value >= 50 else self.COLORS['danger']
            ax.text(angle, value + 8, f'{value:.0f}', 
                   ha='center', va='center', size=13, weight='bold',
                   bbox=dict(boxstyle='round,pad=0.6', facecolor='white', 
                            edgecolor=color, linewidth=2.5))
        
        # Zones de performance
        ax.fill_between(angles, 0, 50, alpha=0.05, color='red', zorder=0)
        ax.fill_between(angles, 50, 70, alpha=0.05, color='orange', zorder=0)
        ax.fill_between(angles, 70, 100, alpha=0.05, color='green', zorder=0)
        
        plt.title(f'{self.player_name}\nProfil Tactique Global (Normalisé)', 
                 size=20, weight='bold', pad=40, color='#222')
        
        fig.text(0.5, 0.92, f'Position: {self.position} | Échelle: 0-100 (normalisée)', 
                ha='center', size=12, color='#666', style='italic')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight', facecolor='white')
        plt.close()
    
    def plot_category_details(self, category: str, save_path: Optional[str] = None):
        """Détail d'une catégorie avec valeurs réelles ET normalisées"""
        stats_data = self._get_category_stats_normalized(category)
        
        if not stats_data:
            return
        
        stat_names = list(stats_data.keys())
        raw_values = [v[0] for v in stats_data.values()]
        normalized_values = [v[1] for v in stats_data.values()]
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6), facecolor='white')
        
        # Graphique 1: Valeurs réelles
        colors1 = [self.COLORS['primary']] * len(stat_names)
        bars1 = ax1.barh(stat_names, raw_values, color=colors1, edgecolor='white', linewidth=2, alpha=0.85)
        
        for bar, val in zip(bars1, raw_values):
            ax1.text(val + max(raw_values) * 0.02, bar.get_y() + bar.get_height()/2, 
                    f'{val:.2f}', va='center', ha='left', size=11, weight='bold')
        
        ax1.set_xlabel('Valeur Réelle (Per 90)', size=13, weight='bold', color='#333')
        ax1.set_title(f'{category} - Valeurs Réelles', size=15, weight='bold', pad=15)
        ax1.spines['top'].set_visible(False)
        ax1.spines['right'].set_visible(False)
        ax1.grid(axis='x', alpha=0.2, linestyle='--')
        ax1.set_facecolor('#f8f9fa')
        
        # Graphique 2: Valeurs normalisées
        colors2 = [self.COLORS['success'] if v >= 70 else self.COLORS['warning'] if v >= 50 else self.COLORS['danger'] 
                   for v in normalized_values]
        bars2 = ax2.barh(stat_names, normalized_values, color=colors2, edgecolor='white', linewidth=2, alpha=0.85)
        
        for bar, val in zip(bars2, normalized_values):
            ax2.text(val + 3, bar.get_y() + bar.get_height()/2, 
                    f'{val:.0f}', va='center', ha='left', size=11, weight='bold')
        
        ax2.set_xlabel('Score Normalisé (0-100)', size=13, weight='bold', color='#333')
        ax2.set_title(f'{category} - Performance Normalisée', size=15, weight='bold', pad=15)
        ax2.set_xlim(0, 110)
        ax2.axvline(50, color='gray', linestyle='--', alpha=0.5, linewidth=2)
        ax2.axvline(70, color='green', linestyle='--', alpha=0.5, linewidth=2)
        ax2.spines['top'].set_visible(False)
        ax2.spines['right'].set_visible(False)
        ax2.grid(axis='x', alpha=0.2, linestyle='--')
        ax2.set_facecolor('#f8f9fa')
        
        plt.suptitle(f'{self.player_name} - Analyse {category}', size=17, weight='bold', y=1.02)
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight', facecolor='white')
        plt.close()
    
    def plot_all_categories_comparison(self, save_path: Optional[str] = None):
        """Comparaison des 5 catégories avec scores normalisés"""
        categories = list(self.CATEGORIES.keys())
        normalized_scores = [self._get_category_average_normalized(cat) for cat in categories]
        
        # Trier
        sorted_data = sorted(zip(categories, normalized_scores), key=lambda x: x[1], reverse=True)
        categories, normalized_scores = zip(*sorted_data)
        
        fig, ax = plt.subplots(figsize=(14, 8), facecolor='white')
        ax.set_facecolor('#f8f9fa')
        
        # Couleurs selon performance
        colors = [self.COLORS['success'] if v >= 70 else self.COLORS['warning'] if v >= 50 else self.COLORS['danger'] 
                  for v in normalized_scores]
        
        bars = ax.barh(categories, normalized_scores, height=0.7, color=colors, 
                      edgecolor='white', linewidth=3, alpha=0.9)
        
        # Annotations
        for bar, val in zip(bars, normalized_scores):
            emoji = '🟢' if val >= 70 else '🟡' if val >= 50 else '🔴'
            ax.text(val + 3, bar.get_y() + bar.get_height()/2, 
                   f'{emoji} {val:.0f}', va='center', ha='left', size=14, weight='bold')
        
        # Lignes de référence
        ax.axvline(50, color='gray', linestyle='--', alpha=0.4, linewidth=2, label='Seuil Acceptable')
        ax.axvline(70, color='green', linestyle='--', alpha=0.4, linewidth=2, label='Seuil Excellent')
        
        ax.set_xlabel('Score Normalisé (0-100)', size=14, weight='bold', color='#333')
        ax.set_xlim(0, 110)
        ax.set_title(f'{self.player_name} - Évaluation Globale par Catégorie\n', 
                    size=18, weight='bold', pad=20, color='#222')
        
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_linewidth(2)
        ax.spines['bottom'].set_linewidth(2)
        ax.grid(axis='x', alpha=0.2, linestyle='--', linewidth=1.5)
        ax.legend(loc='lower right', fontsize=10)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight', facecolor='white')
        plt.close()
    
    def plot_top_stats_absolute(self, top_n: int = 12, save_path: Optional[str] = None):
        """Top stats avec valeurs ABSOLUES (non normalisées)"""
        # Filtrer les stats numériques pertinentes
        relevant_stats = {}
        for key, value in self.stats.items():
            if isinstance(value, (int, float)) and value > 0:
                # Exclure les métadonnées
                if key not in ['minutes_played', 'age', 'birth_date', 'season']:
                    relevant_stats[key] = value
        
        sorted_stats = sorted(relevant_stats.items(), key=lambda x: x[1], reverse=True)[:top_n]
        
        stat_names = [s[0][:40] for s in sorted_stats]
        stat_values = [s[1] for s in sorted_stats]
        
        fig, ax = plt.subplots(figsize=(14, 10), facecolor='white')
        ax.set_facecolor('#f8f9fa')
        
        colors = plt.cm.viridis(np.linspace(0.2, 0.9, len(stat_names)))
        
        bars = ax.barh(stat_names, stat_values, height=0.75, color=colors, 
                      edgecolor='white', linewidth=2.5, alpha=0.9)
        
        for bar, val in zip(bars, stat_values):
            ax.text(val + max(stat_values) * 0.01, bar.get_y() + bar.get_height()/2, 
                   f'{val:.2f}', va='center', ha='left', size=11, weight='bold', color='#333')
        
        ax.set_xlabel('Valeur (Per 90)', size=14, weight='bold', color='#333')
        ax.set_xlim(0, max(stat_values) * 1.15)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_linewidth(2)
        ax.spines['bottom'].set_linewidth(2)
        ax.grid(axis='x', alpha=0.2, linestyle='--', linewidth=1.5)
        
        plt.title(f'{self.player_name} - Top {top_n} Statistiques (Valeurs Absolues)\n', 
                 size=18, weight='bold', pad=20, color='#222')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight', facecolor='white')
        plt.close()
    
    def plot_performance_matrix(self, save_path: Optional[str] = None):
        """Matrice de performance - Vue d'ensemble normalisée"""
        matrix_data = []
        row_labels = []
        col_labels = []
        
        for category, cat_info in self.CATEGORIES.items():
            stats_data = self._get_category_stats_normalized(category)
            if stats_data:
                row = [v[1] for v in stats_data.values()]  # Valeurs normalisées
                matrix_data.append(row)
                row_labels.append(category)
                if not col_labels:
                    col_labels = [s[:20] for s in stats_data.keys()]
        
        # Uniformiser la longueur
        max_len = max(len(row) for row in matrix_data)
        for row in matrix_data:
            while len(row) < max_len:
                row.append(0)
        
        fig, ax = plt.subplots(figsize=(15, 8), facecolor='white')
        
        im = ax.imshow(matrix_data, cmap='RdYlGn', aspect='auto', vmin=0, vmax=100)
        
        ax.set_yticks(range(len(row_labels)))
        ax.set_yticklabels(row_labels, size=13, weight='bold')
        ax.set_xticks(range(max_len))
        ax.set_xticklabels([col_labels[i] if i < len(col_labels) else '' for i in range(max_len)], 
                          rotation=45, ha='right', size=10)
        
        # Annotations
        for i in range(len(matrix_data)):
            for j in range(len(matrix_data[i])):
                val = matrix_data[i][j]
                if val > 0:
                    text_color = 'white' if val < 50 else 'black'
                    ax.text(j, i, f'{val:.0f}', ha='center', va='center',
                           size=11, weight='bold', color=text_color)
        
        cbar = plt.colorbar(im, ax=ax, pad=0.02)
        cbar.set_label('Score Normalisé (0-100)', size=12, weight='bold')
        
        plt.title(f'{self.player_name} - Matrice de Performance Normalisée\n', 
                 size=18, weight='bold', pad=20, color='#222')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight', facecolor='white')
        plt.close()
    
    def print_tactical_summary(self):
        """Résumé textuel avec scores normalisés"""
        print(f"\n{'='*80}")
        print(f"  🎯 PROFIL TACTIQUE - {self.player_name} ({self.position})")
        print(f"{'='*80}\n")
        
        for category in self.CATEGORIES.keys():
            score = self._get_category_average_normalized(category)
            
            # Barre de progression
            bar_length = int(score / 2)
            bar = '█' * bar_length + '░' * (50 - bar_length)
            
            # Emoji selon performance
            if score >= 70:
                emoji = '🟢'
                label = 'EXCELLENT'
            elif score >= 50:
                emoji = '🟡'
                label = 'BON'
            else:
                emoji = '🔴'
                label = 'À AMÉLIORER'
            
            print(f"  {emoji} {category:<12} {bar} {score:>5.0f}/100  [{label}]")
        
        print(f"\n{'='*80}")
        print(f"  📊 Légende: 🟢 ≥70 (Excellent) | 🟡 50-69 (Bon) | 🔴 <50 (À améliorer)")
        print(f"{'='*80}\n")