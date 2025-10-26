"""
Main V10 - Pipeline universel avec cache CSV
Saute le scraping si le fichier CSV existe déjà
"""

import os
from datetime import datetime
from fbref_scraper import FBrefScraper
from data_cleaner import DataCleaner
from player_analyzer import PlayerAnalyzer
from player_comparator import PlayerComparator
import pandas as pd
import csv


def print_banner():
    """Bannière"""
    banner = """
    ╔═══════════════════════════════════════════════════════════════════════════╗
    ║                                                                           ║
    ║          ⚽ FBREF UNIVERSAL ANALYZER - BALLON D'OR EDITION ⚽             ║
    ║                                                                           ║
    ║              Analyse individuelle ou comparaison de joueurs              ║
    ║                                                                           ║
    ╚═══════════════════════════════════════════════════════════════════════════╝
    """
    print(banner)


def print_separator(char="=", length=80):
    """Affiche un séparateur"""
    print("\n" + char * length)


def get_user_choice():
    """Demande le mode à l'utilisateur"""
    print("\n🎯 CHOISISSEZ LE MODE D'ANALYSE :\n")
    print("   1. Analyse d'un seul joueur")
    print("   2. Comparaison de deux joueurs")
    print()
    
    while True:
        choice = input("Votre choix (1 ou 2) : ").strip()
        if choice in ['1', '2']:
            return int(choice)
        print("❌ Choix invalide. Entrez 1 ou 2.")


def get_player_info(player_number: int = None):
    """Demande les informations du joueur"""
    if player_number:
        print(f"\n{'='*80}")
        print(f"  🔵 JOUEUR {player_number}" if player_number == 1 else f"  🔴 JOUEUR {player_number}")
        print("="*80)
    else:
        print("\n📋 INFORMATIONS DU JOUEUR :")
    
    name = input("   Nom du joueur : ").strip()
    url = input("   URL FBref (page principale) : ").strip()
    return name, url


def display_seasons_table(available_seasons, player_name: str):
    """Affiche un tableau formaté des saisons disponibles"""
    print(f"\n{'='*80}")
    print(f"  📅 SAISONS DISPONIBLES POUR {player_name.upper()}")
    print("="*80)
    print(f"\n  {'#':<4} {'Saison':<15} {'Compétition':<30}")
    print(f"  {'-'*4} {'-'*15} {'-'*30}")
    
    for i, report in enumerate(available_seasons, 1):
        print(f"  {i:<4} {report['season']:<15} {report['competition']:<30}")
    
    print("\n" + "="*80)


def select_season(available_seasons, player_name: str):
    """Permet de sélectionner une saison avec interface améliorée"""
    display_seasons_table(available_seasons, player_name)
    
    while True:
        choice = input(f"\n👉 Choisissez une saison (1-{len(available_seasons)}) : ").strip()
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(available_seasons):
                selected = available_seasons[idx]
                print(f"\n✅ Saison sélectionnée : {selected['season']} - {selected['competition']}")
                return selected
        except:
            pass
        print("❌ Choix invalide. Réessayez.")


def load_or_scrape_player(player_name: str, player_url: str, output_dir: str):
    """
    Charge les données depuis le CSV s'il existe, sinon scrape
    
    Returns:
        df_all_seasons, metadata, available_seasons
    """
    # Nom du fichier CSV
    safe_name = player_name.replace(' ', '_')
    csv_file = os.path.join(output_dir, f"{safe_name}_all_seasons.csv")
    
    # Vérifier si le CSV existe
    if os.path.exists(csv_file):
        print(f"\n💾 CSV trouvé : {csv_file}")
        use_cache = input("   Utiliser le fichier existant ? (o/n) [o] : ").strip().lower()
        
        if use_cache in ['', 'o', 'oui', 'y', 'yes']:
            print(f"\n✅ Chargement depuis le cache...")
            
            try:
                df_all_seasons = pd.read_csv(csv_file, quoting=csv.QUOTE_ALL)
                
                # Reconstruire available_seasons depuis le DataFrame
                available_seasons = []
                for _, row in df_all_seasons[['season', 'competition']].drop_duplicates().iterrows():
                    available_seasons.append({
                        'season': row['season'],
                        'competition': row['competition'],
                        'text': f"{row['season']} {row['competition']}"
                    })
                
                # Extraire les métadonnées depuis le DataFrame
                metadata = {
                    'name': player_name,
                    'position': df_all_seasons['position'].iloc[0] if 'position' in df_all_seasons.columns else 'MF'
                }
                
                if 'age' in df_all_seasons.columns:
                    metadata['age'] = df_all_seasons['age'].iloc[0]
                if 'birth_date' in df_all_seasons.columns:
                    metadata['birth_date'] = df_all_seasons['birth_date'].iloc[0]
                
                print(f"✅ {len(df_all_seasons)} lignes chargées")
                print(f"✅ {len(available_seasons)} saison(s) disponible(s)")
                
                return df_all_seasons, metadata, available_seasons
                
            except Exception as e:
                print(f"⚠️  Erreur lors du chargement du cache : {e}")
                print("📥 Lancement du scraping...")
    
    # Si pas de cache ou choix de rescaper
    print(f"\n📥 SCRAPING EN COURS...")
    
    scraper = FBrefScraper(wait_time=10, headless=True)
    
    try:
        df_all_seasons, metadata, available_seasons = scraper.scrape_player_all_seasons(
            player_url=player_url,
            player_name=player_name
        )
        
        if df_all_seasons is None:
            return None, None, []
        
        # Nettoyage des virgules et guillemets dans les textes avant sauvegarde
        df_all_seasons = df_all_seasons.applymap(
            lambda x: str(x).replace(',', '').replace('"', '') if isinstance(x, str) else x
        )
        
        # IMPORTANT: Normaliser aussi available_seasons pour correspondre au CSV
        for season in available_seasons:
            season['competition'] = season['competition'].replace(',', '').replace('"', '')
            season['text'] = f"{season['season']} {season['competition']}"
        
        # Sauvegarder sans guillemets
        df_all_seasons.to_csv(csv_file, index=False, encoding='utf-8-sig', quoting=csv.QUOTE_MINIMAL)
        print(f"\n💾 Données sauvegardées (sans guillemets et sans virgules internes) : {csv_file}")
        
        
        return df_all_seasons, metadata, available_seasons
        
    finally:
        scraper.close()


def analyze_single_player():
    """Mode analyse d'un seul joueur avec cache CSV"""
    print_separator()
    print("  🎯 MODE : ANALYSE INDIVIDUELLE")
    print_separator()
    
    # Récupérer les infos
    player_name, player_url = get_player_info()
    
    OUTPUT_DIR = './fbref_analysis_output'
    TACTICAL_DIR = './tactical_analysis'
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(TACTICAL_DIR, exist_ok=True)
    
    # Charger ou scraper
    print_separator()
    print("  📥 CHARGEMENT DES DONNÉES")
    print_separator()
    
    df_all_seasons, metadata, available_seasons = load_or_scrape_player(
        player_name, player_url, OUTPUT_DIR
    )
    
    if df_all_seasons is None:
        print("\n❌ Impossible de charger les données")
        return
    
    # Sélectionner la saison pour la visualisation
    selected_season = select_season(available_seasons, player_name)
    
    # Nettoyage
    print_separator()
    print("  🧹 NETTOYAGE DES DONNÉES")
    print_separator()
    
    cleaner = DataCleaner(verbose=False)
    
    # Filtrer la saison sélectionnée
    df_selected = df_all_seasons[
        (df_all_seasons['season'] == selected_season['season']) &
        (df_all_seasons['competition'] == selected_season['competition'])
    ].copy()
    
    if df_selected.empty:
        print(f"\n❌ Aucune donnée trouvée pour cette saison")
        return
    
    # Ajouter métadonnées
    season_metadata = metadata.copy()
    for key, value in season_metadata.items():
        if key not in df_selected.columns:
            df_selected.insert(0, key, value)
    
    df_clean = cleaner.clean(df_selected, season_metadata)
    
    print(f"\n✅ Données nettoyées pour {selected_season['season']} - {selected_season['competition']}")
    
    # Visualisations
    print_separator()
    print("  🎨 GÉNÉRATION DES VISUALISATIONS")
    print_separator()
    
    analyzer = PlayerAnalyzer(
        player_name=player_name,
        position=metadata.get('position', 'MF')
    )
    
    analyzer.load_data(df_clean)
    analyzer.print_tactical_summary()
    
    safe_name = f"{player_name.replace(' ', '_')}_{selected_season['season'].replace('-', '_')}_{selected_season['competition'].replace(' ', '_')}"
    
    graphs = [
        ("Spider Radar", "plot_spider_radar", f"{safe_name}_spider.png"),
        ("Scatter Progressive", "plot_scatter_progressive", f"{safe_name}_scatter.png"),
        ("Stats Cards", "plot_key_stats_cards", f"{safe_name}_cards.png"),
        ("Barres Percentile", "plot_percentile_bars", f"{safe_name}_bars.png"),
        ("Grille Performance", "plot_performance_grid", f"{safe_name}_grid.png")
    ]
    
    print(f"\n🎨 Génération des graphiques...\n")
    
    for i, graph_info in enumerate(graphs, 1):
        print(f"   [{i}/5] {graph_info[0]:<25}...", end=' ')
        try:
            method = getattr(analyzer, graph_info[1])
            method(save_path=os.path.join(TACTICAL_DIR, graph_info[2]))
            print("✅")
        except Exception as e:
            print(f"\n❌ Erreur lors de la génération : {e}")
    
    print_separator()
    print("  ✅ ANALYSE TERMINÉE")
    print_separator()
    print(f"\n📁 Fichiers générés :")
    print(f"   • CSV complet : {OUTPUT_DIR}/{player_name.replace(' ', '_')}_all_seasons.csv")
    print(f"   • Graphiques  : {TACTICAL_DIR}/")
    print(f"\n💡 {len(graphs)} visualisations créées pour {selected_season['season']} - {selected_season['competition']}")


def compare_two_players():
    """Mode comparaison de deux joueurs avec cache CSV"""
    print_separator()
    print("  🆚 MODE : COMPARAISON DE DEUX JOUEURS")
    print_separator()
    
    print("\n💡 INFORMATION : Vous pouvez comparer des joueurs sur des saisons différentes")
    print("   Exemple : Verratti 2017-2018 Ligue 1 vs Vitinha 2023-2024 Ligue 1\n")
    
    OUTPUT_DIR = './fbref_analysis_output'
    COMPARISON_DIR = './comparison_analysis'
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(COMPARISON_DIR, exist_ok=True)
    
    # Joueur 1
    player1_name, player1_url = get_player_info(player_number=1)
    
    # Joueur 2
    player2_name, player2_url = get_player_info(player_number=2)
    
    players_data = []
    
    # Charger ou scraper les deux joueurs
    for i, (name, url) in enumerate([(player1_name, player1_url), (player2_name, player2_url)], 1):
        print_separator()
        print(f"  📥 CHARGEMENT JOUEUR {i} : {name.upper()}")
        print_separator()
        
        df_all, metadata, available = load_or_scrape_player(name, url, OUTPUT_DIR)
        
        if df_all is None:
            print(f"\n❌ Impossible de charger les données pour {name}")
            return
        
        # Sélectionner la saison pour ce joueur
        selected = select_season(available, name)
        
        players_data.append({
            'name': name,
            'df_all': df_all,
            'metadata': metadata,
            'selected_season': selected
        })
    
    # Résumé de la comparaison
    print_separator("=")
    print("  📊 RÉSUMÉ DE LA COMPARAISON")
    print_separator("=")
    print(f"\n  🔵 Joueur 1 : {players_data[0]['name']}")
    print(f"     • Saison      : {players_data[0]['selected_season']['season']}")
    print(f"     • Compétition : {players_data[0]['selected_season']['competition']}")
    print(f"     • Position    : {players_data[0]['metadata'].get('position', 'N/A')}")
    
    print(f"\n  🔴 Joueur 2 : {players_data[1]['name']}")
    print(f"     • Saison      : {players_data[1]['selected_season']['season']}")
    print(f"     • Compétition : {players_data[1]['selected_season']['competition']}")
    print(f"     • Position    : {players_data[1]['metadata'].get('position', 'N/A')}")
    
    # Vérifier les positions
    pos1 = players_data[0]['metadata'].get('position', 'Unknown')
    pos2 = players_data[1]['metadata'].get('position', 'Unknown')
    
    if pos1 != pos2:
        print(f"\n⚠️  ATTENTION : Les positions sont différentes ({pos1} vs {pos2})")
        print("   La comparaison reste possible mais peut être moins pertinente.")
        cont = input("\n👉 Continuer la comparaison ? (o/n) : ").strip().lower()
        if cont != 'o':
            print("\n🚫 Comparaison annulée")
            return
    else:
        print(f"\n✅ Les deux joueurs jouent au même poste ({pos1})")
    
    # Vérifier les saisons
    if players_data[0]['selected_season']['season'] != players_data[1]['selected_season']['season']:
        print(f"\n💡 Comparaison en différé : {players_data[0]['selected_season']['season']} vs {players_data[1]['selected_season']['season']}")
    else:
        print(f"\n💡 Comparaison sur la même saison : {players_data[0]['selected_season']['season']}")
    
    input("\n👉 Appuyez sur Entrée pour continuer...")
    
    # Nettoyage
    print_separator()
    print("  🧹 NETTOYAGE DES DONNÉES")
    print_separator()
    
    cleaner = DataCleaner(verbose=False)
    cleaned_data = []
    
    for i, player in enumerate(players_data, 1):
        print(f"\n   [{i}/2] {player['name']}...", end=' ')
        
        # Nouveau format: déjà 1 ligne par saison, filtrer directement
        df_selected = player['df_all'][
            (player['df_all']['season'] == player['selected_season']['season']) &
            (player['df_all']['competition'] == player['selected_season']['competition'])
        ].copy()
        
        if df_selected.empty:
            print(f"❌ Aucune donnée trouvée")
            return
        
        # Ajouter métadonnées manquantes
        metadata = player['metadata'].copy()
        for key, value in metadata.items():
            if key not in df_selected.columns:
                df_selected.insert(0, key, value)
        
        df_clean = cleaner.clean(df_selected, metadata)
        cleaned_data.append(df_clean)
        
        print(f"✅")
    
    # Comparaison
    print_separator()
    print("  🎨 GÉNÉRATION DES VISUALISATIONS DE COMPARAISON")
    print_separator()
    
    # Créer le nom de comparaison avec les saisons
    safe_name1 = f"{players_data[0]['name'].replace(' ', '_')}_{players_data[0]['selected_season']['season'].replace('-', '_')}"
    safe_name2 = f"{players_data[1]['name'].replace(' ', '_')}_{players_data[1]['selected_season']['season'].replace('-', '_')}"
    comparison_name = f"{safe_name1}_vs_{safe_name2}"
    
    comparator = PlayerComparator(
        player1_name=f"{players_data[0]['name']} ({players_data[0]['selected_season']['season']})",
        player2_name=f"{players_data[1]['name']} ({players_data[1]['selected_season']['season']})",
        player1_data=cleaned_data[0],
        player2_data=cleaned_data[1]
    )
    
    print(f"\n🎨 Création des graphiques de comparaison...\n")
    
    comp_graphs = [
        ("Spider Radar Superposé", "plot_comparison_spider", f"{comparison_name}_spider.png"),
        ("Barres par Catégories", "plot_comparison_categories", f"{comparison_name}_categories.png"),
        ("Heatmap Côte à Côte", "plot_comparison_heatmap", f"{comparison_name}_heatmap.png"),
        ("Scatter Comparatif", "plot_comparison_scatter", f"{comparison_name}_scatter.png"),
        ("Cartes Stats Clés", "plot_comparison_cards", f"{comparison_name}_cards.png")
    ]
    
    for i, (name, method, filename) in enumerate(comp_graphs, 1):
        print(f"   [{i}/5] {name:<30}...", end=' ')
        try:
            getattr(comparator, method)(save_path=os.path.join(COMPARISON_DIR, filename))
            print("✅")
        except Exception as e:
            print(f"\n❌ Erreur lors de la génération : {e}")
    
    print_separator()
    print("  ✅ COMPARAISON TERMINÉE")
    print_separator()
    
    print(f"\n📁 Fichiers générés :")
    print(f"   • CSV Joueur 1 : {OUTPUT_DIR}/{players_data[0]['name'].replace(' ', '_')}_all_seasons.csv")
    print(f"   • CSV Joueur 2 : {OUTPUT_DIR}/{players_data[1]['name'].replace(' ', '_')}_all_seasons.csv")
    print(f"   • Graphiques   : {COMPARISON_DIR}/")
    
    print(f"\n💡 Comparaison créée :")
    print(f"   🔵 {players_data[0]['name']} ({players_data[0]['selected_season']['season']} - {players_data[0]['selected_season']['competition']})")
    print(f"   🆚")
    print(f"   🔴 {players_data[1]['name']} ({players_data[1]['selected_season']['season']} - {players_data[1]['selected_season']['competition']})")


def main():
    """Point d'entrée principal"""
    print_banner()
    
    choice = get_user_choice()
    
    if choice == 1:
        analyze_single_player()
    else:
        compare_two_players()
    
    print_separator("=")
    print("  🏆 ANALYSE TERMINÉE AVEC SUCCÈS")
    print_separator("=")
    print("\n👋 Merci d'avoir utilisé FBref Analyzer !\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Analyse interrompue par l'utilisateur")
        print("👋 Au revoir\n")
    except Exception as e:
        print(f"\n\n❌ ERREUR FATALE : {e}")
        import traceback
        traceback.print_exc()
        print("\n💡 Veuillez vérifier votre configuration")
    finally:
        print()