"""
PlayerComparator V6 - Avec pondération par minutes jouées
Ajoute un confidence score basé sur le volume de jeu
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.colors import LinearSegmentedColormap
from typing import Dict, Tuple
from player_analyzer import PlayerAnalyzer


class PlayerComparator:
    """Compare deux joueurs avec pondération par minutes jouées"""
    
    COLORS = {
        'gradient_start': "#000000",
        'gradient_end': '#646327',
        'player1': '#FF0000',
        'player2': '#0000FF',
        'text': '#FFFFFF',
        'edge': '#000000',
        'winner': '#00FF00',
        'low_confidence': '#FFA500'  # Orange pour faible confiance
    }
    
    # Seuils de confiance (en minutes jouées)
    CONFIDENCE_THRESHOLDS = {
        'high': 900,      # 10 matchs complets (90min × 10)
        'medium': 450,    # 5 matchs complets
        'low': 180        # 2 matchs complets
    }
    
    def __init__(self, player1_name: str, player2_name: str,
                 player1_data: pd.DataFrame, player2_data: pd.DataFrame):
        self.player1_name = player1_name
        self.player2_name = player2_name
        
        self.analyzer1 = PlayerAnalyzer(player1_name, player1_data['position'].iloc[0] if 'position' in player1_data else 'MF')
        self.analyzer1.load_data(player1_data)
        
        self.analyzer2 = PlayerAnalyzer(player2_name, player2_data['position'].iloc[0] if 'position' in player2_data else 'MF')
        self.analyzer2.load_data(player2_data)
        
        # Extraire les minutes jouées
        self.minutes1 = self._extract_minutes(player1_data)
        self.minutes2 = self._extract_minutes(player2_data)
        
        # Calculer les confidence scores
        self.confidence1 = self._calculate_confidence(self.minutes1)
        self.confidence2 = self._calculate_confidence(self.minutes2)
        
        print(f"\n📊 ANALYSE DES MINUTES JOUÉES :")
        print(f"   🔴 {self.player1_name:<30} : {self.minutes1:>5.0f} min ({self._get_confidence_label(self.confidence1)})")
        print(f"   🔵 {self.player2_name:<30} : {self.minutes2:>5.0f} min ({self._get_confidence_label(self.confidence2)})")
    
    def _extract_minutes(self, df: pd.DataFrame) -> float:
        """
        Extrait les minutes jouées depuis le DataFrame
        Cherche : 'Minutes', '90s', 'Playing Time'
        """
        minutes_cols = ['Minutes', 'Min', 'Playing Time', '90s']
        
        for col in minutes_cols:
            if col in df.columns:
                # Si c'est '90s', multiplier par 90
                if col == '90s':
                    value = pd.to_numeric(df[col].iloc[0], errors='coerce')
                    if not pd.isna(value):
                        return value * 90
                else:
                    value = pd.to_numeric(df[col].iloc[0], errors='coerce')
                    if not pd.isna(value):
                        return value
        
        # Si aucune colonne trouvée, chercher dans les métadonnées
        if 'minutes' in df.columns:
            value = pd.to_numeric(df['minutes'].iloc[0], errors='coerce')
            if not pd.isna(value):
                return value
        
        # Valeur par défaut (assume une saison complète)
        print(f"   ⚠️  Minutes non trouvées, assume 1800 min (20 matchs)")
        return 1800.0
    
    def _calculate_confidence(self, minutes: float) -> float:
        """
        Calcule un score de confiance (0-1) basé sur les minutes jouées
        
        Formule sigmoïde : confidence = 1 / (1 + e^(-(minutes - 900) / 300))
        
        - < 180 min   → Très faible (~0.1)
        - 180-450 min → Faible (~0.3)
        - 450-900 min → Moyen (~0.5-0.8)
        - > 900 min   → Élevé (~0.9+)
        """
        # Sigmoïde centrée sur 900 minutes (10 matchs)
        confidence = 1 / (1 + np.exp(-(minutes - 900) / 300))
        return confidence
    
    def _get_confidence_label(self, confidence: float) -> str:
        """Retourne un label textuel pour le confidence score"""
        if confidence >= 0.85:
            return "✅ Confiance élevée"
        elif confidence >= 0.6:
            return "⚠️  Confiance moyenne"
        elif confidence >= 0.3:
            return "⚠️  Confiance faible"
        else:
            return "❌ Confiance très faible"
    
    def _apply_confidence_weight(self, value1: float, value2: float) -> Tuple[float, float]:
        """
        Applique une pondération basée sur la confiance
        
        Si un joueur a peu de minutes, ses stats sont moins fiables
        → On les tempère légèrement vers la moyenne
        """
        # Calculer l'écart entre les deux valeurs
        diff = abs(value1 - value2)
        avg = (value1 + value2) / 2
        
        # Si confiance faible, réduire l'écart (rapprocher de la moyenne)
        weighted_value1 = value1 * self.confidence1 + avg * (1 - self.confidence1)
        weighted_value2 = value2 * self.confidence2 + avg * (1 - self.confidence2)
        
        return weighted_value1, weighted_value2
    
    def _get_weighted_comparison_symbol(self) -> str:
        """
        Retourne un symbole indiquant la fiabilité de la comparaison
        """
        min_confidence = min(self.confidence1, self.confidence2)
        
        if min_confidence >= 0.85:
            return "✅"  # Comparaison très fiable
        elif min_confidence >= 0.6:
            return "⚠️"  # Comparaison moyennement fiable
        else:
            return "❌"  # Comparaison peu fiable
    
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
        """Ajoute le contexte de comparaison avec minutes jouées"""
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
    
    def _add_confidence_indicator(self, fig):
        """Ajoute un indicateur de fiabilité de la comparaison"""
        symbol = self._get_weighted_comparison_symbol()
        min_confidence = min(self.confidence1, self.confidence2)
        
        if min_confidence >= 0.85:
            reliability = "Comparaison fiable (échantillon suffisant)"
            color = '#00FF00'
        elif min_confidence >= 0.6:
            reliability = "Comparaison moyennement fiable (échantillon moyen)"
            color = '#FFA500'
        else:
            reliability = "⚠️ Comparaison peu fiable (échantillon faible)"
            color = '#FF0000'
        
        fig.text(0.5, 0.01, f"{symbol} {reliability}", 
                ha='center', va='bottom', fontsize=12, color=color, 
                fontweight='bold', alpha=0.95,
                bbox=dict(boxstyle='round,pad=0.4', facecolor='black', 
                         edgecolor=color, linewidth=2, alpha=0.8))
    
    def plot_comparison_spider(self, save_path: str = None):
        """Spider radar superposé avec pondération par minutes"""
        categories = list(self.analyzer1.CATEGORIES.keys())
        
        values1 = [self.analyzer1._get_category_average_normalized(cat) for cat in categories]
        values2 = [self.analyzer2._get_category_average_normalized(cat) for cat in categories]
        
        angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
        values1 += values1[:1]
        values2 += values2[:1]
        angles += angles[:1]
        
        fig = plt.figure(figsize=(16, 9), facecolor=self.COLORS['gradient_end'])
        self._create_gradient_background(fig)
        
        ax = fig.add_subplot(111, projection='polar', facecolor='none')
        
        # Transparence basée sur la confiance
        alpha1 = 0.9 * self.confidence1 + 0.4 * (1 - self.confidence1)
        alpha2 = 0.9 * self.confidence2 + 0.4 * (1 - self.confidence2)
        
        ax.plot(angles, values1, 'o-', linewidth=4, color=self.COLORS['player1'],
                markersize=16, markeredgecolor=self.COLORS['edge'], markeredgewidth=2, 
                label=f"{self.player1_name} ({self.minutes1:.0f} min)", zorder=6, alpha=alpha1)
        ax.fill(angles, values1, alpha=0.25 * self.confidence1, color=self.COLORS['player1'], zorder=5)
        
        ax.plot(angles, values2, 's-', linewidth=4, color=self.COLORS['player2'],
                markersize=16, markeredgecolor=self.COLORS['edge'], markeredgewidth=2,
                label=f"{self.player2_name} ({self.minutes2:.0f} min)", zorder=6, alpha=alpha2)
        ax.fill(angles, values2, alpha=0.25 * self.confidence2, color=self.COLORS['player2'], zorder=5)
        
        ax.set_ylim(0, 100)
        ax.set_yticks([25, 50, 75, 100])
        ax.set_yticklabels(['25', '50', '75', '100'], size=14, 
                          color='white', fontweight='bold')
        
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(categories, size=16, fontweight='bold', color='white')
        
        ax.grid(color='white', linestyle='-', linewidth=2, alpha=0.5)
        ax.spines['polar'].set_color('white')
        ax.spines['polar'].set_linewidth(2.5)
        
        plt.title(f'COMPARAISON RADAR (pondéré par temps de jeu)\n{self.player1_name} VS {self.player2_name}', 
                 size=26, fontweight='bold', pad=60, color='white')
        
        explanation = "Scores normalisés par catégorie (0-100) | Transparence = confiance basée sur les minutes jouées"
        fig.text(0.5, 0.92, explanation, 
                ha='center', va='top', fontsize=11, color='white', 
                style='italic', alpha=0.9)
        
        legend = plt.legend(loc='upper right', bbox_to_anchor=(1.3, 1.12), 
                           fontsize=14, facecolor='black', edgecolor='white',
                           framealpha=0.8, labelcolor='white')
        legend.get_frame().set_linewidth(2.5)
        
        self._add_watermark(fig)
        self._add_comparison_context(fig)
        self._add_confidence_indicator(fig)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight', 
                       facecolor=self.COLORS['gradient_end'])
        plt.close()
    
    def plot_comparison_categories(self, save_path: str = None):
        """Barres groupées avec indication de confiance"""
        categories = list(self.analyzer1.CATEGORIES.keys())
        
        values1 = [self.analyzer1._get_category_average_normalized(cat) for cat in categories]
        values2 = [self.analyzer2._get_category_average_normalized(cat) for cat in categories]
        
        x = np.arange(len(categories))
        width = 0.35
        
        fig = plt.figure(figsize=(16, 9), facecolor=self.COLORS['gradient_end'])
        self._create_gradient_background(fig)
        
        ax = fig.add_subplot(111, facecolor='none')
        
        # Transparence basée sur la confiance
        alpha1 = 0.8 * self.confidence1 + 0.4 * (1 - self.confidence1)
        alpha2 = 0.8 * self.confidence2 + 0.4 * (1 - self.confidence2)
        
        bars1 = ax.bar(x - width/2, values1, width, 
                      label=f"{self.player1_name} ({self.minutes1:.0f} min)",
                      color=self.COLORS['player1'], edgecolor=self.COLORS['edge'], 
                      linewidth=2, alpha=alpha1)
        bars2 = ax.bar(x + width/2, values2, width, 
                      label=f"{self.player2_name} ({self.minutes2:.0f} min)",
                      color=self.COLORS['player2'], edgecolor=self.COLORS['edge'], 
                      linewidth=2, alpha=alpha2)
        
        for bars in [bars1, bars2]:
            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2, height + 2,
                       f'{height:.0f}', ha='center', va='bottom', size=14,
                       fontweight='bold', color='white')
        
        ax.set_xlabel('CATÉGORIES', size=16, fontweight='bold', color='white')
        ax.set_ylabel('SCORE NORMALISÉ (0-100)', size=16, fontweight='bold', color='white')
        ax.set_xticks(x)
        ax.set_xticklabels(categories, size=14, fontweight='bold', color='white')
        ax.set_ylim(0, 115)
        
        ax.tick_params(axis='both', colors='white', labelsize=14)
        
        ax.axhline(50, color='white', linestyle='--', linewidth=2, alpha=0.6)
        
        ax.grid(axis='y', color='white', linestyle='--', linewidth=1, alpha=0.3)
        self._customize_axes(ax)
        
        legend = ax.legend(fontsize=14, facecolor='black', edgecolor='white',
                          loc='upper left', framealpha=0.8, labelcolor='white')
        legend.get_frame().set_linewidth(2)
        
        plt.title(f'COMPARAISON PAR CATÉGORIES (pondéré)\n{self.player1_name} VS {self.player2_name}', 
                 fontsize=25, color='white', fontweight='bold', pad=20)
        
        explanation = "Barres plus transparentes = moins de minutes jouées = moins de confiance"
        fig.text(0.5, 0.92, explanation, 
                ha='center', va='top', fontsize=11, color='white', 
                style='italic', alpha=0.9)
        
        self._add_watermark(fig)
        self._add_comparison_context(fig)
        self._add_confidence_indicator(fig)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight', 
                       facecolor=self.COLORS['gradient_end'])
        plt.close()
    
    def plot_comparison_scatter(self, save_path: str = None):
        """Scatter plot comparatif avec taille basée sur les minutes"""
        prog_passes1 = self.analyzer1._get_stat_value('Progressive Passes')
        prog_carries1 = self.analyzer1._get_stat_value('Progressive Carries')
        
        prog_passes2 = self.analyzer2._get_stat_value('Progressive Passes')
        prog_carries2 = self.analyzer2._get_stat_value('Progressive Carries')
        
        fig = plt.figure(figsize=(16, 9), facecolor=self.COLORS['gradient_end'])
        self._create_gradient_background(fig)
        
        ax = fig.add_subplot(111, facecolor='none')
        
        # Taille des points basée sur les minutes (plus de minutes = plus gros point)
        size1 = 300 * (0.5 + 0.5 * self.confidence1)
        size2 = 300 * (0.5 + 0.5 * self.confidence2)
        
        ax.scatter(prog_passes1, prog_carries1, s=size1, color=self.COLORS['player1'], 
                  edgecolor=self.COLORS['edge'], linewidth=3, zorder=5,
                  label=f"{self.player1_name} ({self.minutes1:.0f} min)",
                  alpha=0.9)
        
        ax.scatter(prog_passes2, prog_carries2, s=size2, color=self.COLORS['player2'], 
                  edgecolor=self.COLORS['edge'], linewidth=3, zorder=5,
                  marker='s', label=f"{self.player2_name} ({self.minutes2:.0f} min)",
                  alpha=0.9)
        
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
        x_min, x_max = 0, max(max(all_x) + 2, 12)
        y_min, y_max = 0, max(max(all_y) + 2, 10)
        
        ax.set_xlim(x_min, x_max)
        ax.set_ylim(y_min, y_max)
        
        ax.set_xlabel('Passes progressives (par 90")', fontsize=16, 
                     color='white', fontweight='bold')
        ax.set_ylabel('Possessions progressives (par 90")', fontsize=16, 
                     color='white', fontweight='bold')
        
        ax.tick_params(axis='both', colors='white', labelsize=14)
        self._customize_axes(ax)
        
        ax.set_xticks(np.arange(x_min, x_max + 1, 1))
        ax.set_yticks(np.arange(y_min, y_max + 1, 1))
        
        legend = ax.legend(fontsize=14, facecolor='black', edgecolor='white',
                          loc='upper left', framealpha=0.8, labelcolor='white')
        legend.get_frame().set_linewidth(2)
        
        plt.title('COMPARAISON\nPasses et Possessions Progressives (taille = minutes)', 
                 fontsize=24, color='white', fontweight='bold', pad=20)
        
        explanation = "Taille du point = volume de minutes jouées | Plus gros = plus fiable"
        fig.text(0.5, 0.92, explanation, 
                ha='center', va='top', fontsize=10, color='white', 
                style='italic', alpha=0.9)
        
        self._add_watermark(fig)
        self._add_comparison_context(fig)
        self._add_confidence_indicator(fig)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight', 
                       facecolor=self.COLORS['gradient_end'])
        plt.close()
    
    def plot_comparison_cards(self, save_path: str = None):
        """Barres symétriques avec surlignage du gagnant et indicateur de confiance"""
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
        
        n_stats = len(key_stats)
        
        for i, (stat_key, stat_label) in enumerate(key_stats):
            val1 = self.analyzer1._get_stat_value(stat_key)
            val2 = self.analyzer2._get_stat_value(stat_key)
            
            # Déterminer le max pour la normalisation
            max_val = max(val1, val2) if max(val1, val2) > 0 else 1
            
            ax = plt.subplot(n_stats, 1, i+1, facecolor='none')
            
            # Transparence basée sur la confiance
            alpha1 = 0.8 * self.confidence1 + 0.4 * (1 - self.confidence1)
            alpha2 = 0.8 * self.confidence2 + 0.4 * (1 - self.confidence2)
            
            # Barres symétriques
            bar1 = ax.barh([0], [-val1], height=0.6, 
                          color=self.COLORS['player1'], 
                          edgecolor=self.COLORS['edge'], 
                          linewidth=2, alpha=alpha1)
            
            bar2 = ax.barh([0], [val2], height=0.6, 
                          color=self.COLORS['player2'], 
                          edgecolor=self.COLORS['edge'], 
                          linewidth=2, alpha=alpha2)
            
            # Texte des valeurs avec surlignage vert pour le gagnant
            if val1 > val2:
                color1 = self.COLORS['winner']
                color2 = 'white'
            elif val2 > val1:
                color1 = 'white'
                color2 = self.COLORS['winner']
            else:
                color1 = color2 = 'white'
            
            # Valeur joueur 1 (gauche)
            ax.text(-val1 - max_val*0.05, 0, f'{val1:.2f}', 
                   ha='right', va='center', fontsize=18, fontweight='bold',
                   color=color1)
            
            # Valeur joueur 2 (droite)
            ax.text(val2 + max_val*0.05, 0, f'{val2:.2f}', 
                   ha='left', va='center', fontsize=18, fontweight='bold',
                   color=color2)
            
            # Label stat au centre
            ax.text(0, 0, stat_label, 
                   ha='center', va='center', fontsize=14, fontweight='bold',
                   color='white',
                   bbox=dict(boxstyle='round,pad=0.5', facecolor='black', 
                            edgecolor='white', linewidth=2, alpha=0.9))
            
            # Noms des joueurs en haut avec minutes
            if i == 0:
                ax.text(-max_val*0.5, 0.8, f"{self.player1_name}\n({self.minutes1:.0f} min)", 
                       ha='center', va='center', fontsize=14, fontweight='bold',
                       color=self.COLORS['player1'])
                ax.text(max_val*0.5, 0.8, f"{self.player2_name}\n({self.minutes2:.0f} min)", 
                       ha='center', va='center', fontsize=14, fontweight='bold',
                       color=self.COLORS['player2'])
            
            # Style
            ax.set_xlim(-max_val*1.3, max_val*1.3)
            ax.set_ylim(-0.5, 0.5)
            ax.axis('off')
        
        # Titre
        fig.suptitle(f'COMPARAISON STATS CLÉS (pondéré)\n{self.player1_name} VS {self.player2_name}', 
                    fontsize=24, fontweight='bold', color='white', y=0.98)
        
        # Légende
        legend_text = "🟢 Vert = Meilleur | Transparence = confiance | Valeurs par 90'"
        fig.text(0.5, 0.91, legend_text, 
                ha='center', va='top', fontsize=11, color='white', 
                style='italic', alpha=0.9)
        
        self._add_watermark(fig)
        self._add_comparison_context(fig)
        self._add_confidence_indicator(fig)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight', 
                       facecolor=self.COLORS['gradient_end'])
        plt.close()
    
    def plot_comparison_heatmap(self, save_path: str = None):
        """
        Heatmap pondérée avec indicateur de confiance
        Reprend la logique de l'ancienne version mais avec pondération
        """
        # Cette méthode peut être implémentée plus tard si nécessaire
        pass