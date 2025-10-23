"""
Main V4 - Pipeline avec visualisations professionnelles
Design moderne, échelles réalistes, lisibilité optimale
"""

import os
from datetime import datetime
from fbref_scraper import FBrefScraper
from data_cleaner import DataCleaner
from player_analyzer import PlayerAnalyzer


def print_banner():
    """Bannière stylée"""
    banner = """
    ╔═══════════════════════════════════════════════════════════════════════════╗
    ║                                                                           ║
    ║             🔥 FBREF TACTICAL ANALYZER V4 🔥                              ║
    ║                                                                           ║
    ║         Analyse tactique professionnelle avec visualisations modernes    ║
    ║                                                                           ║
    ╚═══════════════════════════════════════════════════════════════════════════╝
    """
    print(banner)


def print_section(title: str, emoji: str = ""):
    """Section stylée"""
    print(f"\n{'='*80}")
    print(f"  {emoji} {title}")
    print(f"{'='*80}\n")


def main():
    """Pipeline complet avec 5 visualisations professionnelles"""
    
    print_banner()
    
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
    
    # Créer les dossiers
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(TACTICAL_DIR, exist_ok=True)
    
    print(f"📋 CONFIGURATION")
    print(f"   Joueur      : {PLAYER_CONFIG['name']}")
    print(f"   Position    : {PLAYER_CONFIG['position']}")
    print(f"   Output      : {OUTPUT_DIR}")
    print(f"   Graphiques  : {TACTICAL_DIR}")
    print(f"   Timestamp   : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    print(f"\n✨ VISUALISATIONS GÉNÉRÉES (5 graphiques professionnels) :")
    print(f"   1️⃣  Spider Radar       → Profil tactique global (échelles réelles)")
    print(f"   2️⃣  Barres Catégories  → Comparaison des 5 aspects du jeu")
    print(f"   3️⃣  Top 12 Stats       → Meilleures performances individuelles")
    print(f"   4️⃣  Passing Polaire    → Analyse détaillée du passing (échelle réelle)")
    print(f"   5️⃣  Heatmap Tactique   → Vue d'ensemble matricielle")
    
    # ========================================================================
    # ÉTAPE 1 : SCRAPING
    # ========================================================================
    
    print_section("ÉTAPE 1/3 : SCRAPING DES DONNÉES", "📥")
    
    scraper = FBrefScraper(
        wait_time=SCRAPER_CONFIG['wait_time'],
        headless=SCRAPER_CONFIG['headless']
    )
    
    try:
        print(f"🌐 Connexion à FBref...")
        print(f"   URL : {PLAYER_CONFIG['url'][:60]}...")
        
        df_raw, metadata = scraper.scrape_player(
            url=PLAYER_CONFIG['url'],
            table_id=PLAYER_CONFIG['table_id'],
            player_name=PLAYER_CONFIG['name']
        )
        
        if df_raw is None:
            print("\n❌ ERREUR : Échec du scraping")
            return
        
        print(f"\n✅ Scraping réussi")
        print(f"   Lignes extraites : {len(df_raw)}")
        print(f"   Colonnes         : {len(df_raw.columns)}")
        
        if metadata:
            print(f"\n📊 MÉTADONNÉES EXTRAITES ({len(metadata)} champs) :")
            for key, value in metadata.items():
                print(f"   • {key:<20} : {value}")
        
        # Sauvegarder données brutes
        raw_file = os.path.join(OUTPUT_DIR, f"{PLAYER_CONFIG['name'].replace(' ', '_')}_raw.csv")
        df_raw.to_csv(raw_file, index=False, encoding='utf-8-sig')
        print(f"\n💾 Données brutes sauvegardées : {raw_file}")
        
    except Exception as e:
        print(f"\n❌ ERREUR lors du scraping : {e}")
        return
    finally:
        scraper.close()
    
    # ========================================================================
    # ÉTAPE 2 : NETTOYAGE
    # ========================================================================
    
    print_section("ÉTAPE 2/3 : NETTOYAGE ET TRANSFORMATION", "🧹")
    
    print("🔄 Application des transformations...")
    print("   • Suppression du Percentile (contexte temporel)")
    print("   • Conversion format horizontal (1 ligne = 1 joueur)")
    print("   • Nettoyage des stats composées")
    print("   • Suppression des colonnes vides")
    
    cleaner = DataCleaner(verbose=False)
    df_clean = cleaner.clean(df_raw, metadata)
    
    print(f"\n✅ Nettoyage terminé")
    print(f"   Format        : HORIZONTAL")
    print(f"   Dimensions    : {df_clean.shape[0]} ligne × {df_clean.shape[1]} colonnes")
    print(f"   Stats conservées : {df_clean.shape[1] - len(metadata or {})}")
    
    # Sauvegarder données nettoyées
    clean_file = os.path.join(OUTPUT_DIR, f"{PLAYER_CONFIG['name'].replace(' ', '_')}_clean.csv")
    df_clean.to_csv(clean_file, index=False, encoding='utf-8-sig')
    print(f"\n💾 Données nettoyées sauvegardées : {clean_file}")
    
    print(f"\n📈 APERÇU DES STATISTIQUES :")
    preview_stats = {col: df_clean[col].iloc[0] for col in df_clean.select_dtypes(include=['number']).columns[:8]}
    for stat, value in preview_stats.items():
        print(f"   • {stat:<30} : {value:.2f}")
    if len(df_clean.select_dtypes(include=['number']).columns) > 8:
        print(f"   ... et {len(df_clean.select_dtypes(include=['number']).columns) - 8} autres stats")
    
    # ========================================================================
    # ÉTAPE 3 : VISUALISATIONS
    # ========================================================================
    
    print_section("ÉTAPE 3/3 : GÉNÉRATION DES VISUALISATIONS", "🎨")
    
    analyzer = PlayerAnalyzer(
        player_name=metadata.get('name', PLAYER_CONFIG['name']),
        position=metadata.get('position', PLAYER_CONFIG['position'])
    )
    
    analyzer.load_data(df_clean)
    
    # Afficher le résumé tactique
    analyzer.print_tactical_summary()
    
    print(f"\n🎨 GÉNÉRATION DES GRAPHIQUES...")
    print(f"   Destination : {TACTICAL_DIR}\n")
    
    safe_name = PLAYER_CONFIG['name'].replace(' ', '_')
    
    # Graphique 1 : Spider Radar
    print("   [1/5] 🕸️  Spider Radar (profil global)...", end=' ')
    try:
        analyzer.plot_spider_radar(
            save_path=os.path.join(TACTICAL_DIR, f"{safe_name}_1_spider_radar.png")
        )
        print("✅")
    except Exception as e:
        print(f"❌ ({e})")
    
    # Graphique 2 : Barres catégories
    print("   [2/5] 📊 Barres horizontales (catégories)...", end=' ')
    try:
        analyzer.plot_category_bars(
            save_path=os.path.join(TACTICAL_DIR, f"{safe_name}_2_categories_bars.png")
        )
        print("✅")
    except Exception as e:
        print(f"❌ ({e})")
    
    # Graphique 3 : Top 12 stats
    print("   [3/5] 🏆 Top 12 statistiques...", end=' ')
    try:
        analyzer.plot_top_stats(
            top_n=12,
            save_path=os.path.join(TACTICAL_DIR, f"{safe_name}_3_top12_stats.png")
        )
        print("✅")
    except Exception as e:
        print(f"❌ ({e})")
    
    # Graphique 4 : Passing polaire
    print("   [4/5] ⚽ Passing détaillé (polaire)...", end=' ')
    try:
        analyzer.plot_passing_polar(
            save_path=os.path.join(TACTICAL_DIR, f"{safe_name}_4_passing_polar.png")
        )
        print("✅")
    except Exception as e:
        print(f"❌ ({e})")
    
    # Graphique 5 : Heatmap
    print("   [5/5] 🔥 Heatmap tactique...", end=' ')
    try:
        analyzer.plot_heatmap_categories(
            save_path=os.path.join(TACTICAL_DIR, f"{safe_name}_5_heatmap.png")
        )
        print("✅")
    except Exception as e:
        print(f"❌ ({e})")
    
    # ========================================================================
    # RÉSUMÉ FINAL
    # ========================================================================
    
    print_section("PIPELINE TERMINÉ AVEC SUCCÈS", "✅")
    
    print("📁 FICHIERS GÉNÉRÉS :\n")
    
    print("   📄 Données :")
    print(f"      • {os.path.basename(raw_file)}")
    print(f"      • {os.path.basename(clean_file)}")
    
    print(f"\n   🎨 Visualisations ({TACTICAL_DIR}) :")
    print(f"      • {safe_name}_1_spider_radar.png      ← Profil tactique global")
    print(f"      • {safe_name}_2_categories_bars.png   ← Comparaison par catégorie")
    print(f"      • {safe_name}_3_top12_stats.png       ← Meilleures performances")
    print(f"      • {safe_name}_4_passing_polar.png     ← Focus sur le passing")
    print(f"      • {safe_name}_5_heatmap.png           ← Vue d'ensemble matricielle")
    
    print(f"\n{'='*80}")
    print(f"  ✨ 5 visualisations professionnelles avec échelles réalistes")
    print(f"  ✨ Design moderne et lisibilité optimale")
    print(f"  ✨ Analyse tactique complète en un coup d'œil")
    print(f"{'='*80}")
    
    print(f"\n💡 PROCHAINES ÉTAPES :")
    print(f"   • Consulter les graphiques dans '{TACTICAL_DIR}'")
    print(f"   • Analyser les forces et faiblesses du joueur")
    print(f"   • Comparer avec d'autres profils similaires")
    
    print(f"\n👋 Analyse terminée pour {PLAYER_CONFIG['name']}\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Pipeline interrompu par l'utilisateur")
        print("👋 Au revoir\n")
    except Exception as e:
        print(f"\n\n❌ ERREUR FATALE : {e}")
        import traceback
        traceback.print_exc()
        print("\n💡 Vérifiez la configuration et les dépendances")
    finally:
        print()