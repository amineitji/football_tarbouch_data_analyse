"""
PlayerAnalyzer V13 - Standards calibrés 2024/2025 + Minutes
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.colors import LinearSegmentedColormap
from typing import Dict, List, Optional
import warnings
warnings.filterwarnings('ignore')

plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans', 'Helvetica']


class PlayerAnalyzer:
    """Analyseur tactique avec standards calibrés 2024/2025"""
    
    # Standards recalibrés au 90e percentile saison 2024/2025
    POSITION_STANDARDS = {
        'DF': {
            'Passing': [63.86, 5.69, 5.79, 0.15, 0.13],
            'Shooting': [0.13, 1.10, 0.15, 0.10, 0.10],
            'Creation': [0.15, 2.64, 0.15, 0.15, 0.15],
            'Defense': [2.71, 2.71, 1.63, 1.78, 4.86],
            'Possession': [2.11, 2.66, 2.66, 1.08, 2.66],
        },
        'MF': {
            'Passing': [57.47, 7.28, 6.59, 0.26, 0.22],
            'Shooting': [0.28, 2.40, 0.26, 0.23, 0.23],
            'Creation': [0.26, 4.33, 0.26, 0.26, 0.26],
            'Defense': [3.03, 3.03, 1.52, 1.72, 2.10],
            'Possession': [3.82, 3.22, 3.22, 1.67, 3.22],
        },
        'FW': {
            'Passing': [33.43, 4.49, 10.92, 0.33, 0.27],
            'Shooting': [0.56, 3.38, 0.33, 0.47, 0.47],
            'Creation': [0.33, 4.64, 0.33, 0.33, 0.33],
            'Defense': [2.00, 2.00, 0.71, 1.43, 1.34],
            'Possession': [6.40, 5.05, 5.05, 2.62, 5.05],
        },
        'GK': {
            'Passing': [30, 3, 2, 0.2, 0.05],
            'Shooting': [0, 0, 0, 0, 0],
            'Creation': [0, 0, 0, 0, 0],
            'Defense': [0, 0, 1, 1, 3],
            'Possession': [40, 20, 0.5, 0, 0]
        }
    }
    
    # Seuils de performance
    THRESHOLDS = {
        'GK': {'elite': 80, 'good': 60, 'acceptable': 40},
        'DF': {'elite': 75, 'good': 55, 'acceptable': 40},
        'MF': {'elite': 70, 'good': 50, 'acceptable': 35},
        'FW': {'elite': 70, 'good': 50, 'acceptable': 35}
    }
    
    CATEGORIES = {
        'Passing': ['Passes Completed', 'Progressive Passes', 'Passes into Final Third', 'Key Passes', 'xA: Expected Assists'],
        'Shooting': ['Goals', 'Shots Total', 'Shots on Target', 'xG: Expected Goals', 'npxG: Non-Penalty xG'],
        'Creation': ['Assists', 'Shot-Creating Actions', 'Goal-Creating Actions', 'Through Balls', 'Passes into Penalty Area'],
        'Defense': ['Tackles', 'Tackles Won', 'Interceptions', 'Blocks', 'Ball Recoveries'],
        'Possession': ['Touches', 'Carries', 'Progressive Carries', 'Successful Take-Ons', 'Carries into Final Third']
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
        self.position = self._normalize_position(position)
        self.df = None
        self.stats = {}
        self.season = None
        self.competition = None
        self.minutes = None
        self.thresholds = self.THRESHOLDS.get(self.position, self.THRESHOLDS['MF'])
        
    def _normalize_position(self, position: str) -> str:
        """Normalise le poste"""
        pos = str(position).upper()
        if 'GK' in pos:
            return 'GK'
        elif any(x in pos for x in ['DF', 'CB', 'LB', 'RB', 'WB']):
            return 'DF'
        elif any(x in pos for x in ['FW', 'CF', 'ST', 'LW', 'RW']):
            return 'FW'
        else:
            return 'MF'
    
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
        
        # Extraire minutes
        if 'minutes_played' in df.columns:
            self.minutes = pd.to_numeric(df['minutes_played'].iloc[0], errors='coerce')
        elif 'Minutes' in df.columns:
            self.minutes = pd.to_numeric(df['Minutes'].iloc[0], errors='coerce')
        elif '90s' in df.columns:
            value = pd.to_numeric(df['90s'].iloc[0], errors='coerce')
            if not pd.isna(value):
                self.minutes = value * 90
    
    def _create_gradient_background(self, fig):
        """Dégradé vertical noir → doré"""
        gradient = np.linspace(0, 1, 256).reshape(-1, 1)
        gradient = np.hstack((gradient, gradient))
        
        cmap = LinearSegmentedColormap.from_list("", 
            [self.COLORS['gradient_start'], self.COLORS['gradient_end']])
        
        ax_bg = fig.add_axes([0, 0, 1, 1])
        ax_bg.axis('off')
        ax_bg.imshow(gradient, aspect='auto', cmap=cmap, extent=[0, 1, 0, 1], zorder=-1)
    
    def _customize_axes(self, ax):
        """Contours blancs"""
        for spine in ax.spines.values():
            spine.set_edgecolor('white')
            spine.set_linewidth(2.5)
    
    def _add_watermark(self, fig):
        """Watermark @TarbouchData"""
        fig.text(0.98, 0.02, '@TarbouchData', 
                fontsize=20, color='white', fontweight='bold', 
                ha='right', va='bottom', alpha=1.0,
                bbox=dict(boxstyle='round,pad=0.5', facecolor='black', 
                         edgecolor='white', linewidth=2, alpha=0.8))
    
    def _add_context_info(self, fig):
        """Info contexte"""
        context_text = f"Position: {self.position}"
        if self.season:
            context_text += f" | Saison: {self.season}"
        if self.competition:
            context_text += f" | {self.competition}"
        if self.minutes:
            context_text += f" | {self.minutes:.0f} minutes"
        
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
        """Normalise sur 0-100"""
        if reference == 0:
            return 0
        normalized = (value / reference) * 100
        return min(normalized, 100)
    
    def _get_category_stats_normalized(self, category: str) -> Dict[str, tuple]:
        """Stats normalisées selon le poste"""
        stats_list = self.CATEGORIES.get(category, [])
        standards = self.POSITION_STANDARDS.get(self.position, {}).get(category, [])
        
        result = {}
        for i, stat_name in enumerate(stats_list):
            raw_value = self._get_stat_value(stat_name)
            if i < len(standards) and standards[i] > 0:
                normalized = self._normalize_stat(raw_value, standards[i])
            else:
                normalized = 0
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
        """Spider radar 16:9"""
        categories = list(self.CATEGORIES.keys())
        values_normalized = [self._get_category_average_normalized(cat) for cat in categories]
        angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
        values_normalized += values_normalized[:1]
        angles += angles[:1]
        
        fig = plt.figure(figsize=(16, 9), facecolor='none')
        self._create_gradient_background(fig)
        ax = fig.add_subplot(111, projection='polar', facecolor='none')
        
        ax.plot(angles, values_normalized, 'o-', linewidth=4,
                color=self.COLORS['points'], markersize=14,
                markeredgecolor=self.COLORS['edge'], markeredgewidth=2.5,
                label=self.player_name, zorder=5, alpha=0.9)
        ax.fill(angles, values_normalized, alpha=0.25, color=self.COLORS['points'], zorder=4)
        
        ax.set_ylim(0, 100)
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels([])  # Vide pour éviter les doublons
        ax.set_yticks([20, 40, 60, 80, 100])
        ax.set_yticklabels(['20', '40', '60', '80', '100'],
                           color='white', size=14, fontweight='bold')
        ax.grid(True, color='white', linestyle='--', linewidth=2, alpha=0.4)
        ax.spines['polar'].set_color('white')
        ax.spines['polar'].set_linewidth(3)
        
        # Mettre en évidence les catégories par-dessus le reste
        for i, angle in enumerate(angles[:-1]):
            ax.text(angle, 115, categories[i], size=18, color="#FFFFFF", fontweight='bold',
                    ha='center', va='center', 
                    bbox=dict(boxstyle='round,pad=0.4', fc='black', ec='#FFD700', lw=2.5, alpha=0.9))
        
        plt.title(f'{self.player_name} | {self.competition}',
                  size=32, fontweight='bold', pad=50, color='white')
        
        # Légende sur le côté droit
        legend = ax.legend(loc='upper left', bbox_to_anchor=(1.15, 1.0),
                          frameon=True, facecolor='black', edgecolor='#FFD700',
                          fontsize=14, labelcolor='white', framealpha=0.9)
        legend.get_frame().set_linewidth(2.5)
        
        self._add_watermark(fig)
        self._add_context_info(fig)
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight',
                        facecolor=self.COLORS['gradient_end'])
        plt.close()


    def plot_key_stats_cards(self, save_path: Optional[str] = None):
        """Cartes stats clés 16:9"""
        if self.position == 'DF':
            key_stats = [
                ('Tackles Won', 'TACLES'),
                ('Interceptions', 'INTERCEPTIONS'),
                ('Blocks', 'CONTRES'),
                ('Ball Recoveries', 'RÉCUP.'),
                ('Progressive Passes', 'PASSES PROG.'),
                ('Passes Completed', 'PASSES')
            ]
        elif self.position == 'FW':
            key_stats = [
                ('Goals', 'BUTS'),
                ('xG: Expected Goals', 'xG'),
                ('Shots Total', 'TIRS'),
                ('Assists', 'PASSES D.'),
                ('Shot-Creating Actions', 'ACTIONS'),
                ('Successful Take-Ons', 'DRIBBLES')
            ]
        else:  # MF
            key_stats = [
                ('Goals', 'BUTS'),
                ('Assists', 'PASSES D.'),
                ('Progressive Passes', 'PASSES PROG.'),
                ('Tackles Won', 'TACLES'),
                ('xG: Expected Goals', 'xG'),
                ('Key Passes', 'PASSES CLÉS')
            ]
        
        fig = plt.figure(figsize=(16, 9), facecolor='none')
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
        
        self._add_watermark(fig)
        self._add_context_info(fig)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight', 
                       facecolor=self.COLORS['gradient_end'])
        plt.close()
    
    def plot_percentile_bars(self, save_path: Optional[str] = None):
        """Barres horizontales 16:9"""
        categories = list(self.CATEGORIES.keys())
        scores = [self._get_category_average_normalized(cat) for cat in categories]
        
        fig = plt.figure(figsize=(16, 9), facecolor='none')
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
        
        elite = self.thresholds['elite']
        good = self.thresholds['good']
        
        ax.axvline(good, color='white', linestyle='--', linewidth=2, alpha=0.6, zorder=3)
        ax.axvline(elite, color='white', linestyle='--', linewidth=2, alpha=0.6, zorder=3)
        
        ax.text(good, len(categories), f'{good}', 
               ha='center', va='bottom', fontsize=10, color='white', 
               fontweight='bold', alpha=0.8)
        ax.text(elite, len(categories), f'{elite}', 
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
        """Heatmap 16:9"""
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
        
        fig = plt.figure(figsize=(16, 9), facecolor='none')
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
        
        self._add_watermark(fig)
        self._add_context_info(fig)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight', 
                       facecolor=self.COLORS['gradient_end'])
        plt.close()
    
    def print_tactical_summary(self):
        """Résumé avec seuils adaptés"""
        print(f"\n{'='*80}")
        print(f"  ⚽ {self.player_name} ({self.position}) - Standards {self.position} ⚽")
        print(f"{'='*80}\n")
        
        elite = self.thresholds['elite']
        good = self.thresholds['good']
        
        for category in self.CATEGORIES.keys():
            score = self._get_category_average_normalized(category)
            
            bar_length = int(score / 2)
            bar = '█' * bar_length + '░' * (50 - bar_length)
            
            if score >= elite:
                emoji = '🟢'
                label = 'ÉLITE'
            elif score >= good:
                emoji = '🟡'
                label = 'BON'
            else:
                emoji = '🔴'
                label = 'PROGRESSION'
            
            print(f"  {emoji} {category:<12} {bar} {score:>5.0f}/100  [{label}]")
        
        print(f"\n  Seuils {self.position}: Élite >{elite} | Bon {good}-{elite} | <{good}")
        print(f"\n{'='*80}")
        print(f"  @TarbouchData")
        print(f"{'='*80}\n")