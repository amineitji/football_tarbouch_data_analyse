"""
PlayerAnalyzer V24 - Évaluation Très Exigeante via Benchmark Hybride
- Le 90e percentile (Standard) correspond à un score normalisé de 85.
- Un benchmark "Élite" (Standard * 1.30) correspond à 100.
- Normalisation non linéaire (Power=2.0) sous le Standard, linéaire au-dessus.
- Conserve la pondération (V16), pénalité d'inconsistance (V23), seuils très stricts (V22).
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.colors import LinearSegmentedColormap
from typing import Dict, List, Optional, Tuple
import warnings
import re

warnings.filterwarnings('ignore')

plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans', 'Helvetica']


class PlayerAnalyzer:
    """Analyseur tactique V24: Benchmark Hybride + Power 2.0 + CapIndiv + Pondéré + StdDev Penalty + Seuils Très Stricts"""

    # Standards = 90e percentile (INCHANGÉ)
    POSITION_STANDARDS = {
        'DF': { 'Passing': [63.86, 5.69, 5.79, 0.15, 0.13], 'Shooting': [0.13, 1.10, 0.15, 0.10, 0.10],'Creation': [0.15, 2.64, 0.15, 0.15, 0.15], 'Defense': [2.71, 2.71, 1.63, 1.78, 4.86],'Possession': [2.11, 2.66, 2.66, 1.08, 2.66], },
        'MF': { 'Passing': [57.47, 7.28, 6.59, 0.26, 0.22], 'Shooting': [0.28, 2.40, 0.26, 0.23, 0.23],'Creation': [0.26, 4.33, 0.26, 0.26, 0.26], 'Defense': [3.03, 3.03, 1.52, 1.72, 2.10],'Possession': [3.82, 3.22, 3.22, 1.67, 3.22], },
        'FW': { 'Passing': [33.43, 4.49, 10.92, 0.33, 0.27], 'Shooting': [0.56, 3.38, 0.33, 0.47, 0.47],'Creation': [0.33, 4.64, 0.33, 0.33, 0.33], 'Defense': [2.00, 2.00, 0.71, 1.43, 1.34],'Possession': [6.40, 5.05, 5.05, 2.62, 5.05], },
        'GK': { 'Passing': [30, 3, 2, 0.2, 0.05], 'Shooting': [0, 0, 0, 0, 0],'Creation': [0, 0, 0, 0, 0], 'Defense': [0, 0, 1, 1, 3], 'Possession': [40, 20, 0.5, 0, 0] }
    }

    # Poids des Statistiques par Poste (INCHANGÉ - V16)
    STAT_WEIGHTS = {
        'GK': { 'Defense': {'Save pct': 2.0, 'PSxG_net': 2.0, 'Crosses_Stopped_pct': 1.5}, 'Passing': {'Launched_Cmp_pct': 1.5, 'Passes_Launch_pct': 1.5} },
        'DF': { 'Defense': {'Tackles Won': 1.5, 'Interceptions': 1.5, 'Blocks': 1.0, 'Clearances': 1.0, 'Aerials Won pct': 1.5}, 'Passing': {'Progressive Passes': 1.5, 'Passes Completed pct': 1.0}, 'Possession': {'Progressive Carries': 1.0, 'Carries into Final Third': 1.0} },
        'MF': { 'Passing': {'Progressive Passes': 2.0, 'Key Passes': 1.5, 'xA: Expected Assists': 1.5, 'Passes into Final Third': 1.0}, 'Creation': {'Shot-Creating Actions': 1.5, 'Goal-Creating Actions': 1.5, 'Passes into Penalty Area': 1.5, 'Through Balls': 1.0}, 'Possession': {'Progressive Carries': 1.5, 'Successful Take-Ons': 1.5, 'Carries into Final Third': 1.0, 'Touches': 0.5}, 'Defense': {'Tackles Won': 1.0, 'Interceptions': 1.0, 'Ball Recoveries': 1.0}, 'Shooting': {'Goals': 1.0, 'xG: Expected Goals': 1.0} },
        'FW': { 'Shooting': {'Goals': 2.0, 'npxG: Non-Penalty xG': 2.0, 'Shots on Target pct': 1.5, 'Shots Total': 1.0}, 'Creation': {'Assists': 1.5, 'Shot-Creating Actions': 1.5, 'Goal-Creating Actions': 1.5, 'Passes into Penalty Area': 1.0}, 'Possession': {'Touches_Att_Pen': 2.0, 'Successful Take-Ons': 1.5, 'Progressive Passes Rec': 1.5, 'Progressive Carries': 1.0},'Passing': {'Key Passes': 1.0, 'xA: Expected Assists': 1.0}, 'Defense': {'Tackles_Att_3rd': 1.0, 'Blocks': 0.5} }
    }

    # Seuils TRÈS STRICTS (INCHANGÉ - V22)
    THRESHOLDS = {
        'GK': {'elite': 90, 'good': 70, 'acceptable': 50},
        'DF': {'elite': 90, 'good': 70, 'acceptable': 50},
        'MF': {'elite': 90, 'good': 70, 'acceptable': 50},
        'FW': {'elite': 90, 'good': 70, 'acceptable': 50}
    }

    # Noms des stats ATTENDUS (INCHANGÉ)
    CATEGORIES = {
         'Passing': ['Passes Completed', 'Progressive Passes', 'Passes into Final Third', 'Key Passes', 'xA: Expected Assists'],
         'Shooting': ['Goals', 'Shots Total', 'Shots on Target', 'xG: Expected Goals', 'npxG: Non-Penalty xG'],
         'Creation': ['Assists', 'Shot-Creating Actions', 'Goal-Creating Actions', 'Through Balls', 'Passes into Penalty Area'],
         'Defense': ['Tackles', 'Tackles Won', 'Interceptions', 'Blocks', 'Ball Recoveries'],
         'Possession': ['Touches', 'Carries', 'Progressive Carries', 'Successful Take-Ons', 'Carries into Final Third']
    }

    COLORS = {
        'gradient_start': "#000000", 'gradient_end': "#646327", 'points': '#FF0000',
        'text': '#FFFFFF', 'edge': '#000000'
    }

    # === Paramètres de Normalisation Hybride ===
    NORMALIZATION_POWER = 2.0 # Puissance pour la partie < Standard
    STANDARD_SCORE_TARGET = 85 # Score correspondant au 90e percentile
    ELITE_BENCHMARK_FACTOR = 1.30 # Facteur multiplicatif pour définir le benchmark Elite (score 100)
    CONSISTENCY_PENALTY_FACTOR = 0.20 # Pénalité pour inconsistance (inchangé)
    # ==========================================

    def __init__(self, player_name: str, position: str):
        self.player_name = player_name
        self.position = self._normalize_position(position)
        self.df: Optional[pd.DataFrame] = None; self.stats: Dict[str, object] = {}
        self.season: Optional[str] = None; self.competition: Optional[str] = None
        self.minutes: Optional[float] = None
        self.thresholds = self.THRESHOLDS.get(self.position, self.THRESHOLDS['MF'])
        print(f"ℹ️ Analyzer V24 (Benchmark Hybride {self.STANDARD_SCORE_TARGET}/{self.ELITE_BENCHMARK_FACTOR*100:.0f}pct + Pwr{self.NORMALIZATION_POWER}+Pen{self.CONSISTENCY_PENALTY_FACTOR}+Wgt+Strict90) initialisé pour {self.player_name}, Poste: {self.position}, Seuils: {self.thresholds}")


    # --- Méthodes internes (_normalize_position, load_data, etc.) ---
    # --- restent les mêmes que V21/V22 ---
    # --- SAUF _normalize_stat ET _get_category_average_normalized ---

    def _normalize_position(self, position: str) -> str:
        pos = str(position).upper(); # ... (Identique V21) ...
        if 'GK' in pos: return 'GK'
        elif any(x in pos for x in ['DF', 'CB', 'LB', 'RB', 'FB', 'WB']): return 'DF'
        elif any(x in pos for x in ['FW', 'ST', 'LW', 'RW', 'AM']): return 'FW'
        else: return 'MF'

    def load_data(self, df: pd.DataFrame):
        # ... (Identique V21) ...
        if df is None or df.empty: print("⚠️ Erreur: Le DataFrame fourni est vide ou None."); return
        self.df = df.iloc[[0]].copy(); self.stats = {}
        for col in self.df.columns:
            try: numeric_val = pd.to_numeric(self.df[col].iloc[0], errors='coerce'); self.stats[col] = float(numeric_val) if not pd.isna(numeric_val) else self.df[col].iloc[0]
            except Exception: self.stats[col] = self.df[col].iloc[0]
        self.season = self.stats.get('season', None); self.competition = self.stats.get('competition', None)
        minutes_val = None
        for key in ['minutes_played', 'Minutes', 'Min', '90s']:
            if key in self.stats: numeric_min = pd.to_numeric(self.stats[key], errors='coerce');
            if not pd.isna(numeric_min): minutes_val = numeric_min * 90 if key == '90s' else numeric_min; break
        self.minutes = minutes_val
        print(f"📊 Données chargées. Stats: {len(self.stats)}. Minutes: {self.minutes}")

    def _create_gradient_background(self, fig):
        # ... (Identique V21) ...
        gradient = np.linspace(0, 1, 256).reshape(-1, 1); gradient = np.hstack((gradient, gradient))
        cmap = LinearSegmentedColormap.from_list("", [self.COLORS['gradient_start'], self.COLORS['gradient_end']])
        ax_bg = fig.add_axes([0, 0, 1, 1]); ax_bg.axis('off')
        ax_bg.imshow(gradient, aspect='auto', cmap=cmap, extent=[0, 1, 0, 1], zorder=-1)

    def _customize_axes(self, ax):
        # ... (Identique V21) ...
         for spine in ax.spines.values(): spine.set_edgecolor('white'); spine.set_linewidth(2.5)

    def _add_watermark(self, fig):
        # ... (Identique V21) ...
         fig.text(0.98, 0.02, '@TarbouchData', fontsize=20, color='white', fontweight='bold', ha='right', va='bottom', alpha=1.0,
                 bbox=dict(boxstyle='round,pad=0.5', facecolor='black', edgecolor='white', linewidth=2, alpha=0.8))

    def _add_context_info(self, fig):
        # ... (Identique V21, label mis à jour pour V24) ...
        context_parts = [f"Pos: {self.position}"]
        if self.season: context_parts.append(f"Saison: {self.season}")
        if self.competition: context_parts.append(str(self.competition))
        if self.minutes is not None: context_parts.append(f"{self.minutes:.0f} min")
        context_text = " | ".join(context_parts) + f" | Eval Hybride Pwr{self.NORMALIZATION_POWER}+Pen{self.CONSISTENCY_PENALTY_FACTOR}+Wgt" # Mention évaluation
        fig.text(0.02, 0.02, context_text, fontsize=9, color='white', fontweight='normal', ha='left', va='bottom', alpha=0.9)

    def _clean_stat_name(self, stat_name: str) -> str:
        # ... (Identique V21) ...
        cleaned = re.sub(r'[^\w%:]+', '_', stat_name); cleaned = cleaned.replace('%', 'pct').replace(':', '').strip('_'); return cleaned

    def _get_stat_value(self, expected_stat_name: str) -> float:
        # ... (Identique V21) ...
        if not self.stats: return 0.0
        expected_lower = expected_stat_name.lower()
        for col_name, value in self.stats.items():
            if col_name.lower() == expected_lower:
                numeric_value = pd.to_numeric(value, errors='coerce'); return float(numeric_value) if not pd.isna(numeric_value) else 0.0
        cleaned_expected_name = self._clean_stat_name(expected_stat_name).lower()
        for col_name, value in self.stats.items():
            cleaned_col_name = self._clean_stat_name(col_name).lower()
            if cleaned_col_name == cleaned_expected_name:
                numeric_value = pd.to_numeric(value, errors='coerce'); return float(numeric_value) if not pd.isna(numeric_value) else 0.0
        simple_name = expected_lower.replace('_pct','').replace('percentage','')
        if simple_name != expected_lower:
             for col_name, value in self.stats.items():
                 if col_name.lower() == simple_name:
                    numeric_value = pd.to_numeric(value, errors='coerce'); return float(numeric_value) if not pd.isna(numeric_value) else 0.0
        return 0.0

    # === MISE À JOUR: Normalisation Hybride ===
    def _normalize_stat(self, value: float, standard_benchmark: float) -> float:
        """Normalise une valeur sur 0-100 en utilisant l'échelle hybride."""
        if standard_benchmark <= 0: return 0.0 # Éviter division par zéro
        
        elite_benchmark = standard_benchmark * self.ELITE_BENCHMARK_FACTOR
        
        if value <= 0:
            normalized = 0.0
        elif value <= standard_benchmark:
            # Partie non linéaire mappée sur 0 - STANDARD_SCORE_TARGET
            ratio = value / standard_benchmark
            scaled_ratio = ratio ** self.NORMALIZATION_POWER
            normalized = scaled_ratio * self.STANDARD_SCORE_TARGET
        else: # value > standard_benchmark
            # Partie linéaire mappée sur STANDARD_SCORE_TARGET - 100
            # Calculer la proportion de la distance entre Standard et Elite couverte
            # Assurer que elite_benchmark > standard_benchmark pour éviter division par zéro
            range_diff = elite_benchmark - standard_benchmark
            if range_diff <= 0: # Si Elite <= Standard, plafonner à STANDARD_SCORE_TARGET
                normalized = self.STANDARD_SCORE_TARGET
            else:
                proportion_above_standard = (value - standard_benchmark) / range_diff
                # Limiter cette proportion à 1 (on ne dépasse pas 100)
                capped_proportion = min(1.0, proportion_above_standard)
                # Ajouter la proportion de la plage restante (100 - STANDARD_SCORE_TARGET)
                normalized = self.STANDARD_SCORE_TARGET + (100.0 - self.STANDARD_SCORE_TARGET) * capped_proportion

        # Assurer que le résultat final est bien entre 0 et 100
        return max(0.0, min(normalized, 100.0))
    # =========================================

    def _get_category_stats_normalized(self, category: str) -> Dict[str, Tuple[float, float, float]]:
        # Utilise la nouvelle fonction _normalize_stat (hybride)
        stats_in_category = self.CATEGORIES.get(category, []); standards = self.POSITION_STANDARDS.get(self.position, {}).get(category, []); weights = self.STAT_WEIGHTS.get(self.position, {}).get(category, {})
        result = {}
        for i, stat_name in enumerate(stats_in_category):
            raw_value = self._get_stat_value(stat_name)
            # Applique la normalisation hybride
            normalized_value = self._normalize_stat(raw_value, standards[i]) if i < len(standards) else 0.0
            stat_weight = weights.get(stat_name, 1.0)
            result[stat_name] = (raw_value, normalized_value, stat_weight) # norm_val <= 100
        return result

    def _get_category_average_normalized(self, category: str) -> float:
        # Calcul pondéré + Pénalité d'écart-type (inchangé V23)
        stats_data = self._get_category_stats_normalized(category); # Récupère (raw, norm_hybride, weight)
        if not stats_data: return 0.0
        weighted_scores = []; individual_norm_scores = []; total_weight = 0.0
        for stat_name, (raw_val, norm_val, weight) in stats_data.items():
             if weight > 0: weighted_scores.append(norm_val * weight); individual_norm_scores.append(norm_val); total_weight += weight
        if total_weight == 0 or not individual_norm_scores :
             norm_vals_all = [norm_val for _, norm_val, _ in stats_data.values()]; return np.mean(norm_vals_all) if norm_vals_all else 0.0
        weighted_average = sum(weighted_scores) / total_weight
        std_dev = np.std(individual_norm_scores, ddof=0) if len(individual_norm_scores) > 1 else 0.0
        penalty_reduction = self.CONSISTENCY_PENALTY_FACTOR * (std_dev / 100.0)
        final_score = weighted_average * (1.0 - penalty_reduction)
        final_score = max(0.0, min(final_score, 100.0))
        # print(f"   => Cat: {category} | MoyPond: {weighted_average:.1f} | StdDev: {std_dev:.1f} | Penalty: {penalty_reduction:.2f} | ScoreFinal: {final_score:.0f}")
        return final_score

    # --- Méthodes de Plotting (inchangées en structure) ---
    # Elles utiliseront les nouveaux scores finaux (hybrides + pénalité).

    def plot_spider_radar(self, save_path: Optional[str] = None):
        # ... (Identique V21, utilisera les nouveaux scores finaux) ...
        if self.df is None or not self.stats: print("⚠️ Spider Radar: Données non chargées."); return
        categories=list(self.CATEGORIES.keys()); values_normalized=[self._get_category_average_normalized(cat) for cat in categories]
        if all(v == 0 for v in values_normalized): print("⚠️ Spider Radar: Scores finaux à 0.")
        angles=np.linspace(0, 2*np.pi, len(categories), endpoint=False).tolist(); values_normalized+=values_normalized[:1]; angles+=angles[:1]
        fig=plt.figure(figsize=(16, 9), facecolor='none'); self._create_gradient_background(fig); ax=fig.add_subplot(111, projection='polar', facecolor='none')
        ax.plot(angles, values_normalized, 'o-', linewidth=4, color=self.COLORS['points'], markersize=14, markeredgecolor=self.COLORS['edge'], markeredgewidth=2.5, label=f"{self.player_name}", zorder=5, alpha=0.9)
        ax.fill(angles, values_normalized, alpha=0.25, color=self.COLORS['points'], zorder=4)
        ax.set_ylim(0, 100); ax.set_xticks(angles[:-1]); ax.set_xticklabels([])
        ax.set_yticks([20, 40, 60, 80, 100]); ax.set_yticklabels(['20', '40', '60', '80', '100'], color='white', size=14, fontweight='bold')
        ax.grid(True, color='white', linestyle='--', linewidth=2, alpha=0.4); ax.spines['polar'].set_color('white'); ax.spines['polar'].set_linewidth(3)
        for i, angle in enumerate(angles[:-1]): ax.text(angle, 115, categories[i], size=18, color="#FFFFFF", fontweight='bold', ha='center', va='center', bbox=dict(boxstyle='round,pad=0.4', fc='black', ec='#FFFFFF', lw=2.5, alpha=0.9))
        title = f'{self.player_name}' + (f' | {self.competition}' if self.competition else '') + f''; plt.title(title, size=24, fontweight='bold', pad=50, color='white')
        legend = ax.legend(loc='upper left', bbox_to_anchor=(1.15, 1.0), frameon=True, facecolor='black', edgecolor='#FFFFFF', fontsize=14, labelcolor='white', framealpha=0.9); legend.get_frame().set_linewidth(2.5)
        self._add_watermark(fig); self._add_context_info(fig); plt.tight_layout(rect=[0, 0.05, 1, 0.95])
        if save_path: plt.savefig(save_path, dpi=300, bbox_inches='tight', facecolor=self.COLORS['gradient_end'], edgecolor='black')
        plt.close(fig)

    def plot_key_stats_cards(self, save_path: Optional[str] = None):
        # ... (Identique V21) ...
        if self.df is None or not self.stats: print("⚠️ Stats Cards: Données non chargées."); return
        if self.position=='DF': key_stats=[('Tackles Won','TACLES GAGNÉS'),('Interceptions','INTERCEPTIONS'),('Blocks','CONTRES'),('Ball Recoveries','RÉCUPÉRATIONS'),('Progressive Passes','PASSES PROG.'),('Passes Completed','PASSES RÉUSSIES')]
        elif self.position=='FW': key_stats=[('Goals','BUTS'),('npxG: Non-Penalty xG','NPXG'),('Shots Total','TIRS'),('Assists','PASSES DÉC.'),('Shot-Creating Actions','ACTIONS CRÉÉES'),('Successful Take-Ons','DRIBBLES RÉUSSIS')]
        elif self.position=='GK': key_stats=[('Save pct','ARRÊTS %'),('Clean Sheet pct','CLEAN SHEETS %'),('PSxG_net','PSxG +/-'),('Launched_Cmp_pct','PASSES LONGUES %'),('Crosses_Stopped_pct','CENTRES STOPPÉS%'),('Def_Actions_Outside_Pen_Area','SORTIES')]
        else: key_stats=[('Goals','BUTS'),('Assists','PASSES DÉC.'),('Progressive Passes','PASSES PROG.'),('Tackles Won','TACLES GAGNÉS'),('xG: Expected Goals','xG'),('Key Passes','PASSES CLÉS')]
        fig=plt.figure(figsize=(16, 9), facecolor='none'); self._create_gradient_background(fig)
        num_stats=len(key_stats); rows=2 if num_stats > 3 else 1; cols=(num_stats + rows - 1) // rows
        valid_stats_found=0
        for i, (stat_key, stat_label) in enumerate(key_stats):
            ax=plt.subplot(rows, cols, i + 1, facecolor='none'); value=self._get_stat_value(stat_key)
            value_text = f'{value:.1f}%' if '%' in stat_key or 'pct' in stat_key.lower() or 'Percentage' in stat_key else f'{value:.2f}'
            if value > 0: valid_stats_found += 1
            ax.text(0.5, 0.6, value_text, ha='center', va='center', fontsize=40, fontweight='bold', color='white')
            ax.text(0.5, 0.3, stat_label.upper(), ha='center', va='center', fontsize=16, fontweight='bold', color='white', wrap=True)
            if '%' not in stat_key and 'pct' not in stat_key.lower() and 'Percentage' not in stat_key: ax.text(0.5, 0.15, 'par 90 min', ha='center', va='center', fontsize=11, style='italic', color='white', alpha=0.8)
            ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis('off')
            rect=mpatches.Rectangle((0.05, 0.05), 0.9, 0.9, linewidth=2.5, edgecolor='white', facecolor='black', alpha=0.3, transform=ax.transAxes, zorder=-1); ax.add_patch(rect)
        if valid_stats_found == 0: print(f"⚠️ Stats Cards: Aucune stat clé trouvée.")
        fig.suptitle(f'{self.player_name}\nSTATISTIQUES CLÉS BRUTES ({self.position})', fontsize=28, fontweight='bold', color='white', y=0.98)
        self._add_watermark(fig); self._add_context_info(fig); plt.tight_layout(rect=[0, 0.05, 1, 0.93])
        if save_path: plt.savefig(save_path, dpi=300, bbox_inches='tight', facecolor=self.COLORS['gradient_end'], edgecolor='black')
        plt.close(fig)

    def plot_percentile_bars(self, save_path: Optional[str] = None):
        # ... (Identique V21, utilisera les nouveaux scores finaux) ...
        if self.df is None or not self.stats: print("⚠️ Barres Percentile: Données non chargées."); return
        categories=list(self.CATEGORIES.keys()); scores=[self._get_category_average_normalized(cat) for cat in categories]
        valid_categories=[]; valid_scores=[]
        for cat, score in zip(categories, scores):
            if score > 0 or self.position == 'GK': valid_categories.append(cat); valid_scores.append(score)
        if not valid_scores: print("⚠️ Barres Percentile: Scores finaux à 0."); return
        fig=plt.figure(figsize=(16, 9), facecolor='none'); self._create_gradient_background(fig); ax=fig.add_subplot(111, facecolor='none')
        y_pos=np.arange(len(valid_categories)); bars=ax.barh(y_pos, valid_scores, height=0.6, color=self.COLORS['points'], edgecolor=self.COLORS['edge'], linewidth=2, alpha=0.8)
        for i, (bar, score) in enumerate(zip(bars, valid_scores)): ax.text(score + 3, i, f'{score:.0f}', va='center', ha='left', fontsize=16, fontweight='bold', color='white')
        ax.set_yticks(y_pos); ax.set_yticklabels(valid_categories, fontsize=14, color='white', fontweight='bold'); ax.invert_yaxis()
        ax.set_xlim(0, 110); ax.set_xlabel(f'SCORE FINAL (Hybride+Pen{self.CONSISTENCY_PENALTY_FACTOR}+Wgt, vs 90e pct={self.STANDARD_SCORE_TARGET})', fontsize=11, color='white', fontweight='bold') # Label ajusté
        ax.tick_params(axis='x', colors='white', labelsize=14); ax.tick_params(axis='y', length=0)
        self._customize_axes(ax); ax.spines['left'].set_visible(False); ax.spines['right'].set_visible(False); ax.spines['top'].set_visible(False)
        elite_thresh=self.thresholds['elite']; good_thresh=self.thresholds['good']; acceptable_thresh=self.thresholds['acceptable']
        ax.axvline(acceptable_thresh, color='white', linestyle=':', linewidth=1.5, alpha=0.4, zorder=0)
        ax.axvline(good_thresh, color='white', linestyle='--', linewidth=2, alpha=0.5, zorder=0)
        ax.axvline(elite_thresh, color='white', linestyle='--', linewidth=2, alpha=0.5, zorder=0)
        ax.text(acceptable_thresh, -0.8, f'Moyen ({acceptable_thresh})', ha='center', va='bottom', fontsize=12, color='white', fontweight='normal', alpha=0.7)
        ax.text(good_thresh, -0.8, f'Bon ({good_thresh})', ha='center', va='bottom', fontsize=12, color='white', fontweight='bold', alpha=0.8)
        ax.text(elite_thresh, -0.8, f'Élite ({elite_thresh})', ha='center', va='bottom', fontsize=12, color='white', fontweight='bold', alpha=0.8)
        ax.set_title(f'{self.player_name} ({self.position})', fontsize=24, fontweight='bold', color='white', pad=20)
        self._add_watermark(fig); self._add_context_info(fig); plt.tight_layout(rect=[0, 0.05, 1, 0.95])
        if save_path: plt.savefig(save_path, dpi=300, bbox_inches='tight', facecolor=self.COLORS['gradient_end'], edgecolor='black')
        plt.close(fig)

    def plot_performance_grid(self, save_path: Optional[str] = None):
        # Affiche les scores normalisés INDIVIDUELS (hybrides maintenant)
        if self.df is None or not self.stats: print("⚠️ Grille Performance: Données non chargées."); return
        matrix_data=[]; row_labels=[]; col_labels=[]
        max_cols=0
        for category in self.CATEGORIES.keys():
             stats_data=self._get_category_stats_normalized(category) # Récupère (raw, norm_hybride, weight)
             if stats_data:
                normalized_vals=[v[1] for v in stats_data.values()]; stat_names=list(stats_data.keys()) # Prend norm_hybride (index 1)
                # Pas besoin de re-plafonner ici, déjà fait dans _normalize_stat
                row_vals = normalized_vals[:5] + [np.nan]*(5 - len(normalized_vals))
                row_stat_names=stat_names[:5] + [""]*(5 - len(stat_names))
                matrix_data.append(row_vals); row_labels.append(category)
                if not col_labels: col_labels=[name.replace(': Expected','').replace(': Non-Penalty','') for name in row_stat_names]
                max_cols=max(max_cols, len(normalized_vals))
        if not matrix_data: print("⚠️ Grille Performance: Aucune donnée à afficher."); return
        num_cols_to_display=min(max_cols, 5); matrix_data=np.array(matrix_data)[:, :num_cols_to_display]; col_labels=col_labels[:num_cols_to_display]
        fig=plt.figure(figsize=(16, 9), facecolor='none'); self._create_gradient_background(fig); ax=fig.add_subplot(111, facecolor='none')
        cmap=LinearSegmentedColormap.from_list('custom', ['#333333', self.COLORS['points']], N=256); cmap.set_bad(color='#1a1a1a')
        im=ax.imshow(matrix_data, cmap=cmap, aspect='auto', vmin=0, vmax=100, interpolation='nearest')
        ax.set_yticks(np.arange(len(row_labels))); ax.set_yticklabels(row_labels, fontsize=14, fontweight='bold', color='white')
        ax.set_xticks(np.arange(num_cols_to_display)); ax.set_xticklabels(col_labels, fontsize=10, color='white', rotation=30, ha='right')
        for i in range(len(matrix_data)):
            for j in range(num_cols_to_display):
                val=matrix_data[i, j]
                if not pd.isna(val): color='white' if val < 40 or val > 90 else 'black'; ax.text(j, i, f'{val:.0f}', ha='center', va='center', fontsize=14, fontweight='bold', color=color)
        cbar=plt.colorbar(im, ax=ax, pad=0.02, fraction=0.046, aspect=30)
        cbar.set_label(f'Score Stat Hybride (90pct={self.STANDARD_SCORE_TARGET})', fontsize=12, color='white', fontweight='bold'); cbar.ax.tick_params(colors='white', labelsize=12) # Label ajusté
        cbar.outline.set_edgecolor('white'); cbar.outline.set_linewidth(1)
        plt.title(f'{self.player_name}\nMATRICE DE PERFORMANCE DÉTAILLÉE ({self.position})', fontsize=25, fontweight='bold', color='white', pad=20)
        for spine in ax.spines.values(): spine.set_visible(False)
        self._add_watermark(fig); self._add_context_info(fig); plt.tight_layout(rect=[0, 0.05, 1, 0.95])
        if save_path: plt.savefig(save_path, dpi=300, bbox_inches='tight', facecolor=self.COLORS['gradient_end'], edgecolor='black')
        plt.close(fig)

    def print_tactical_summary(self):
        # Utilise les nouveaux scores finaux (avec pénalité) et les seuils TRES STRICTS
        if self.df is None or not self.stats: print("⚠️ Résumé Tactique: Données non chargées."); return
        print(f"\n{'='*80}")
        print(f"  ⚽ {self.player_name} ({self.position}) - Saison: {self.season or 'N/A'} | Comp: {self.competition or 'N/A'} ⚽")
        print(f"  ⏱️  Minutes jouées: {self.minutes:.0f}" if self.minutes is not None else "  ⏱️  Minutes non disponibles")
        print(f"  📊 Éval. Hybride Très Exigeante (90e pct={self.STANDARD_SCORE_TARGET}, Pwr{self.NORMALIZATION_POWER}+Pen{self.CONSISTENCY_PENALTY_FACTOR}+Wgt)") # Mention évaluation
        print(f"{'='*80}\n")

        elite_thresh=self.thresholds['elite']; good_thresh=self.thresholds['good']; acceptable_thresh=self.thresholds['acceptable']

        has_scores=False
        for category in self.CATEGORIES.keys():
            score=self._get_category_average_normalized(category) # Score Hybride+Pondéré+Penalty
            if score == 0 and self.position != 'GK': continue
            has_scores=True
            bar_length=int(score / 2); bar='█'*bar_length + '░'*(50 - bar_length)

            # Labels basés sur les seuils TRES STRICTS
            if score >= elite_thresh: emoji='🟢'; label=f'ÉLITE ({score:.0f} ≥ {elite_thresh})'
            elif score >= good_thresh: emoji='🟡'; label=f'BON ({good_thresh} ≤ {score:.0f} < {elite_thresh})'
            elif score >= acceptable_thresh: emoji='🟠'; label=f'MOYEN ({acceptable_thresh} ≤ {score:.0f} < {good_thresh})'
            else: emoji='🔴'; label=f'À AMÉLIORER ({score:.0f} < {acceptable_thresh})'

            print(f"  {emoji} {category:<12} {bar} {score:>5.0f}/100  [{label}]")

        if not has_scores: print("  ⚠️ Aucune catégorie n'a pu être évaluée.")
        # Labels des seuils mis à jour dans le print
        print(f"\n  Seuils (Score Très Exigeant): Élite ≥ {elite_thresh} | Bon ≥ {good_thresh} | Moyen ≥ {acceptable_thresh} | À Améliorer < {acceptable_thresh}")
        print(f"\n{'='*80}")
        print(f"  @TarbouchData")
        print(f"{'='*80}\n")