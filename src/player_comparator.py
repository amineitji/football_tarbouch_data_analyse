"""
PlayerComparator V4 - Style avec dégradé + infos contextuelles enrichies
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.colors import LinearSegmentedColormap
from typing import Dict
from player_analyzer import PlayerAnalyzer


class PlayerComparator:
    """Compare deux joueurs avec style dégradé blanc-pastel"""
    
    COLORS = {
        'gradient_start': "#000000",
        'gradient_end': '#646327',
        'player1': '#FF0000',
        'player2': '#0000FF',
        'text': '#FFFFFF',
        'edge': '#000000'
    }
    
    def __init__(self, player1_name: str, player2_name: str,
                 player1_data: pd.DataFrame, player2_data: pd.DataFrame):
        self.player1_name = player1_name
        self.player2_name = player2_name
        
        # Créer les analyzers
        self.analyzer1 = PlayerAnalyzer(player1_name, player1_data['position'].iloc[0] if 'position' in player1_data else 'MF')
        self.analyzer1.load_data(player1_data)
        
        self.analyzer2 = PlayerAnalyzer(player2_name, player2_data['position'].iloc[0] if 'position' in player2_data else 'MF')
        self.analyzer2.load_data(player2_data)
    
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
        """Ajoute le watermark @TarbouchData en grand"""
        fig.text(0.98, 0.02, '@TarbouchData', 
                fontsize=20, color='white', fontweight='bold', 
                ha='right', va='bottom', alpha=1.0,
                bbox=dict(boxstyle='round,pad=0.5', facecolor='black', 
                         edgecolor='white', linewidth=2, alpha=0.8))
    
    def _add_comparison_context(self, fig):
        """Ajoute le contexte de comparaison"""
        context1 = f"{self.analyzer1.position}"
        if self.analyzer1.season:
            context1 += f" | {self.analyzer1.season}"
        if self.analyzer1.competition:
            context1 += f" | {self.analyzer1.competition}"
        
        context2 = f"{self.analyzer2.position}"
        if self.analyzer2.season:
            context2 += f" | {self.analyzer2.season}"
        if self.analyzer2.competition:
            context2 += f" | {self.analyzer2.competition}"
        
        fig.text(0.02, 0.06, f"🔴 {self.player1_name}: {context1}", 
                fontsize=11, color='white', ha='left', va='bottom', alpha=0.9)
        fig.text(0.02, 0.02, f"🔵 {self.player2_name}: {context2}", 
                fontsize=11, color='white', ha='left', va='bottom', alpha=0.9)
    
    def plot_comparison_spider(self, save_path: str = None):
        """Spider radar superposé avec explications"""
        categories = list(self.analyzer1.CATEGORIES.keys())
        
        values1 = [self.analyzer1._get_category_average_normalized(cat) for cat in categories]
        values2 = [self.analyzer2._get_category_average_normalized(cat) for cat in categories]
        
        angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
        values1 += values1[:1]
        values2 += values2[:1]
        angles += angles[:1]
        
        fig = plt.figure(figsize=(16, 9))
        self._create_gradient_background(fig)
        
        ax = fig.add_subplot(111, projection='polar', facecolor='none')
        
        # Joueur 1 (Rouge)
        ax.plot(angles, values1, 'o-', linewidth=4, color=self.COLORS['player1'],
                markersize=16, markeredgecolor=self.COLORS['edge'], markeredgewidth=2, 
                label=self.player1_name, zorder=6, alpha=0.9)
        ax.fill(angles, values1, alpha=0.25, color=self.COLORS['player1'], zorder=5)
        
        # Joueur 2 (Bleu)
        ax.plot(angles, values2, 's-', linewidth=4, color=self.COLORS['player2'],
                markersize=16, markeredgecolor=self.COLORS['edge'], markeredgewidth=2,
                label=self.player2_name, zorder=6, alpha=0.9)
        ax.fill(angles, values2, alpha=0.25, color=self.COLORS['player2'], zorder=5)
        
        # Style
        ax.set_ylim(0, 100)
        ax.set_yticks([25, 50, 75, 100])
        ax.set_yticklabels(['25', '50', '75', '100'], size=14, 
                          color='white', fontweight='bold')
        
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(categories, size=16, fontweight='bold', color='white')
        
        ax.grid(color='white', linestyle='-', linewidth=2, alpha=0.5)
        ax.spines['polar'].set_color('white')
        ax.spines['polar'].set_linewidth(2.5)
        
        # Titre
        plt.title(f'COMPARAISON RADAR\n{self.player1_name} VS {self.player2_name}', 
                 size=28, fontweight='bold', pad=60, color='white')
        
        # Explication
        explanation = "Scores normalisés par catégorie (0-100) | Plus la zone est grande, meilleur est le joueur"
        fig.text(0.5, 0.92, explanation, 
                ha='center', va='top', fontsize=11, color='white', 
                style='italic', alpha=0.9)
        
        # Légende améliorée
        legend = plt.legend(loc='upper right', bbox_to_anchor=(1.3, 1.12), 
                           fontsize=16, facecolor='black', edgecolor='white',
                           framealpha=0.8, labelcolor='white')
        legend.get_frame().set_linewidth(2.5)
        
        # Watermark et contexte
        self._add_watermark(fig)
        self._add_comparison_context(fig)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight', facecolor='none')
        plt.close()
    
    def plot_comparison_categories(self, save_path: str = None):
        """Barres groupées avec légendes"""
        categories = list(self.analyzer1.CATEGORIES.keys())
        
        values1 = [self.analyzer1._get_category_average_normalized(cat) for cat in categories]
        values2 = [self.analyzer2._get_category_average_normalized(cat) for cat in categories]
        
        x = np.arange(len(categories))
        width = 0.35
        
        fig = plt.figure(figsize=(16, 9))
        self._create_gradient_background(fig)
        
        ax = fig.add_subplot(111, facecolor='none')
        
        # Barres
        bars1 = ax.bar(x - width/2, values1, width, label=self.player1_name,
                      color=self.COLORS['player1'], edgecolor=self.COLORS['edge'], 
                      linewidth=2, alpha=0.8)
        bars2 = ax.bar(x + width/2, values2, width, label=self.player2_name,
                      color=self.COLORS['player2'], edgecolor=self.COLORS['edge'], 
                      linewidth=2, alpha=0.8)
        
        # Annotations
        for bars in [bars1, bars2]:
            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2, height + 2,
                       f'{height:.0f}', ha='center', va='bottom', size=14,
                       fontweight='bold', color='white')
        
        # Style
        ax.set_xlabel('CATÉGORIES', size=16, fontweight='bold', color='white')
        ax.set_ylabel('SCORE NORMALISÉ (0-100)', size=16, fontweight='bold', color='white')
        ax.set_xticks(x)
        ax.set_xticklabels(categories, size=14, fontweight='bold', color='white')
        ax.set_ylim(0, 115)
        
        ax.tick_params(axis='both', colors='white', labelsize=14)
        
        # Lignes de référence avec labels
        ax.axhline(50, color='white', linestyle='--', linewidth=2, alpha=0.6)
        ax.axhline(70, color='white', linestyle='--', linewidth=2, alpha=0.6)
        
        ax.text(len(categories)-0.5, 52, 'Seuil 50', 
               ha='right', fontsize=10, color='white', fontweight='bold', alpha=0.8)
        ax.text(len(categories)-0.5, 72, 'Seuil 70 (Élite)', 
               ha='right', fontsize=10, color='white', fontweight='bold', alpha=0.8)
        
        self._customize_axes(ax)
        
        # Légende
        ax.legend(fontsize=16, facecolor='black', edgecolor='white',
                 loc='upper left', framealpha=0.8, labelcolor='white')
        
        # Titre
        plt.title(f'COMPARAISON PAR CATÉGORIE\n{self.player1_name} VS {self.player2_name}', 
                 size=25, fontweight='bold', pad=20, color='white')
        
        # Watermark et contexte
        self._add_watermark(fig)
        self._add_comparison_context(fig)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight', facecolor='none')
        plt.close()
    
    def plot_comparison_heatmap(self, save_path: str = None):
        """Heatmap côte à côte avec explications"""
        categories = list(self.analyzer1.CATEGORIES.keys())
        
        matrix1 = []
        matrix2 = []
        stat_labels = []
        
        for category in categories:
            stats1 = self.analyzer1._get_category_stats_normalized(category)
            stats2 = self.analyzer2._get_category_stats_normalized(category)
            
            for stat_name in list(stats1.keys())[:5]:
                matrix1.append([stats1[stat_name][1]])
                matrix2.append([stats2.get(stat_name, (0, 0))[1]])
                stat_labels.append(f"{category[:4]}: {stat_name[:22]}")
        
        fig = plt.figure(figsize=(16, 9))
        self._create_gradient_background(fig)
        
        from matplotlib.gridspec import GridSpec
        gs = GridSpec(1, 2, figure=fig, width_ratios=[1, 1], wspace=0.1)
        ax1 = fig.add_subplot(gs[0], facecolor='none')
        ax2 = fig.add_subplot(gs[1], facecolor='none')
        
        # Colormaps
        cmap1 = LinearSegmentedColormap.from_list('custom1',
            ['white', self.COLORS['player1']], N=256)
        cmap2 = LinearSegmentedColormap.from_list('custom2',
            ['white', self.COLORS['player2']], N=256)
        
        # Joueur 1
        im1 = ax1.imshow(matrix1, cmap=cmap1, aspect='auto', vmin=0, vmax=100)
        ax1.set_yticks(range(len(stat_labels)))
        ax1.set_yticklabels(stat_labels, size=11, color='white', fontweight='bold')
        ax1.set_xticks([0])
        ax1.set_xticklabels([self.player1_name], size=16, fontweight='bold', 
                           color='white')
        
        for i, val in enumerate(matrix1):
            color = 'white' if val[0] > 50 else 'black'
            ax1.text(0, i, f'{val[0]:.0f}', ha='center', va='center',
                    size=12, fontweight='bold', color=color)
        
        self._customize_axes(ax1)
        
        # Joueur 2
        im2 = ax2.imshow(matrix2, cmap=cmap2, aspect='auto', vmin=0, vmax=100)
        ax2.set_yticks(range(len(stat_labels)))
        ax2.set_yticklabels([], size=11)
        ax2.set_xticks([0])
        ax2.set_xticklabels([self.player2_name], size=16, fontweight='bold', 
                           color='white')
        
        for i, val in enumerate(matrix2):
            color = 'white' if val[0] > 50 else 'black'
            ax2.text(0, i, f'{val[0]:.0f}', ha='center', va='center',
                    size=12, fontweight='bold', color=color)
        
        self._customize_axes(ax2)
        
        # Titre
        plt.suptitle(f'HEATMAP DÉTAILLÉE\n{self.player1_name} VS {self.player2_name}', 
                    size=25, fontweight='bold', color='white', y=0.96)
        
        # Explication
        fig.text(0.5, 0.91, "Chaque ligne = 1 statistique spécifique | Plus c'est foncé, meilleur est le score", 
                ha='center', va='top', fontsize=10, color='white', 
                style='italic', alpha=0.9)
        
        # Watermark et contexte
        self._add_watermark(fig)
        self._add_comparison_context(fig)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight', facecolor='none')
        plt.close()
    
    def plot_comparison_scatter(self, save_path: str = None):
        """Scatter plot comparatif avec contexte"""
        prog_passes1 = self.analyzer1._get_stat_value('Progressive Passes')
        prog_carries1 = self.analyzer1._get_stat_value('Progressive Carries')
        
        prog_passes2 = self.analyzer2._get_stat_value('Progressive Passes')
        prog_carries2 = self.analyzer2._get_stat_value('Progressive Carries')
        
        fig = plt.figure(figsize=(16, 9))
        self._create_gradient_background(fig)
        
        ax = fig.add_subplot(111, facecolor='none')
        
        # Points des joueurs
        ax.scatter(prog_passes1, prog_carries1, s=300, color=self.COLORS['player1'], 
                  edgecolor=self.COLORS['edge'], linewidth=3, zorder=5,
                  label=self.player1_name)
        
        ax.scatter(prog_passes2, prog_carries2, s=300, color=self.COLORS['player2'], 
                  edgecolor=self.COLORS['edge'], linewidth=3, zorder=5,
                  marker='s', label=self.player2_name)
        
        # Labels des joueurs avec box
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
        
        # Limites
        all_x = [prog_passes1, prog_passes2]
        all_y = [prog_carries1, prog_carries2]
        x_min, x_max = 0, max(max(all_x) + 2, 12)
        y_min, y_max = 0, max(max(all_y) + 2, 10)
        
        ax.set_xlim(x_min, x_max)
        ax.set_ylim(y_min, y_max)
        
        # Style
        ax.set_xlabel('Passes progressives (par 90")', fontsize=16, 
                     color='white', fontweight='bold')
        ax.set_ylabel('Possessions progressives (par 90")', fontsize=16, 
                     color='white', fontweight='bold')
        
        ax.tick_params(axis='both', colors='white', labelsize=14)
        self._customize_axes(ax)
        
        ax.set_xticks(np.arange(x_min, x_max + 1, 1))
        ax.set_yticks(np.arange(y_min, y_max + 1, 1))
        
        # Légende
        legend = ax.legend(fontsize=16, facecolor='black', edgecolor='white',
                          loc='upper left', framealpha=0.8, labelcolor='white')
        legend.get_frame().set_linewidth(2)
        
        # Titre
        plt.title('COMPARAISON\nPasses et Possessions Progressives', 
                 fontsize=25, color='white', fontweight='bold', pad=20)
        
        # Explication
        explanation = "Position sur le graphique = influence offensive | En haut à droite = meilleur contributeur"
        fig.text(0.5, 0.92, explanation, 
                ha='center', va='top', fontsize=10, color='white', 
                style='italic', alpha=0.9)
        
        # Watermark et contexte
        self._add_watermark(fig)
        self._add_comparison_context(fig)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight', facecolor='none')
        plt.close()
    
    def plot_comparison_cards(self, save_path: str = None):
        """Cartes de comparaison côte à côte avec contexte"""
        key_stats = [
            ('Goals', 'BUTS'),
            ('Assists', 'PASSES D.'),
            ('Progressive Passes', 'PASSES PROG.'),
            ('Tackles Won', 'TACLES'),
            ('xG: Expected Goals', 'xG'),
            ('Key Passes', 'PASSES CLÉS')
        ]
        
        fig = plt.figure(figsize=(16, 9))
        self._create_gradient_background(fig)
        
        # Grille 3x4
        for i, (stat_key, stat_label) in enumerate(key_stats):
            val1 = self.analyzer1._get_stat_value(stat_key)
            val2 = self.analyzer2._get_stat_value(stat_key)
            
            # Déterminer le gagnant
            winner_color1 = self.COLORS['player1'] if val1 > val2 else 'white'
            winner_color2 = self.COLORS['player2'] if val2 > val1 else 'white'
            
            # Joueur 1 (gauche)
            ax1 = plt.subplot(3, 4, i*2+1, facecolor='none')
            
            ax1.text(0.5, 0.6, f'{val1:.2f}', 
                    ha='center', va='center', fontsize=32, fontweight='bold',
                    color='white')
            
            ax1.text(0.5, 0.3, stat_label, 
                    ha='center', va='center', fontsize=14, fontweight='bold',
                    color='white')
            
            ax1.text(0.5, 0.15, 'par 90\'', 
                    ha='center', va='center', fontsize=10, style='italic',
                    color='white', alpha=0.7)
            
            if i == 0:
                ax1.text(0.5, 0.9, self.player1_name, 
                        ha='center', va='center', fontsize=14, fontweight='bold',
                        color='white')
            
            ax1.set_xlim(0, 1)
            ax1.set_ylim(0, 1)
            ax1.axis('off')
            
            rect = mpatches.Rectangle((0, 0), 1, 1, linewidth=3, 
                                     edgecolor=winner_color1, facecolor='none', 
                                     transform=ax1.transAxes)
            ax1.add_patch(rect)
            
            # Joueur 2 (droite)
            ax2 = plt.subplot(3, 4, i*2+2, facecolor='none')
            
            ax2.text(0.5, 0.6, f'{val2:.2f}', 
                    ha='center', va='center', fontsize=32, fontweight='bold',
                    color='white')
            
            ax2.text(0.5, 0.3, stat_label, 
                    ha='center', va='center', fontsize=14, fontweight='bold',
                    color='white')
            
            ax2.text(0.5, 0.15, 'par 90\'', 
                    ha='center', va='center', fontsize=10, style='italic',
                    color='white', alpha=0.7)
            
            if i == 0:
                ax2.text(0.5, 0.9, self.player2_name, 
                        ha='center', va='center', fontsize=14, fontweight='bold',
                        color='white')
            
            ax2.set_xlim(0, 1)
            ax2.set_ylim(0, 1)
            ax2.axis('off')
            
            rect = mpatches.Rectangle((0, 0), 1, 1, linewidth=3, 
                                     edgecolor=winner_color2, facecolor='none', 
                                     transform=ax2.transAxes)
            ax2.add_patch(rect)
        
        # Titre
        fig.suptitle(f'COMPARAISON STATS CLÉS\n{self.player1_name} VS {self.player2_name}', 
                    fontsize=25, fontweight='bold', color='white', y=0.98)
        
        # Légende bordures colorées
        legend_text = "Bordure colorée = meilleur dans cette statistique"
        fig.text(0.5, 0.91, legend_text, 
                ha='center', va='top', fontsize=11, color='white', 
                style='italic', alpha=0.9)
        
        # Watermark et contexte
        self._add_watermark(fig)
        self._add_comparison_context(fig)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight', facecolor='none')
        plt.close()