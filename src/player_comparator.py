"""
PlayerComparator V8 - 16:9 + Rouge/Bleu + Évite stats à 0
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.colors import LinearSegmentedColormap
from typing import Dict, Tuple, List
from player_analyzer import PlayerAnalyzer


class PlayerComparator:
    """Compare deux joueurs 16:9"""
    
    COLORS = {
        'gradient_start': "#000000",
        'gradient_end': '#646327',
        'player1': '#FF0000',  # Rouge
        'player2': '#0000FF',  # Bleu
        'text': '#FFFFFF',
        'edge': '#000000',
        'winner': '#00FF00'
    }
    
    CONFIDENCE_THRESHOLDS = {
        'high': 900,
        'medium': 450,
        'low': 180
    }
    
    # Pool de stats de backup si les principales sont à 0
    BACKUP_STATS = [
        ('Touches', 'TOUCHES'),
        ('Carries', 'POSSESSIONS'),
        ('Ball Recoveries', 'RÉCUP.'),
        ('Passes into Final Third', 'PASSES 1/3'),
        ('Successful Take-Ons', 'DRIBBLES'),
        ('Passes into Penalty Area', 'PASSES SURF.')
    ]
    
    def __init__(self, player1_name: str, player2_name: str,
                 player1_data: pd.DataFrame, player2_data: pd.DataFrame):
        self.player1_name = player1_name
        self.player2_name = player2_name
        
        pos1 = player1_data['position'].iloc[0] if 'position' in player1_data else 'MF'
        pos2 = player2_data['position'].iloc[0] if 'position' in player2_data else 'MF'
        
        self.analyzer1 = PlayerAnalyzer(player1_name, pos1)
        self.analyzer1.load_data(player1_data)
        
        self.analyzer2 = PlayerAnalyzer(player2_name, pos2)
        self.analyzer2.load_data(player2_data)
        
        self.minutes1 = self._extract_minutes(player1_data)
        self.minutes2 = self._extract_minutes(player2_data)
        
        self.confidence1 = self._calculate_confidence(self.minutes1)
        self.confidence2 = self._calculate_confidence(self.minutes2)
        
        print(f"\n📊 MINUTES JOUÉES :")
        print(f"   🔴 {self.player1_name:<30} : {self.minutes1:>5.0f} min")
        print(f"   🔵 {self.player2_name:<30} : {self.minutes2:>5.0f} min")
    
    def _extract_minutes(self, df: pd.DataFrame) -> float:
        """Extrait les minutes"""
        minutes_cols = ['Minutes', 'Min', 'Playing Time', '90s']
        
        for col in minutes_cols:
            if col in df.columns:
                if col == '90s':
                    value = pd.to_numeric(df[col].iloc[0], errors='coerce')
                    if not pd.isna(value):
                        return value * 90
                else:
                    value = pd.to_numeric(df[col].iloc[0], errors='coerce')
                    if not pd.isna(value):
                        return value
        
        if 'minutes' in df.columns:
            value = pd.to_numeric(df['minutes'].iloc[0], errors='coerce')
            if not pd.isna(value):
                return value
        
        return 1800.0
    
    def _calculate_confidence(self, minutes: float) -> float:
        """Score de confiance 0-1"""
        confidence = 1 / (1 + np.exp(-(minutes - 900) / 300))
        return confidence
    
    def _create_gradient_background(self, fig):
        """Dégradé vertical"""
        gradient = np.linspace(0, 1, 256).reshape(-1, 1)
        gradient = np.hstack((gradient, gradient))
        
        cmap = LinearSegmentedColormap.from_list("", 
            [self.COLORS['gradient_start'], self.COLORS['gradient_end']])
        
        ax_bg = fig.add_axes([0, 0, 1, 1])
        ax_bg.axis('off')
        ax_bg.imshow(gradient, aspect='auto', cmap=cmap, extent=[0, 1, 0, 1], zorder=-1)
    
    def _add_watermark(self, fig):
        """Watermark simple"""
        fig.text(0.98, 0.02, '@TarbouchData', 
                fontsize=20, color='white', fontweight='bold', 
                ha='right', va='bottom', alpha=1.0,
                bbox=dict(boxstyle='round,pad=0.5', facecolor='black', 
                         edgecolor='white', linewidth=2, alpha=0.8))
    
    def _add_comparison_context(self, fig):
        """Contexte en bas"""
        context1 = f"{self.analyzer1.position}"
        if self.analyzer1.season:
            context1 += f" | {self.analyzer1.season}"
        if self.analyzer1.competition:
            context1 += f" | {self.analyzer1.competition}"
        context1 += f" | {self.minutes1:.0f} min"
        
        context2 = f"{self.analyzer2.position}"
        if self.analyzer2.season:
            context2 += f" | {self.analyzer2.season}"
        if self.analyzer2.competition:
            context2 += f" | {self.analyzer2.competition}"
        context2 += f" | {self.minutes2:.0f} min"
        
        fig.text(0.02, 0.06, f"🔴 {self.player1_name}: {context1}", 
                fontsize=11, color='white', ha='left', va='bottom', alpha=0.9)
        fig.text(0.02, 0.02, f"🔵 {self.player2_name}: {context2}", 
                fontsize=11, color='white', ha='left', va='bottom', alpha=0.9)
    
    def _get_stat_value(self, analyzer, stat_key: str) -> float:
        """Récupère valeur stat depuis analyzer"""
        return analyzer._get_stat_value(stat_key)
    
    def _select_valid_stats(self, preferred_stats: List[tuple]) -> List[tuple]:
        """
        Sélectionne les stats valides (non nulles pour les deux joueurs)
        Remplace par des stats de backup si nécessaire
        """
        valid_stats = []
        
        for stat_key, stat_label in preferred_stats:
            val1 = self.analyzer1._get_stat_value(stat_key)
            val2 = self.analyzer2._get_stat_value(stat_key)
            
            # Garder si au moins un joueur a une valeur > 0
            if val1 > 0 or val2 > 0:
                valid_stats.append((stat_key, stat_label))
        
        # Si on n'a pas assez de stats, ajouter des backups
        if len(valid_stats) < 6:
            for stat_key, stat_label in self.BACKUP_STATS:
                if len(valid_stats) >= 6:
                    break
                # Vérifier que cette stat n'est pas déjà dans la liste
                if (stat_key, stat_label) not in valid_stats:
                    val1 = self.analyzer1._get_stat_value(stat_key)
                    val2 = self.analyzer2._get_stat_value(stat_key)
                    if val1 > 0 or val2 > 0:
                        valid_stats.append((stat_key, stat_label))
        
        return valid_stats[:6]  # Max 6 stats
    
    def plot_comparison_spider(self, save_path: str = None):
        """Spider comparaison 16:9"""
        categories = list(PlayerAnalyzer.CATEGORIES.keys())
        
        values1 = [self.analyzer1._get_category_average_normalized(cat) for cat in categories]
        values2 = [self.analyzer2._get_category_average_normalized(cat) for cat in categories]
        
        angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
        values1 += values1[:1]
        values2 += values2[:1]
        angles += angles[:1]
        
        fig = plt.figure(figsize=(16, 9), facecolor='none')
        self._create_gradient_background(fig)
        
        ax = fig.add_subplot(111, projection='polar', facecolor='none')
        
        # Joueur 1 - Rouge
        ax.plot(angles, values1, 'o-', linewidth=4, 
                color=self.COLORS['player1'], markersize=12, 
                markeredgecolor=self.COLORS['edge'], markeredgewidth=2, 
                label=self.player1_name, zorder=5, alpha=0.9)
        ax.fill(angles, values1, alpha=0.2, color=self.COLORS['player1'], zorder=4)
        
        # Joueur 2 - Bleu
        ax.plot(angles, values2, 's-', linewidth=4, 
                color=self.COLORS['player2'], markersize=12, 
                markeredgecolor=self.COLORS['edge'], markeredgewidth=2, 
                label=self.player2_name, zorder=5, alpha=0.9)
        ax.fill(angles, values2, alpha=0.2, color=self.COLORS['player2'], zorder=4)
        
        ax.set_ylim(0, 100)
        ax.set_yticks([25, 50, 75, 100])
        ax.set_yticklabels(['25', '50', '75', '100'], size=14, 
                          color='white', fontweight='bold')
        
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(categories, size=16, fontweight='bold', color='white')
        
        ax.grid(color='white', linestyle='-', linewidth=2, alpha=0.5)
        ax.spines['polar'].set_color('white')
        ax.spines['polar'].set_linewidth(2.5)
        
        # Légende
        legend = ax.legend(loc='upper right', fontsize=14, 
                          facecolor='black', edgecolor='white',
                          framealpha=0.8, labelcolor='white')
        legend.get_frame().set_linewidth(2)
        
        plt.title(f'COMPARAISON\n{self.player1_name} vs {self.player2_name}', 
                 size=28, fontweight='bold', pad=50, color='white')
        
        self._add_watermark(fig)
        self._add_comparison_context(fig)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight', 
                       facecolor=self.COLORS['gradient_end'])
        plt.close()
    
    def plot_comparison_scatter(self, save_path: str = None):
        """Scatter 16:9"""
        prog_passes1 = self.analyzer1._get_stat_value('Progressive Passes')
        prog_carries1 = self.analyzer1._get_stat_value('Progressive Carries')
        
        prog_passes2 = self.analyzer2._get_stat_value('Progressive Passes')
        prog_carries2 = self.analyzer2._get_stat_value('Progressive Carries')
        
        fig = plt.figure(figsize=(16, 9), facecolor='none')
        self._create_gradient_background(fig)
        
        ax = fig.add_subplot(111, facecolor='none')
        
        # Taille basée sur minutes
        size1 = 300 * (0.5 + 0.5 * self.confidence1)
        size2 = 300 * (0.5 + 0.5 * self.confidence2)
        
        ax.scatter(prog_passes1, prog_carries1, s=size1, 
                  color=self.COLORS['player1'], 
                  edgecolor=self.COLORS['edge'], linewidth=3, zorder=5,
                  label=f"{self.player1_name} ({self.minutes1:.0f} min)",
                  alpha=0.9)
        
        ax.scatter(prog_passes2, prog_carries2, s=size2, 
                  color=self.COLORS['player2'], 
                  edgecolor=self.COLORS['edge'], linewidth=3, zorder=5,
                  marker='s', label=f"{self.player2_name} ({self.minutes2:.0f} min)",
                  alpha=0.9)
        
        # Labels
        ax.text(prog_passes1 + 0.3, prog_carries1 + 0.2, self.player1_name, 
               ha='right', va='bottom', fontsize=13, fontweight='bold',
               color='white', zorder=6,
               bbox=dict(boxstyle='round,pad=0.4', facecolor='black',
                        edgecolor=self.COLORS['player1'], linewidth=2, alpha=0.8))
        
        ax.text(prog_passes2 + 0.3, prog_carries2 + 0.2, self.player2_name, 
               ha='right', va='bottom', fontsize=13, fontweight='bold',
               color='white', zorder=6,
               bbox=dict(boxstyle='round,pad=0.4', facecolor='black',
                        edgecolor=self.COLORS['player2'], linewidth=2, alpha=0.8))
        
        all_x = [prog_passes1, prog_passes2]
        all_y = [prog_carries1, prog_carries2]
        x_max = max(max(all_x) + 2, 12)
        y_max = max(max(all_y) + 2, 10)
        
        ax.set_xlim(0, x_max)
        ax.set_ylim(0, y_max)
        
        ax.set_xlabel('Passes progressives (par 90")', fontsize=16, 
                     color='white', fontweight='bold')
        ax.set_ylabel('Possessions progressives (par 90")', fontsize=16, 
                     color='white', fontweight='bold')
        
        ax.tick_params(axis='both', colors='white', labelsize=14)
        
        for spine in ax.spines.values():
            spine.set_edgecolor('white')
            spine.set_linewidth(2.5)
        
        ax.set_xticks(np.arange(0, x_max + 1, 1))
        ax.set_yticks(np.arange(0, y_max + 1, 1))
        
        legend = ax.legend(fontsize=14, facecolor='black', edgecolor='white',
                          loc='upper left', framealpha=0.8, labelcolor='white')
        legend.get_frame().set_linewidth(2)
        
        plt.title('COMPARAISON\nPasses et Possessions Progressives', 
                 fontsize=24, color='white', fontweight='bold', pad=20)
        
        self._add_watermark(fig)
        self._add_comparison_context(fig)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight', 
                       facecolor=self.COLORS['gradient_end'])
        plt.close()
    
    def plot_comparison_cards(self, save_path: str = None):
        """Cartes comparaison 16:9 - Évite les stats à 0"""
        # Stats préférées
        preferred_stats = [
            ('Goals', 'BUTS'),
            ('Assists', 'PASSES D.'),
            ('Progressive Passes', 'PASSES PROG.'),
            ('Tackles Won', 'TACLES'),
            ('xG: Expected Goals', 'xG'),
            ('Key Passes', 'PASSES CLÉS')
        ]
        
        # Sélectionner les stats valides
        key_stats = self._select_valid_stats(preferred_stats)
        
        fig = plt.figure(figsize=(16, 9), facecolor='none')
        self._create_gradient_background(fig)
        
        n_stats = len(key_stats)
        
        for i, (stat_key, stat_label) in enumerate(key_stats):
            val1 = self.analyzer1._get_stat_value(stat_key)
            val2 = self.analyzer2._get_stat_value(stat_key)
            
            max_val = max(val1, val2) if max(val1, val2) > 0 else 1
            
            ax = plt.subplot(n_stats, 1, i+1, facecolor='none')
            
            # Transparence basée sur confiance
            alpha1 = 0.8 * self.confidence1 + 0.4 * (1 - self.confidence1)
            alpha2 = 0.8 * self.confidence2 + 0.4 * (1 - self.confidence2)
            
            # Barres symétriques
            ax.barh([0], [-val1], height=0.6, 
                   color=self.COLORS['player1'], 
                   edgecolor=self.COLORS['edge'], 
                   linewidth=2, alpha=alpha1)
            
            ax.barh([0], [val2], height=0.6, 
                   color=self.COLORS['player2'], 
                   edgecolor=self.COLORS['edge'], 
                   linewidth=2, alpha=alpha2)
            
            # Couleur gagnant
            if val1 > val2:
                color1, color2 = self.COLORS['winner'], 'white'
            elif val2 > val1:
                color1, color2 = 'white', self.COLORS['winner']
            else:
                color1 = color2 = 'white'
            
            ax.text(-val1 - max_val*0.05, 0, f'{val1:.2f}', 
                   ha='right', va='center', fontsize=18, fontweight='bold',
                   color=color1)
            
            ax.text(val2 + max_val*0.05, 0, f'{val2:.2f}', 
                   ha='left', va='center', fontsize=18, fontweight='bold',
                   color=color2)
            
            # Label stat
            ax.text(0, 0, stat_label, 
                   ha='center', va='center', fontsize=14, fontweight='bold',
                   color='white',
                   bbox=dict(boxstyle='round,pad=0.5', facecolor='black', 
                            edgecolor='white', linewidth=2, alpha=0.9))
            
            # Noms en haut
            if i == 0:
                ax.text(-max_val*0.5, 0.8, f"{self.player1_name}\n({self.minutes1:.0f} min)", 
                       ha='center', va='center', fontsize=14, fontweight='bold',
                       color=self.COLORS['player1'])
                ax.text(max_val*0.5, 0.8, f"{self.player2_name}\n({self.minutes2:.0f} min)", 
                       ha='center', va='center', fontsize=14, fontweight='bold',
                       color=self.COLORS['player2'])
            
            ax.set_xlim(-max_val*1.3, max_val*1.3)
            ax.set_ylim(-0.5, 0.5)
            ax.axis('off')
        
        fig.suptitle(f'COMPARAISON STATS CLÉS\n{self.player1_name} VS {self.player2_name}', 
                    fontsize=24, fontweight='bold', color='white', y=0.98)
        
        self._add_watermark(fig)
        self._add_comparison_context(fig)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight', 
                       facecolor=self.COLORS['gradient_end'])
        plt.close()