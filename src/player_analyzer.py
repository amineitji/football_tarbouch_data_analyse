"""
PlayerAnalyzer V10 - Style avec dégradé + fond complet
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.colors import LinearSegmentedColormap
import seaborn as sns
from typing import Dict, List, Optional
import warnings
warnings.filterwarnings('ignore')

plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans', 'Helvetica']


class PlayerAnalyzer:
    """Analyseur tactique avec style dégradé blanc-pastel"""
    
    CATEGORIES = {
        'Passing': {
            'stats': ['Passes Completed', 'Progressive Passes', 'Passes into Final Third', 'Key Passes', 'xA: Expected Assists'],
            'scales': [100, 10, 10, 2, 0.5]
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
        'gradient_start': "#000000",
        'gradient_end': "#646327",
        'points': '#FF0000',
        'text': '#FFFFFF',
        'edge': '#000000'
    }
    
    def __init__(self, player_name: str, position: str):
        self.player_name = player_name
        self.position = position
        self.df = None
        self.stats = {}
        self.season = None
        self.competition = None
        
    def load_data(self, df: pd.DataFrame):
        """Charge les données"""
        self.df = df
        for col in df.columns:
            try:
                self.stats[col] = float(df[col].iloc[0])
            except:
                self.stats[col] = df[col].iloc[0]
        
        if 'season' in df.columns:
            self.season = df['season'].iloc[0]
        if 'competition' in df.columns:
            self.competition = df['competition'].iloc[0]
    
    def _create_gradient_background(self, fig):
        """Crée un fond en dégradé vertical"""
        gradient = np.linspace(0, 1, 256).reshape(-1, 1)
        gradient = np.hstack((gradient, gradient))
        
        cmap = LinearSegmentedColormap.from_list("", 
            [self.COLORS['gradient_start'], self.COLORS['gradient_end']])
        
        ax_bg = fig.add_axes([0, 0, 1, 1])
        ax_bg.axis('off')
        ax_bg.imshow(gradient, aspect='auto', cmap=cmap, extent=[0, 1, 0, 1], zorder=-1)
    
    def _customize_axes(self, ax):
        """Personnalise les axes avec contours blancs épais"""
        for spine in ax.spines.values():
            spine.set_edgecolor('white')
            spine.set_linewidth(2.5)
    
    def _add_watermark(self, fig):
        """Ajoute le watermark @TarbouchData en grand et visible"""
        fig.text(0.98, 0.02, '@TarbouchData', 
                fontsize=20, color='white', fontweight='bold', 
                ha='right', va='bottom', alpha=1.0,
                bbox=dict(boxstyle='round,pad=0.5', facecolor='black', 
                         edgecolor='white', linewidth=2, alpha=0.8))
    
    def _add_context_info(self, fig):
        """Ajoute les infos de contexte"""
        context_text = f"Position: {self.position}"
        if self.season:
            context_text += f" | Saison: {self.season}"
        if self.competition:
            context_text += f" | {self.competition}"
        
        fig.text(0.02, 0.02, context_text, 
                fontsize=12, color='white', fontweight='normal', 
                ha='left', va='bottom', alpha=0.9)
    
    def _get_stat_value(self, stat_name: str) -> float:
        """Récupère la valeur d'une stat"""
        if stat_name in self.stats:
            return self.stats[stat_name]
        
        stat_lower = stat_name.lower()
        for key, value in self.stats.items():
            if stat_lower in key.lower():
                return value
        
        return 0.0
    
    def _normalize_stat(self, value: float, reference: float) -> float:
        """Normalise une stat sur 0-100"""
        if reference == 0:
            return 0
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
        """Moyenne normalisée d'une catégorie"""
        stats = self._get_category_stats_normalized(category)
        if not stats:
            return 0
        normalized_values = [v[1] for v in stats.values()]
        return np.mean(normalized_values)
    
    def plot_spider_radar(self, save_path: Optional[str] = None):
        """Spider radar avec explications"""
        categories = list(self.CATEGORIES.keys())
        values_normalized = [self._get_category_average_normalized(cat) for cat in categories]
        
        angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
        values_normalized += values_normalized[:1]
        angles += angles[:1]
        
        fig = plt.figure(figsize=(16, 9), facecolor=self.COLORS['gradient_end'])
        self._create_gradient_background(fig)
        
        ax = fig.add_subplot(111, projection='polar', facecolor='none')
        
        ax.plot(angles, values_normalized, 'o-', linewidth=4, color=self.COLORS['points'], 
                markersize=16, markeredgecolor=self.COLORS['edge'], markeredgewidth=2, zorder=5)
        ax.fill(angles, values_normalized, alpha=0.3, color=self.COLORS['points'], zorder=4)
        
        ax.set_ylim(0, 100)
        ax.set_yticks([25, 50, 75, 100])
        ax.set_yticklabels(['25', '50', '75', '100'], size=14, 
                          color='white', fontweight='bold')
        
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(categories, size=16, fontweight='bold', color='white')
        
        ax.grid(color='white', linestyle='-', linewidth=2, alpha=0.5)
        ax.spines['polar'].set_color('white')
        ax.spines['polar'].set_linewidth(2.5)
        
        for angle, value in zip(angles[:-1], values_normalized[:-1]):
            ax.text(angle, value + 10, f'{value:.0f}', 
                   ha='center', va='center', size=14, fontweight='bold',
                   color='white')
        
        plt.title(f'{self.player_name}\nPROFIL TACTIQUE', 
                 size=28, fontweight='bold', pad=50, color='white')
        
        explanation = "Scores normalisés par catégorie (0-100)\nChaque catégorie regroupe 5 statistiques clés"
        fig.text(0.5, 0.92, explanation, 
                ha='center', va='top', fontsize=11, color='white', 
                style='italic', alpha=0.9)
        
        legend_text = "🔴 <50: À améliorer  |  🟡 50-70: Bon niveau  |  🟢 >70: Élite"
        fig.text(0.5, 0.08, legend_text, 
                ha='center', va='bottom', fontsize=12, color='white', 
                fontweight='bold', alpha=0.9)
        
        self._add_watermark(fig)
        self._add_context_info(fig)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight', 
                       facecolor=self.COLORS['gradient_end'])
        plt.close()
    
    def plot_scatter_progressive(self, save_path: Optional[str] = None):
        """Scatter plot avec contexte"""
        prog_passes = self._get_stat_value('Progressive Passes')
        prog_carries = self._get_stat_value('Progressive Carries')
        
        fig = plt.figure(figsize=(16, 9), facecolor=self.COLORS['gradient_end'])
        self._create_gradient_background(fig)
        
        ax = fig.add_subplot(111, facecolor='none')
        
        ax.scatter(prog_passes, prog_carries, s=300, color=self.COLORS['points'], 
                  edgecolor=self.COLORS['edge'], linewidth=3, zorder=5)
        
        ax.text(prog_passes + 0.3, prog_carries + 0.2, self.player_name, 
               ha='right', va='bottom', fontsize=14, fontweight='bold',
               color='white', zorder=6,
               bbox=dict(boxstyle='round,pad=0.4', facecolor='black', 
                        edgecolor='white', linewidth=1.5, alpha=0.7))
        
        x_min, x_max = 0, max(12, prog_passes + 2)
        y_min, y_max = 0, max(10, prog_carries + 2)
        ax.set_xlim(x_min, x_max)
        ax.set_ylim(y_min, y_max)
        
        ax.set_xlabel('Passes progressives (par 90")', fontsize=16, 
                     color='white', fontweight='bold')
        ax.set_ylabel('Possessions progressives (par 90")', fontsize=16, 
                     color='white', fontweight='bold')
        
        ax.set_title('Projection des Passes et des Possessions progressives', 
                    fontsize=25, color='white', fontweight='bold', pad=20)
        
        explanation = "Passes progressives : passes qui rapprochent significativement le ballon du but adverse\nPossessions progressives : dribbles qui progressent vers le but adverse"
        fig.text(0.5, 0.92, explanation, 
                ha='center', va='top', fontsize=10, color='white', 
                style='italic', alpha=0.9)
        
        self._customize_axes(ax)
        ax.tick_params(axis='both', colors='white', labelsize=14)
        ax.set_xticks(np.arange(x_min, x_max + 1, 1))
        ax.set_yticks(np.arange(y_min, y_max + 1, 1))
        
        self._add_watermark(fig)
        self._add_context_info(fig)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight', 
                       facecolor=self.COLORS['gradient_end'])
        plt.close()
    
    def plot_key_stats_cards(self, save_path: Optional[str] = None):
        """Cartes de stats clés avec contexte"""
        key_stats = [
            ('Goals', 'BUTS'),
            ('Assists', 'PASSES D.'),
            ('Progressive Passes', 'PASSES PROG.'),
            ('Tackles Won', 'TACLES'),
            ('xG: Expected Goals', 'xG'),
            ('Key Passes', 'PASSES CLÉS')
        ]
        
        fig = plt.figure(figsize=(16, 9), facecolor=self.COLORS['gradient_end'])
        self._create_gradient_background(fig)
        
        for i, (stat_key, stat_label) in enumerate(key_stats):
            ax = plt.subplot(2, 3, i+1, facecolor='none')
            
            value = self._get_stat_value(stat_key)
            
            ax.text(0.5, 0.6, f'{value:.2f}', 
                   ha='center', va='center', fontsize=40, fontweight='bold',
                   color='white')
            
            ax.text(0.5, 0.3, stat_label, 
                   ha='center', va='center', fontsize=16, fontweight='bold',
                   color='white')
            
            ax.text(0.5, 0.15, 'par 90\'', 
                   ha='center', va='center', fontsize=11, style='italic',
                   color='white', alpha=0.8)
            
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.axis('off')
            
            rect = mpatches.Rectangle((0, 0), 1, 1, linewidth=2.5, 
                                     edgecolor='white', facecolor='none', 
                                     transform=ax.transAxes)
            ax.add_patch(rect)
        
        fig.suptitle(f'{self.player_name}\nSTATISTIQUES CLÉS', 
                    fontsize=28, fontweight='bold', color='white', y=0.98)
        
        subtitle = "Moyennes par 90 minutes jouées"
        fig.text(0.5, 0.91, subtitle, 
                ha='center', va='top', fontsize=12, color='white', 
                style='italic', alpha=0.9)
        
        self._add_watermark(fig)
        self._add_context_info(fig)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight', 
                       facecolor=self.COLORS['gradient_end'])
        plt.close()
    
    def plot_percentile_bars(self, save_path: Optional[str] = None):
        """Barres horizontales avec légendes"""
        categories = list(self.CATEGORIES.keys())
        scores = [self._get_category_average_normalized(cat) for cat in categories]
        
        fig = plt.figure(figsize=(16, 9), facecolor=self.COLORS['gradient_end'])
        self._create_gradient_background(fig)
        
        ax = fig.add_subplot(111, facecolor='none')
        
        bars = ax.barh(categories, scores, height=0.6, color=self.COLORS['points'], 
                      edgecolor=self.COLORS['edge'], linewidth=2, alpha=0.8)
        
        for i, (bar, score) in enumerate(zip(bars, scores)):
            ax.text(score + 3, i, f'{score:.0f}', 
                   va='center', ha='left', fontsize=16, fontweight='bold',
                   color='white')
        
        ax.set_xlim(0, 110)
        ax.set_xlabel('SCORE NORMALISÉ (0-100)', fontsize=16, color='white', fontweight='bold')
        ax.tick_params(axis='both', colors='white', labelsize=14)
        
        self._customize_axes(ax)
        
        ax.axvline(50, color='white', linestyle='--', linewidth=2, alpha=0.6, zorder=3)
        ax.axvline(70, color='white', linestyle='--', linewidth=2, alpha=0.6, zorder=3)
        
        ax.text(50, len(categories), '50: Seuil acceptable', 
               ha='center', va='bottom', fontsize=10, color='white', 
               fontweight='bold', alpha=0.8)
        ax.text(70, len(categories), '70: Niveau élite', 
               ha='center', va='bottom', fontsize=10, color='white', 
               fontweight='bold', alpha=0.8)
        
        ax.set_title(f'{self.player_name}\nÉVALUATION PAR CATÉGORIE', 
                    fontsize=28, fontweight='bold', color='white', pad=20)
        
        self._add_watermark(fig)
        self._add_context_info(fig)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight', 
                       facecolor=self.COLORS['gradient_end'])
        plt.close()
    
    def plot_performance_grid(self, save_path: Optional[str] = None):
        """Heatmap avec explications"""
        matrix_data = []
        row_labels = []
        
        for category in self.CATEGORIES.keys():
            stats_data = self._get_category_stats_normalized(category)
            if stats_data:
                row = [v[1] for v in stats_data.values()][:5]
                while len(row) < 5:
                    row.append(0)
                matrix_data.append(row)
                row_labels.append(category)
        
        fig = plt.figure(figsize=(16, 9), facecolor=self.COLORS['gradient_end'])
        self._create_gradient_background(fig)
        
        ax = fig.add_subplot(111, facecolor='none')
        
        cmap = LinearSegmentedColormap.from_list('custom',
            ['white', self.COLORS['points']], N=256)
        
        im = ax.imshow(matrix_data, cmap=cmap, aspect='auto', vmin=0, vmax=100)
        
        ax.set_yticks(range(len(row_labels)))
        ax.set_yticklabels(row_labels, fontsize=14, fontweight='bold', color='white')
        ax.set_xticks(range(5))
        ax.set_xticklabels([f'Stat {i+1}' for i in range(5)], 
                          fontsize=12, color='white')
        
        for i in range(len(matrix_data)):
            for j in range(len(matrix_data[i])):
                val = matrix_data[i][j]
                if val > 0:
                    color = 'white' if val > 50 else 'black'
                    ax.text(j, i, f'{val:.0f}', ha='center', va='center',
                           fontsize=14, fontweight='bold', color=color)
        
        cbar = plt.colorbar(im, ax=ax, pad=0.02)
        cbar.set_label('Score (0-100)', fontsize=14, color='white', fontweight='bold')
        cbar.ax.tick_params(colors='white', labelsize=12)
        cbar.outline.set_edgecolor('white')
        cbar.outline.set_linewidth(2)
        
        plt.title(f'{self.player_name}\nMATRICE DE PERFORMANCE DÉTAILLÉE', 
                 fontsize=25, fontweight='bold', color='white', pad=20)
        
        explanation = "Chaque ligne = 1 catégorie | Chaque colonne = 1 statistique de la catégorie"
        fig.text(0.5, 0.92, explanation, 
                ha='center', va='top', fontsize=10, color='white', 
                style='italic', alpha=0.9)
        
        self._add_watermark(fig)
        self._add_context_info(fig)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight', 
                       facecolor=self.COLORS['gradient_end'])
        plt.close()
    
    def print_tactical_summary(self):
        """Résumé textuel"""
        print(f"\n{'='*80}")
        print(f"  ⚽ PROFIL TACTIQUE - {self.player_name} ({self.position}) ⚽")
        print(f"{'='*80}\n")
        
        for category in self.CATEGORIES.keys():
            score = self._get_category_average_normalized(category)
            
            bar_length = int(score / 2)
            bar = '█' * bar_length + '░' * (50 - bar_length)
            
            if score >= 70:
                emoji = '🟢'
                label = 'ÉLITE'
            elif score >= 50:
                emoji = '🟡'
                label = 'BON'
            else:
                emoji = '🔴'
                label = 'PROGRESSION'
            
            print(f"  {emoji} {category:<12} {bar} {score:>5.0f}/100  [{label}]")
        
        print(f"\n{'='*80}")
        print(f"  @TarbouchData")
        print(f"{'='*80}\n")