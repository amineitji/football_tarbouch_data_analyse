"""
Main V2 - Pipeline complet avec analyse tactique avancée
- Scraping + Métadonnées
- Nettoyage des données
- Visualisations tactiques innovantes par aspect (Passing, Shooting, Defense, etc.)
"""

import os
import sys
from datetime import datetime

# Import des classes
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
    Pipeline complet V2 : Scraping + Nettoyage + Analyse Tactique Avancée
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
        'headless': True
    }
    
    OUTPUT_DIR = './fbref_analysis_output'
    TACTICAL_DIR = './tactical_analysis'
    
    # ========================================================================
    # DÉBUT DU PIPELINE
    # ========================================================================
    
    print_header("🔍 PIPELINE D'ANALYSE FBREF V2 - ANALYSE TACTIQUE")
    print(f"Joueur    : {PLAYER_CONFIG['name']}")
    print(f"Position  : {PLAYER_CONFIG['position']}")
    print(f"Output    : {OUTPUT_DIR}")
    print(f"Tactical  : {TACTICAL_DIR}")
    print(f"Timestamp : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"\n✨ Fonctionnalités V2 :")
    print(f"  • Extraction des métadonnées (nom, âge, taille, minutes jouées)")
    print(f"  • Suppression du Percentile (contexte temporel)")
    print(f"  • Format horizontal (1 ligne = 1 joueur)")
    print(f"  • 🆕 Spider radar tactique")
    print(f"  • 🆕 Heatmap par catégorie")
    print(f"  • 🆕 Analyse détaillée par aspect (Passing, Shooting, Defense, etc.)")
    print(f"  • 🆕 Graphiques polaires et barres pour chaque aspect")
    
    # Créer les dossiers de sortie
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(TACTICAL_DIR, exist_ok=True)
    print(f"\n✓ Dossiers de sortie créés")
    
    # ========================================================================
    # ÉTAPE 1 : SCRAPING + MÉTADONNÉES
    # ========================================================================
    
    print_step(1, 3, "SCRAPING DES DONNÉES + MÉTADONNÉES")
    
    scraper = FBrefScraper(
        wait_time=SCRAPER_CONFIG['wait_time'],
        headless=SCRAPER_CONFIG['headless']
    )
    
    try:
        df_raw, metadata = scraper.scrape_player(
            url=PLAYER_CONFIG['url'],
            table_id=PLAYER_CONFIG['table_id'],
            player_name=PLAYER_CONFIG['name']
        )
        
        if df_raw is None:
            print("\n❌ ERREUR : Échec du scraping")
            return
        
        print(f"\n✓ Scraping réussi : {len(df_raw)} lignes extraites")
        print(f"✓ Métadonnées extraites : {len(metadata)} champs")
        
        # Afficher les métadonnées
        if metadata:
            print("\n📋 MÉTADONNÉES DU JOUEUR :")
            for key, value in metadata.items():
                print(f"  • {key:<20} : {value}")
        
        # Sauvegarder les données brutes
        raw_file = os.path.join(OUTPUT_DIR, f"{PLAYER_CONFIG['name'].replace(' ', '_')}_raw.csv")
        df_raw.to_csv(raw_file, index=False, encoding='utf-8-sig')
        print(f"\n✓ Données brutes sauvegardées : {raw_file}")
        
    finally:
        scraper.close()
    
    # ========================================================================
    # ÉTAPE 2 : NETTOYAGE + TRANSFORMATION HORIZONTALE
    # ========================================================================
    
    print_step(2, 3, "NETTOYAGE + TRANSFORMATION HORIZONTALE")
    
    cleaner = DataCleaner(verbose=True)
    
    df_clean = cleaner.clean(df_raw, metadata)
    
    # Afficher le rapport
    cleaner.print_cleaning_report()
    
    # Sauvegarder les données nettoyées (format horizontal)
    clean_file = os.path.join(OUTPUT_DIR, f"{PLAYER_CONFIG['name'].replace(' ', '_')}_clean_horizontal.csv")
    df_clean.to_csv(clean_file, index=False, encoding='utf-8-sig')
    print(f"\n✓ Données nettoyées sauvegardées : {clean_file}")
    
    # Afficher un aperçu
    print("\n📊 APERÇU DES DONNÉES FINALES (format horizontal) :")
    print(f"\nNombre de colonnes : {len(df_clean.columns)}")
    print(f"\nPremières colonnes (métadonnées + stats) :")
    
    # Afficher les 10 premières colonnes
    preview_cols = df_clean.columns[:min(10, len(df_clean.columns))]
    for col in preview_cols:
        value = df_clean[col].iloc[0]
        print(f"  • {col:<30} : {value}")
    
    if len(df_clean.columns) > 10:
        print(f"  ... et {len(df_clean.columns) - 10} autres colonnes")
    
    # ========================================================================
    # ÉTAPE 3 : ANALYSE TACTIQUE AVANCÉE + IA 🆕
    # ========================================================================
    
    print_step(3, 3, "🆕 ANALYSE TACTIQUE AVANCÉE + INTELLIGENCE ARTIFICIELLE")
    
    # Créer l'analyseur
    analyzer = PlayerAnalyzer(
        player_name=metadata.get('name', PLAYER_CONFIG['name']),
        position=metadata.get('position', PLAYER_CONFIG['position'])
    )
    
    # Charger les données
    analyzer.load_data(df_clean)
    
    # Afficher le résumé tactique
    print("\n📝 Génération du résumé tactique...")
    analyzer.print_tactical_summary()
    
    # Générer tous les graphiques tactiques standard
    print("\n🎨 Génération des visualisations tactiques standard...")
    print("   (Cela peut prendre quelques secondes...)")
    
    try:
        analyzer.generate_tactical_report(output_dir=TACTICAL_DIR)
    except Exception as e:
        print(f"\n⚠️  Erreur lors de la génération des graphiques : {e}")
        print("   Les données ont été sauvegardées, mais les visualisations ont échoué.")
        import traceback
        traceback.print_exc()
    
    # 🆕 ANALYSES IA AVANCÉES
    print("\n" + "="*80)
    print("🤖 ANALYSES INTELLIGENCE ARTIFICIELLE AVANCÉES")
    print("="*80)
    
    safe_name = PLAYER_CONFIG['name'].replace(' ', '_')
    
    # 1. Analyse IA du profil
    print("\n1️⃣  Analyse IA du profil tactique (K-Means, profiling)...")
    try:
        ai_profile_path = os.path.join(TACTICAL_DIR, f"{safe_name}_ai_profile.png")
        ai_analysis = analyzer.analyze_player_profile_ai(save_path=ai_profile_path)
    except Exception as e:
        print(f"⚠️  Erreur analyse IA : {e}")
        ai_analysis = None
    
    # 2. Dashboard avancé multi-dimensionnel
    print("\n2️⃣  Création du dashboard tactique avancé multi-dimensionnel...")
    try:
        dashboard_path = os.path.join(TACTICAL_DIR, f"{safe_name}_advanced_dashboard.png")
        analyzer.plot_advanced_comparison(save_path=dashboard_path)
    except Exception as e:
        print(f"⚠️  Erreur dashboard : {e}")
    
    print("\n✅ Analyses IA terminées !")
    
    # ========================================================================
    # RÉSUMÉ FINAL
    # ========================================================================
    
    print_header("📊 PIPELINE TERMINÉ")
    
    print("\n📁 Fichiers générés :")
    print(f"\n  Données :")
    print(f"    • {raw_file}")
    print(f"    • {clean_file}")
    
    print(f"\n  Visualisations tactiques ({TACTICAL_DIR}) :")
    
    safe_name = PLAYER_CONFIG['name'].replace(' ', '_')
    
    print(f"\n    🕷️  Spider Radar :")
    print(f"      • {safe_name}_spider.png")
    
    print(f"\n    🔥 Heatmap :")
    print(f"      • {safe_name}_heatmap.png")
    
    print(f"\n    📊 Vue d'ensemble :")
    print(f"      • {safe_name}_multi_aspects.png")
    
    print(f"\n    ⭕ Analyses par aspect (Polaires) :")
    categories = ['Shooting', 'Passing', 'Defense', 'Possession', 
                 'Progression', 'Creation', 'Discipline']
    for cat in categories:
        print(f"      • {safe_name}_{cat.lower()}_polar.png")
    
    print(f"\n    📊 Détails par aspect (Barres) :")
    for cat in categories:
        print(f"      • {safe_name}_{cat.lower()}_bars.png")
    
    print(f"\n    🆕 🤖 ANALYSES IA AVANCÉES :")
    print(f"      • {safe_name}_ai_profile.png - Profil IA & Points forts/faibles")
    print(f"      • {safe_name}_advanced_dashboard.png - Dashboard multi-dimensionnel")
    
    print("\n✨ Analyses disponibles :")
    print(f"  ✓ Spider radar tactique global (ÉCHELLE ADAPTATIVE)")
    print(f"  ✓ Heatmap de performance par catégorie")
    print(f"  ✓ Vue multi-aspects avec radars comparatifs")
    print(f"  ✓ 7 graphiques polaires détaillés par aspect tactique")
    print(f"  ✓ 7 graphiques en barres pour chaque aspect")
    print(f"  🆕 ✓ Analyse IA du profil tactique (Forces/Faiblesses)")
    print(f"  🆕 ✓ Dashboard avancé multi-dimensionnel")
    print(f"  ✓ Total : 19 visualisations tactiques professionnelles")
    
    print("\n🎯 Comment utiliser les résultats :")
    print(f"  1. Ouvrez les fichiers PNG dans {TACTICAL_DIR}")
    print(f"  2. 🆕 Spider radar avec échelle ADAPTATIVE (met en valeur les forces)")
    print(f"  3. 🆕 Analyse IA pour identifier le profil tactique automatiquement")
    print(f"  4. 🆕 Dashboard multi-dimensionnel pour une vue à 360°")
    print(f"  5. Consultez les graphiques par aspect (Shooting, Passing, Defense, etc.)")
    print(f"  6. Utilisez la heatmap pour identifier forces/faiblesses rapidement")
    
    print("\n🚀 NOUVEAUTÉS V3 :")
    print(f"  ⭐ Échelle adaptative sur spider radar (50% du max pour mieux valoriser)")
    print(f"  ⭐ Analyse IA avec identification automatique du profil tactique")
    print(f"  ⭐ Dashboard avancé : 6 vues complémentaires en 1 graphique")
    print(f"  ⭐ Visualisations optimisées pour Twitter (lisibles, impactantes)")
    
    print("\n✅ Pipeline terminé avec succès !")
    print(f"📂 Tous les fichiers sont dans : {OUTPUT_DIR} et {TACTICAL_DIR}")
    
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