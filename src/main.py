"""
Main - Pipeline complet d'analyse de joueur FBref
Orchestre : Scraping → Nettoyage → Analyse → Visualisation
"""

import os
import sys
from datetime import datetime

# Import des classes custom
from fbref_scraper import FBrefScraper
from data_cleaner import DataCleaner
from player_analyzer import PlayerAnalyzer


def print_header(title: str):
    """Affiche un header stylisé"""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80)


def print_step(step_number: int, total_steps: int, description: str):
    """Affiche une étape du pipeline"""
    print(f"\n{'─'*80}")
    print(f"📍 ÉTAPE {step_number}/{total_steps} : {description}")
    print(f"{'─'*80}")


def main():
    """
    Pipeline complet d'analyse d'un joueur FBref
    """
    
    # ========================================================================
    # CONFIGURATION
    # ========================================================================
    
    PLAYER_CONFIG = {
        'name': 'Marco Verratti',
        'url': 'https://fbref.com/en/players/1467af0d/scout/11454/Marco-Verratti-Scouting-Report',
        'table_id': 'scout_full_MF',
        'position': 'MF'
    }
    
    SCRAPER_CONFIG = {
        'wait_time': 10,
        'headless': True  # False pour voir le navigateur
    }
    
    CLEANING_CONFIG = {
        'remove_composites': True,
        'remove_percentages': True,
        'remove_duplicates': True,
        'remove_empty': True
    }
    
    OUTPUT_DIR = './fbref_analysis_output'
    
    # ========================================================================
    # DÉBUT DU PIPELINE
    # ========================================================================
    
    print_header("🔍 PIPELINE D'ANALYSE FBREF")
    print(f"Joueur    : {PLAYER_CONFIG['name']}")
    print(f"Position  : {PLAYER_CONFIG['position']}")
    print(f"Output    : {OUTPUT_DIR}")
    print(f"Timestamp : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Créer le dossier de sortie
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"\n✓ Dossier de sortie créé : {OUTPUT_DIR}")
    
    # ========================================================================
    # ÉTAPE 1 : SCRAPING
    # ========================================================================
    
    print_step(1, 4, "SCRAPING DES DONNÉES")
    
    scraper = FBrefScraper(
        wait_time=SCRAPER_CONFIG['wait_time'],
        headless=SCRAPER_CONFIG['headless']
    )
    
    try:
        df_raw = scraper.scrape_player(
            url=PLAYER_CONFIG['url'],
            table_id=PLAYER_CONFIG['table_id'],
            player_name=PLAYER_CONFIG['name']
        )
        
        if df_raw is None:
            print("\n❌ ERREUR : Échec du scraping")
            return
        
        print(f"\n✓ Scraping réussi : {len(df_raw)} lignes extraites")
        
        # Sauvegarder les données brutes
        raw_file = os.path.join(OUTPUT_DIR, f"{PLAYER_CONFIG['name'].replace(' ', '_')}_raw.csv")
        df_raw.to_csv(raw_file, index=False, encoding='utf-8-sig')
        print(f"✓ Données brutes sauvegardées : {raw_file}")
        
    finally:
        scraper.close()
    
    # ========================================================================
    # ÉTAPE 2 : NETTOYAGE
    # ========================================================================
    
    print_step(2, 4, "NETTOYAGE DES DONNÉES")
    
    cleaner = DataCleaner(verbose=True)
    
    df_clean = cleaner.clean(
        df_raw,
        remove_composites=CLEANING_CONFIG['remove_composites'],
        remove_percentages=CLEANING_CONFIG['remove_percentages'],
        remove_duplicates=CLEANING_CONFIG['remove_duplicates'],
        remove_empty=CLEANING_CONFIG['remove_empty']
    )
    
    print(f"\n✓ Nettoyage terminé : {len(df_clean)} lignes conservées")
    
    # Afficher le rapport de nettoyage
    cleaner.print_cleaning_report()
    
    # Sauvegarder les données nettoyées
    clean_file = os.path.join(OUTPUT_DIR, f"{PLAYER_CONFIG['name'].replace(' ', '_')}_clean.csv")
    df_clean.to_csv(clean_file, index=False, encoding='utf-8-sig')
    print(f"\n✓ Données nettoyées sauvegardées : {clean_file}")
    
    # ========================================================================
    # ÉTAPE 3 : ANALYSE TEXTUELLE
    # ========================================================================
    
    print_step(3, 4, "ANALYSE DU JOUEUR")
    
    # Copier les métadonnées
    df_clean.attrs = df_raw.attrs.copy()
    
    analyzer = PlayerAnalyzer(
        player_name=PLAYER_CONFIG['name'],
        position=PLAYER_CONFIG['position']
    )
    
    analyzer.load_data(df_clean)
    
    # Afficher le profil textuel
    analyzer.print_player_profile()
    
    # Sauvegarder le résumé textuel
    summary_file = os.path.join(OUTPUT_DIR, f"{PLAYER_CONFIG['name'].replace(' ', '_')}_summary.txt")
    
    with open(summary_file, 'w', encoding='utf-8') as f:
        # Rediriger la sortie vers le fichier
        old_stdout = sys.stdout
        sys.stdout = f
        
        analyzer.print_player_profile()
        
        sys.stdout = old_stdout
    
    print(f"\n✓ Résumé textuel sauvegardé : {summary_file}")
    
    # ========================================================================
    # ÉTAPE 4 : VISUALISATIONS
    # ========================================================================
    
    print_step(4, 4, "GÉNÉRATION DES VISUALISATIONS")
    
    # Créer un sous-dossier pour les graphiques
    viz_dir = os.path.join(OUTPUT_DIR, 'visualizations')
    os.makedirs(viz_dir, exist_ok=True)
    
    print("\nGénération des graphiques...")
    
    safe_name = PLAYER_CONFIG['name'].replace(' ', '_').replace('-', '_')
    
    # 1. Radar des percentiles
    print("  [1/4] Radar des percentiles...")
    analyzer.plot_percentile_radar(
        save_path=os.path.join(viz_dir, f'{safe_name}_radar.png')
    )
    
    # 2. Top statistiques
    print("  [2/4] Top statistiques...")
    analyzer.plot_top_stats(
        n=15,
        save_path=os.path.join(viz_dir, f'{safe_name}_top_stats.png')
    )
    
    # 3. Comparaison par catégories
    print("  [3/4] Comparaison par catégories...")
    analyzer.plot_category_comparison(
        save_path=os.path.join(viz_dir, f'{safe_name}_categories.png')
    )
    
    # 4. Distribution des percentiles
    print("  [4/4] Distribution des percentiles...")
    analyzer.plot_percentile_distribution(
        save_path=os.path.join(viz_dir, f'{safe_name}_distribution.png')
    )
    
    print(f"\n✓ Visualisations sauvegardées dans : {viz_dir}")
    
    # ========================================================================
    # RÉSUMÉ FINAL
    # ========================================================================
    
    print_header("📊 PIPELINE TERMINÉ")
    
    print("\n📁 Fichiers générés :")
    print(f"  • Données brutes      : {raw_file}")
    print(f"  • Données nettoyées   : {clean_file}")
    print(f"  • Résumé textuel      : {summary_file}")
    print(f"  • Visualisations      : {viz_dir}/")
    
    print("\n🎨 Graphiques créés :")
    print(f"  • Radar des percentiles")
    print(f"  • Top 15 statistiques")
    print(f"  • Comparaison par catégories")
    print(f"  • Distribution des percentiles")
    
    print("\n✅ Analyse complète terminée avec succès !")
    print(f"📂 Tous les fichiers sont dans : {OUTPUT_DIR}")
    
    print("\n" + "="*80)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Pipeline interrompu par l'utilisateur")
    except Exception as e:
        print(f"\n\n❌ ERREUR FATALE : {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\n👋 Fin du programme")