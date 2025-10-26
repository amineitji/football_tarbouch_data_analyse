"""
PlayerComparator V13 - Higher Center Label in Cards
- Reverts bar drawing logic to simple center-outwards (like V10).
- Adjusts the vertical position of the central stat label box upwards.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.colors import LinearSegmentedColormap
from typing import Dict, Tuple, List, Optional
# Ensure the latest PlayerAnalyzer is used
from player_analyzer import PlayerAnalyzer


class PlayerComparator:
    """Compare deux joueurs avec des visualisations 16:9 (V13)."""

    COLORS = {
        'gradient_start': "#000000", 'gradient_end': '#646327', 'player1': '#FF0000',
        'player2': '#0000FF', 'text': '#FFFFFF', 'edge': '#000000',
        'winner': '#00FF00', 'bar_bg': '#333333'
    }

    CONFIDENCE_THRESHOLDS = { 'high': 900, 'medium': 450, 'low': 180 }
    BACKUP_STATS = [
        ('Touches', 'TOUCHES'), ('Carries', 'POSSESSIONS'), ('Ball Recoveries', 'RÉCUP.'),
        ('Passes into Final Third', 'PASSES 1/3'), ('Successful Take-Ons', 'DRIBBLES'),
        ('Passes into Penalty Area', 'PASSES SURFACE')
    ]

    def __init__(self, player1_name: str, player2_name: str,
                 player1_data: pd.DataFrame, player2_data: pd.DataFrame):
        # ... (init code identical to V11/V12) ...
        self.player1_short_name = player1_name.split('(')[0].strip()
        self.player2_short_name = player2_name.split('(')[0].strip()
        self.player1_full_name = player1_name
        self.player2_full_name = player2_name
        pos1 = player1_data['position'].iloc[0] if 'position' in player1_data.columns and not player1_data['position'].empty else 'MF'
        pos2 = player2_data['position'].iloc[0] if 'position' in player2_data.columns and not player2_data['position'].empty else 'MF'
        self.analyzer1 = PlayerAnalyzer(self.player1_short_name, pos1) # Use latest PlayerAnalyzer
        self.analyzer1.load_data(player1_data)
        self.analyzer2 = PlayerAnalyzer(self.player2_short_name, pos2) # Use latest PlayerAnalyzer
        self.analyzer2.load_data(player2_data)
        self.minutes1 = self.analyzer1.minutes if self.analyzer1.minutes is not None else 0.0
        self.minutes2 = self.analyzer2.minutes if self.analyzer2.minutes is not None else 0.0
        self.confidence1 = self._calculate_confidence(self.minutes1)
        self.confidence2 = self._calculate_confidence(self.minutes2)
        print(f"\n📊 Comparaison Initialisée (Comparator V13):")
        print(f"   🔴 {self.player1_full_name:<35} | Pos: {self.analyzer1.position} | Min: {self.minutes1:>5.0f} | Conf: {self.confidence1:.2f}")
        print(f"   🔵 {self.player2_full_name:<35} | Pos: {self.analyzer2.position} | Min: {self.minutes2:>5.0f} | Conf: {self.confidence2:.2f}")

    def _calculate_confidence(self, minutes: float) -> float:
        # ... (Identical V12) ...
        confidence = 1 / (1 + np.exp(-(minutes - 900) / 300)); return confidence

    def _create_gradient_background(self, fig):
        # ... (Identical V12) ...
        gradient = np.linspace(0, 1, 256).reshape(-1, 1); gradient = np.hstack((gradient, gradient))
        cmap = LinearSegmentedColormap.from_list("", [self.COLORS['gradient_start'], self.COLORS['gradient_end']])
        ax_bg = fig.add_axes([0, 0, 1, 1]); ax_bg.axis('off'); ax_bg.imshow(gradient, aspect='auto', cmap=cmap, extent=[0, 1, 0, 1], zorder=-1)

    def _add_watermark(self, fig):
        # ... (Identical V12) ...
        fig.text(0.98, 0.02, '@TarbouchData', fontsize=20, color='white', fontweight='bold', ha='right', va='bottom', alpha=1.0,
                 bbox=dict(boxstyle='round,pad=0.5', facecolor='black', edgecolor='white', linewidth=2, alpha=0.8))

    def _add_comparison_context(self, fig):
        # ... (Identical V12) ...
        context1 = f"Pos: {self.analyzer1.position}" + (f" | {self.analyzer1.season}" if self.analyzer1.season else "") + (f" | {self.analyzer1.competition}" if self.analyzer1.competition else "") + f" | {self.minutes1:.0f} min"
        context2 = f"Pos: {self.analyzer2.position}" + (f" | {self.analyzer2.season}" if self.analyzer2.season else "") + (f" | {self.analyzer2.competition}" if self.analyzer2.competition else "") + f" | {self.minutes2:.0f} min"
        fig.text(0.02, 0.06, f"🔴 {self.player1_short_name}: {context1}", fontsize=11, color='white', ha='left', va='bottom', alpha=0.9)
        fig.text(0.02, 0.02, f"🔵 {self.player2_short_name}: {context2}", fontsize=11, color='white', ha='left', va='bottom', alpha=0.9)

    def _select_valid_stats(self, preferred_stats: List[Tuple[str, str]]) -> List[Tuple[str, str]]:
        # ... (Identical V12) ...
        valid_stats = []; # ... rest is identical ...
        for stat_key, stat_label in preferred_stats:
             val1 = self.analyzer1._get_stat_value(stat_key); val2 = self.analyzer2._get_stat_value(stat_key)
             if val1 > 0 or val2 > 0: valid_stats.append((stat_key, stat_label))
        stats_in_list_keys = {key for key, label in valid_stats}
        if len(valid_stats) < 6:
            for stat_key, stat_label in self.BACKUP_STATS:
                if len(valid_stats) >= 6: break
                if stat_key not in stats_in_list_keys:
                    val1 = self.analyzer1._get_stat_value(stat_key); val2 = self.analyzer2._get_stat_value(stat_key)
                    if val1 > 0 or val2 > 0: valid_stats.append((stat_key, stat_label)); stats_in_list_keys.add(stat_key)
        if len(valid_stats) < 6: print(f"⚠️ Moins de 6 stats valides trouvées ({len(valid_stats)}).")
        return valid_stats[:6]

    def plot_comparison_spider(self, save_path: Optional[str] = None):
        # ... (Identical V12) ...
        if self.analyzer1.df is None or self.analyzer2.df is None: print("⚠️ Spider Comparatif: Données manquantes."); return
        categories = list(PlayerAnalyzer.CATEGORIES.keys()); values1 = [self.analyzer1._get_category_average_normalized(cat) for cat in categories]; values2 = [self.analyzer2._get_category_average_normalized(cat) for cat in categories]; angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
        values1 += values1[:1]; values2 += values2[:1]; angles += angles[:1]
        fig = plt.figure(figsize=(16, 9), facecolor='none'); self._create_gradient_background(fig); ax = fig.add_subplot(111, projection='polar', facecolor='none')
        ax.plot(angles, values1, 'o-', linewidth=4, color=self.COLORS['player1'], markersize=12, markeredgecolor=self.COLORS['edge'], markeredgewidth=2, label=self.player1_full_name, zorder=5, alpha=0.9); ax.fill(angles, values1, alpha=0.2, color=self.COLORS['player1'], zorder=4)
        ax.plot(angles, values2, 's-', linewidth=4, color=self.COLORS['player2'], markersize=12, markeredgecolor=self.COLORS['edge'], markeredgewidth=2, label=self.player2_full_name, zorder=5, alpha=0.9); ax.fill(angles, values2, alpha=0.2, color=self.COLORS['player2'], zorder=4)
        ax.set_ylim(0, 100); ax.set_yticks([25, 50, 75, 100]); ax.set_yticklabels(['25', '50', '75', '100'], color='white', size=14, fontweight='bold'); ax.set_xticks(angles[:-1]); ax.set_xticklabels([])
        ax.grid(True, color='white', linestyle='--', linewidth=2, alpha=0.4); ax.spines['polar'].set_color('white'); ax.spines['polar'].set_linewidth(2.5)
        for i, angle in enumerate(angles[:-1]): ax.text(angle, 115, categories[i], size=18, color="#FFFFFF", fontweight='bold', ha='center', va='center', bbox=dict(boxstyle='round,pad=0.4', fc='black', ec='#FFFFFF', lw=2.5, alpha=0.9))
        comp1 = self.analyzer1.competition or "Comp 1"; comp2 = self.analyzer2.competition or "Comp 2"; title = f'{self.player1_short_name} vs {self.player2_short_name}'; plt.title(title, size=32, fontweight='bold', pad=50, color='white')
        legend = ax.legend(loc='upper left', bbox_to_anchor=(1.15, 1.0), frameon=True, facecolor='black', edgecolor='#FFFFFF', fontsize=14, labelcolor='white', framealpha=0.9); legend.get_frame().set_linewidth(2.5)
        self._add_watermark(fig); self._add_comparison_context(fig); plt.tight_layout(rect=[0, 0.08, 0.85, 0.92])
        if save_path: plt.savefig(save_path, dpi=300, bbox_inches='tight', facecolor=self.COLORS['gradient_end'], edgecolor='black')
        plt.close(fig)

    def plot_comparison_scatter(self, save_path: Optional[str] = None):
        # ... (Identical V12) ...
        if self.analyzer1.df is None or self.analyzer2.df is None: print("⚠️ Scatter Comparatif: Données manquantes."); return
        prog_passes1 = self.analyzer1._get_stat_value('Progressive Passes'); prog_carries1 = self.analyzer1._get_stat_value('Progressive Carries'); prog_passes2 = self.analyzer2._get_stat_value('Progressive Passes'); prog_carries2 = self.analyzer2._get_stat_value('Progressive Carries')
        fig = plt.figure(figsize=(16, 9), facecolor='none'); self._create_gradient_background(fig); ax = fig.add_subplot(111, facecolor='none')
        min_size = 100; size1 = min_size + 400 * self.confidence1; size2 = min_size + 400 * self.confidence2
        ax.scatter(prog_passes1, prog_carries1, s=size1, color=self.COLORS['player1'], edgecolor=self.COLORS['edge'], linewidth=3, zorder=5, marker='o', label=f"{self.player1_full_name}", alpha=0.9)
        ax.scatter(prog_passes2, prog_carries2, s=size2, color=self.COLORS['player2'], edgecolor=self.COLORS['edge'], linewidth=3, zorder=5, marker='s', label=f"{self.player2_full_name}", alpha=0.9)
        ax.text(prog_passes1, prog_carries1 + 0.15, self.player1_short_name, ha='center', va='bottom', fontsize=13, fontweight='bold', color='white', zorder=6, bbox=dict(boxstyle='round,pad=0.3', facecolor=self.COLORS['player1'], edgecolor=self.COLORS['edge'], linewidth=1, alpha=0.8))
        ax.text(prog_passes2, prog_carries2 + 0.15, self.player2_short_name, ha='center', va='bottom', fontsize=13, fontweight='bold', color='white', zorder=6, bbox=dict(boxstyle='round,pad=0.3', facecolor=self.COLORS['player2'], edgecolor=self.COLORS['edge'], linewidth=1, alpha=0.8))
        all_x = [0, prog_passes1, prog_passes2]; all_y = [0, prog_carries1, prog_carries2]; x_max = max(max(all_x) * 1.1, 5); y_max = max(max(all_y) * 1.1, 5)
        ax.set_xlim(0, x_max); ax.set_ylim(0, y_max); ax.set_xlabel('Passes Progressives (par 90 min)', fontsize=16, color='white', fontweight='bold'); ax.set_ylabel('Portées Progressives (par 90 min)', fontsize=16, color='white', fontweight='bold'); ax.tick_params(axis='both', colors='white', labelsize=14)
        for spine in ax.spines.values(): spine.set_edgecolor('white'); spine.set_linewidth(2.5)
        ax.grid(True, color='white', linestyle=':', linewidth=1, alpha=0.3)
        legend = ax.legend(fontsize=14, facecolor='black', edgecolor='white', loc='upper left', framealpha=0.8, labelcolor='white', title="Joueurs (Saison)"); legend.get_frame().set_linewidth(1.5); legend.get_title().set_color('white'); legend.get_title().set_fontweight('bold')
        plt.title('COMPARAISON : PROGRESSION BALLE AU PIED\nPasses vs Portées Progressives', fontsize=24, color='white', fontweight='bold', pad=20)
        self._add_watermark(fig); self._add_comparison_context(fig); plt.tight_layout(rect=[0, 0.08, 1, 0.92])
        if save_path: plt.savefig(save_path, dpi=300, bbox_inches='tight', facecolor=self.COLORS['gradient_end'], edgecolor='black')
        plt.close(fig)

    # === MISE À JOUR plot_comparison_cards ===
    def plot_comparison_cards(self, save_path: Optional[str] = None):
        """Cartes de comparaison V13: Label central plus haut."""
        if self.analyzer1.df is None or self.analyzer2.df is None: print("⚠️ Cartes Comparatives: Données manquantes."); return

        preferred_stats = [
            ('Goals', 'BUTS'), ('Assists', 'PASSES D.'), ('xG: Expected Goals', 'xG'),
            ('Progressive Passes', 'PASSES PROG.'), ('Successful Take-Ons', 'DRIBBLES RÉUSSIS'),
            ('Tackles Won', 'TACLES GAGNÉS')
        ]
        key_stats = self._select_valid_stats(preferred_stats)
        if not key_stats: print("⚠️ Cartes Comparatives: Aucune stat valide sélectionnée."); return

        fig = plt.figure(figsize=(16, 9), facecolor='none'); self._create_gradient_background(fig)
        n_stats = len(key_stats)
        global_max = 0
        for stat_key, _ in key_stats:
            val1 = self.analyzer1._get_stat_value(stat_key); val2 = self.analyzer2._get_stat_value(stat_key)
            global_max = max(global_max, val1, val2)

        # Marge augmentée pour texte externe
        plot_limit = global_max * 1.5 if global_max > 0 else 1.0
        text_offset = plot_limit * 0.03

        for i, (stat_key, stat_label) in enumerate(key_stats):
            val1 = self.analyzer1._get_stat_value(stat_key); val2 = self.analyzer2._get_stat_value(stat_key)
            ax = plt.subplot(n_stats, 1, i + 1, facecolor='none')
            alpha1 = 0.5 + 0.5 * self.confidence1; alpha2 = 0.5 + 0.5 * self.confidence2

            # --- Barres Simples (comme V10/V11) ---
            ax.barh([0], [-val1], height=0.6, color=self.COLORS['player1'], edgecolor=self.COLORS['edge'], linewidth=1.5, alpha=alpha1, zorder=3)
            ax.barh([0], [val2], height=0.6, color=self.COLORS['player2'], edgecolor=self.COLORS['edge'], linewidth=1.5, alpha=alpha2, zorder=3)
            # -------------------------------------

            # Fond gris et ligne centrale
            ax.axhline(0, color=self.COLORS['bar_bg'], linewidth=15, zorder=1, alpha=0.5)
            ax.axvline(0, color='white', linewidth=1, linestyle='--', alpha=0.7, zorder=2)

            # Gagnant
            if val1 > val2: color1, color2 = self.COLORS['winner'], 'white'
            elif val2 > val1: color1, color2 = 'white', self.COLORS['winner']
            else: color1 = color2 = 'white'
            fmt = '.1f%' if '%' in stat_key or 'pct' in stat_key.lower() or 'Percentage' in stat_key else '.2f'

            # Texte Numérique (position externe V10/V11)
            ax.text(-val1 - text_offset, 0, f'{val1:{fmt}}', ha='right', va='center', fontsize=18, fontweight='bold', color=color1, zorder=5)
            ax.text(val2 + text_offset, 0, f'{val2:{fmt}}', ha='left', va='center', fontsize=18, fontweight='bold', color=color2, zorder=5)

            # --- Label Central - Position Y Ajustée ---
            # Mettre une valeur Y > 0 (ex: 0.3) et ajuster va='center' ou va='bottom'
            ax.text(0, 0.7, stat_label.upper(), ha='center', va='center', fontsize=14, fontweight='bold', color='white',
                   bbox=dict(boxstyle='round,pad=0.4', facecolor='black', edgecolor=self.COLORS['edge'], linewidth=1.5, alpha=0.85), zorder=4)
            # ------------------------------------------

            # Noms joueurs (1ère carte) - Position Y ajustée aussi
            if i == 0:
                ax.text(-plot_limit * 0.6, 1.1, f"{self.player1_full_name}", ha='center', va='center', fontsize=14, fontweight='bold', color=self.COLORS['player1']) # Y > 0.8
                ax.text(plot_limit * 0.6, 1.1, f"{self.player2_full_name}", ha='center', va='center', fontsize=14, fontweight='bold', color=self.COLORS['player2']) # Y > 0.8

            # Axes - Ajuster Y Limites si nécessaire
            ax.set_xlim(-plot_limit, plot_limit); ax.set_ylim(-0.8, 1.2); ax.axis('off') # Augmenter limite Y sup

        fig.suptitle(f'COMPARAISON STATS CLÉS (par 90 min)', fontsize=24, fontweight='bold', color='white', y=0.98)
        self._add_watermark(fig); self._add_comparison_context(fig); plt.tight_layout(rect=[0, 0.08, 1, 0.93], h_pad=2.5) # Augmenter h_pad
        if save_path: plt.savefig(save_path, dpi=300, bbox_inches='tight', facecolor=self.COLORS['gradient_end'], edgecolor='black')
        plt.close(fig)
    # =======================================

    def plot_comparison_categories(self, save_path: Optional[str] = None):
        # ... (Identique V12) ...
        if self.analyzer1.df is None or self.analyzer2.df is None: print("⚠️ Barres Catégories: Données manquantes."); return
        categories = list(PlayerAnalyzer.CATEGORIES.keys()); scores1 = [self.analyzer1._get_category_average_normalized(cat) for cat in categories]; scores2 = [self.analyzer2._get_category_average_normalized(cat) for cat in categories]
        fig = plt.figure(figsize=(16, 9), facecolor='none'); self._create_gradient_background(fig); ax = fig.add_subplot(111, facecolor='none')
        y_pos = np.arange(len(categories)); bar_height = 0.35
        bars1 = ax.barh(y_pos + bar_height/2, scores1, height=bar_height, color=self.COLORS['player1'], edgecolor=self.COLORS['edge'], linewidth=1.5, alpha=0.8, label=self.player1_full_name)
        bars2 = ax.barh(y_pos - bar_height/2, scores2, height=bar_height, color=self.COLORS['player2'], edgecolor=self.COLORS['edge'], linewidth=1.5, alpha=0.8, label=self.player2_full_name)
        for bar, score in zip(bars1, scores1): ax.text(score + 2, bar.get_y() + bar.get_height()/2, f'{score:.0f}', va='center', ha='left', fontsize=12, fontweight='bold', color='white')
        for bar, score in zip(bars2, scores2): ax.text(score + 2, bar.get_y() + bar.get_height()/2, f'{score:.0f}', va='center', ha='left', fontsize=12, fontweight='bold', color='white')
        ax.set_yticks(y_pos); ax.set_yticklabels(categories, fontsize=14, color='white', fontweight='bold'); ax.invert_yaxis()
        ax.set_xlim(0, 115); ax.set_xlabel('SCORE NORMALISÉ MOYEN (0-100)', fontsize=16, color='white', fontweight='bold'); ax.tick_params(axis='x', colors='white', labelsize=14); ax.tick_params(axis='y', length=0)
        for spine in ['top', 'right', 'left']: ax.spines[spine].set_visible(False)
        ax.spines['bottom'].set_color('white'); ax.spines['bottom'].set_linewidth(2.5); ax.grid(axis='x', color='white', linestyle=':', linewidth=1, alpha=0.3)
        legend = ax.legend(fontsize=14, facecolor='black', edgecolor='white', loc='lower right', framealpha=0.8, labelcolor='white', title="Joueurs (Saison)"); legend.get_frame().set_linewidth(1.5); legend.get_title().set_color('white')
        plt.title(f'COMPARAISON PAR CATÉGORIE\n{self.player1_short_name} vs {self.player2_short_name}', fontsize=24, color='white', fontweight='bold', pad=20)
        self._add_watermark(fig); self._add_comparison_context(fig); plt.tight_layout(rect=[0, 0.08, 1, 0.92])
        if save_path: plt.savefig(save_path, dpi=300, bbox_inches='tight', facecolor=self.COLORS['gradient_end'], edgecolor='black')
        plt.close(fig)

    def plot_comparison_heatmap(self, save_path: Optional[str] = None):
        # ... (Identique V12) ...
        print(f"🚧 La fonction 'plot_comparison_heatmap' n'est pas encore implémentée."); print(f"   Le fichier {save_path} ne sera pas créé."); pass