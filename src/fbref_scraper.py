"""
FBrefScraper V4 - Scraping universel robuste
Correction des erreurs de timeout et de gestion des URLs
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup
import pandas as pd
import time
import re
from typing import Dict, Optional, Tuple, List


class FBrefScraper:
    """Scraper FBref universel avec gestion d'erreurs robuste"""
    
    def __init__(self, wait_time: int = 15, headless: bool = True):
        self.wait_time = wait_time
        self.headless = headless
        self.driver = None
        self._setup_driver()
    
    def _setup_driver(self):
        """Configure le driver Chrome avec options robustes"""
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument('--headless=new')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        print("✅ Driver Chrome initialisé")
    
    def _safe_get_page(self, url: str, max_retries: int = 3) -> bool:
        """Charge une page avec retry et gestion d'erreurs"""
        for attempt in range(max_retries):
            try:
                self.driver.get(url)
                time.sleep(2)
                return True
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"   ⚠️  Tentative {attempt + 1}/{max_retries} échouée, retry...")
                    time.sleep(3)
                else:
                    print(f"   ❌ Impossible de charger la page après {max_retries} tentatives")
                    return False
        return False
    
    def _extract_metadata_from_page(self, soup: BeautifulSoup, player_name: str) -> Dict:
        """Extrait les métadonnées du joueur depuis la page"""
        metadata = {'name': player_name}
        
        try:
            meta_info = soup.find('div', {'id': 'meta'})
            if meta_info:
                # Position
                position = meta_info.find('strong', string='Position:')
                if position:
                    pos_text = position.find_next_sibling(string=True)
                    if pos_text:
                        metadata['position'] = pos_text.strip().split()[0]
                
                # Âge
                birth_info = meta_info.find('span', {'id': 'necro-birth'})
                if birth_info:
                    birth_date = birth_info.get('data-birth', '')
                    if birth_date:
                        metadata['birth_date'] = birth_date
                        from datetime import datetime
                        birth_year = int(birth_date.split('-')[0])
                        current_year = datetime.now().year
                        metadata['age'] = current_year - birth_year
                
                # Taille
                height_elem = meta_info.find('span', string=re.compile(r'\d+cm'))
                if height_elem:
                    height_match = re.search(r'(\d+)cm', height_elem.text)
                    if height_match:
                        metadata['height_cm'] = int(height_match.group(1))
        
        except Exception as e:
            print(f"   ⚠️  Erreur extraction métadonnées: {e}")
        
        return metadata
    
    def _detect_position_from_url(self, url: str) -> str:
        """Détecte la position depuis l'URL du scouting report"""
        positions = {
            'scout_full_GK': 'GK',
            'scout_full_FW': 'FW',
            'scout_full_MF': 'MF',
            'scout_full_DF': 'DF',
            'scout_full_AM': 'AM',
            'scout_full_DM': 'DM',
            'scout_full_FB': 'FB',
            'scout_full_CB': 'CB',
            'scout_full_WB': 'WB'
        }
        
        for table_id, pos in positions.items():
            if table_id in url:
                return pos
        
        return 'MF'
    
    def _get_table_id_for_position(self, position: str) -> str:
        """Retourne le table_id selon la position"""
        position_map = {
            'GK': 'scout_full_GK',
            'FW': 'scout_full_FW',
            'MF': 'scout_full_MF',
            'DF': 'scout_full_DF',
            'AM': 'scout_full_AM',
            'DM': 'scout_full_DM',
            'FB': 'scout_full_FB',
            'CB': 'scout_full_CB',
            'WB': 'scout_full_WB'
        }
        return position_map.get(position.upper(), 'scout_full_MF')
    
    def _normalize_player_url(self, url: str) -> str:
        """
        Normalise l'URL pour extraire l'URL de base du joueur
        Supprime les parties /scout/ pour obtenir la page principale
        """
        # Si c'est une URL de scouting report, extraire l'URL de base
        if '/scout/' in url:
            # Extraire l'ID du joueur depuis l'URL
            match = re.search(r'players/([a-f0-9]+)/', url)
            if match:
                player_id = match.group(1)
                # Extraire le nom du joueur
                name_match = re.search(r'/([A-Za-z-]+)-Scouting-Report', url)
                if name_match:
                    player_name = name_match.group(1)
                    return f"https://fbref.com/en/players/{player_id}/{player_name}"
        
        # Retourner l'URL telle quelle si déjà au bon format
        return url
    
    def _get_scouting_report_links(self, player_url: str, exclude_365_days: bool = False) -> List[Dict[str, str]]:
        """
        Récupère tous les liens de scouting reports disponibles
        
        Args:
            player_url: URL du joueur
            exclude_365_days: Si True, ignore les rapports "Last 365 Days" (souvent problématiques)
        """
        print(f"\n🔍 Recherche des scouting reports disponibles...")
        
        # Normaliser l'URL
        player_url = self._normalize_player_url(player_url)
        print(f"   📍 URL normalisée : {player_url}")
        
        if not self._safe_get_page(player_url):
            return []
        
        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        
        scouting_reports = []
        
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            if '/scout/' in href and 'Scouting-Report' in href:
                link_text = link.get_text(strip=True)
                
                # Filtrer "Last 365 Days" si demandé
                if exclude_365_days and 'Last 365 Days' in link_text:
                    continue
                
                full_url = f"https://fbref.com{href}" if href.startswith('/') else href
                
                # Extraire la saison
                season_match = re.search(r'(\d{4}-\d{4})', link_text)
                if season_match:
                    season = season_match.group(1)
                else:
                    # Chercher des patterns alternatifs
                    if 'Last 365 Days' in link_text:
                        season = "2024-2025"
                    elif re.search(r'(\d{4})', link_text):
                        year = re.search(r'(\d{4})', link_text).group(1)
                        season = f"{year}-{int(year)+1}"
                    else:
                        season = "Unknown"
                
                # Extraire la compétition
                competition = re.sub(r'\d{4}-\d{4}|\d{4}|Last 365 Days', '', link_text).strip()
                if not competition:
                    competition = "Scouting Report"
                
                scouting_reports.append({
                    'url': full_url,
                    'season': season,
                    'competition': competition,
                    'text': link_text
                })
        
        # Supprimer les doublons
        seen = set()
        unique_reports = []
        for report in scouting_reports:
            key = (report['season'], report['competition'])
            if key not in seen:
                seen.add(key)
                unique_reports.append(report)
        
        if unique_reports:
            print(f"✅ {len(unique_reports)} scouting reports trouvés")
            for i, report in enumerate(unique_reports, 1):
                marker = " ⚠️ " if "Big 5" in report['competition'] or "Last 365" in report['text'] else ""
                print(f"   {i}. {report['season']} - {report['competition']}{marker}")
        else:
            print(f"❌ Aucun scouting report trouvé")
        
        return unique_reports
    
    def _scrape_single_report(self, url: str, table_id: str, season: str, competition: str) -> Optional[pd.DataFrame]:
        """Scrape un seul scouting report avec gestion robuste des erreurs"""
        if not self._safe_get_page(url):
            return None
        
        try:
            # Attendre que les tableaux soient chargés (important pour les pages JS dynamiques)
            time.sleep(3)  # Pause initiale pour le JS
            
            # Attendre qu'un tableau avec des données apparaisse
            WebDriverWait(self.driver, self.wait_time).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "table tbody tr"))
            )
            
            # Attendre encore un peu pour être sûr que le contenu est chargé
            time.sleep(2)
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # Chercher le tableau spécifique
            table = soup.find('table', {'id': table_id})
            
            if not table:
                # Chercher tous les tableaux avec classe 'stats_table'
                stats_tables = soup.find_all('table', class_='stats_table')
                if stats_tables:
                    # Prendre le premier tableau de stats
                    table = stats_tables[0]
                else:
                    # Fallback: n'importe quel tableau
                    all_tables = soup.find_all('table')
                    if all_tables:
                        table = all_tables[0]
                    else:
                        return None
            
            # Vérifier que le tableau a du contenu (pas juste du HTML vide)
            tbody = table.find('tbody')
            if not tbody or not tbody.find_all('tr'):
                print(f"   ⚠️  Tableau vide détecté")
                return None
            
            # Parser le tableau
            df = pd.read_html(str(table))[0]
            
            # Vérifier que le DataFrame n'est pas vide
            if df.empty or len(df) < 3:
                print(f"   ⚠️  DataFrame trop petit ({len(df)} lignes)")
                return None
            
            df['season'] = season
            df['competition'] = competition
            
            return df
        
        except TimeoutException:
            print(f"   ❌ Timeout - page trop longue à charger")
            return None
        except Exception as e:
            print(f"   ❌ Erreur: {str(e)[:80]}")
            return None
    
    def scrape_player_all_seasons(self, player_url: str, player_name: str, exclude_365_days: bool = False) -> Tuple[pd.DataFrame, Dict, List[Dict]]:
        """
        Scrape toutes les saisons disponibles pour un joueur
        
        Args:
            player_url: URL du joueur
            player_name: Nom du joueur
            exclude_365_days: Si True, ignore les rapports "Last 365 Days" (souvent lents/problématiques)
        
        Returns:
            - DataFrame avec toutes les saisons (1 ligne par saison)
            - Métadonnées du joueur
            - Liste des saisons disponibles
        """
        print(f"\n{'='*80}")
        print(f"🎯 SCRAPING MULTI-SAISONS - {player_name}")
        print(f"{'='*80}")
        
        # 1. Récupérer tous les scouting reports
        scouting_reports = self._get_scouting_report_links(player_url, exclude_365_days=exclude_365_days)
        
        if not scouting_reports:
            print("\n❌ Aucun scouting report trouvé")
            print("💡 Vérifiez que l'URL est correcte et pointe vers la page principale du joueur")
            return None, None, []
        
        # 2. Déterminer la position depuis le premier report
        first_report_url = scouting_reports[0]['url']
        position = self._detect_position_from_url(first_report_url)
        table_id = self._get_table_id_for_position(position)
        
        print(f"\n📊 Position détectée: {position}")
        print(f"📊 Table ID: {table_id}")
        
        # 3. Extraire les métadonnées
        if self._safe_get_page(first_report_url):
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            metadata = self._extract_metadata_from_page(soup, player_name)
            metadata['position'] = position
            
            print(f"\n📊 Métadonnées extraites:")
            for key, value in metadata.items():
                print(f"   • {key:<15} : {value}")
        else:
            metadata = {'name': player_name, 'position': position}
        
        # 4. Scraper chaque saison
        all_seasons_data = []
        
        print(f"\n🔄 Scraping de {len(scouting_reports)} saisons...")
        
        for i, report in enumerate(scouting_reports, 1):
            print(f"\n   [{i}/{len(scouting_reports)}] {report['season']} - {report['competition'][:40]}...", end=' ')
            
            df_season = self._scrape_single_report(
                url=report['url'],
                table_id=table_id,
                season=report['season'],
                competition=report['competition']
            )
            
            if df_season is not None:
                all_seasons_data.append(df_season)
                print("✅")
            else:
                print("❌")
            
            time.sleep(2)  # Rate limiting
        
        # 5. Combiner toutes les saisons
        if not all_seasons_data:
            print("\n❌ Aucune donnée extraite avec succès")
            return None, metadata, scouting_reports
        
        df_all_seasons = pd.concat(all_seasons_data, ignore_index=True)
        
        print(f"\n{'='*80}")
        print(f"✅ SCRAPING TERMINÉ")
        print(f"{'='*80}")
        print(f"   Saisons extraites  : {len(all_seasons_data)} / {len(scouting_reports)}")
        print(f"   Lignes totales     : {len(df_all_seasons)}")
        print(f"   Colonnes           : {len(df_all_seasons.columns)}")
        
        return df_all_seasons, metadata, scouting_reports
    
    def close(self):
        """Ferme le driver"""
        if self.driver:
            self.driver.quit()
            print("\n🔒 Driver fermé")


# Test rapide
if __name__ == "__main__":
    print("Test du scraper...")
    
    # Exemple avec URL complète de scouting report
    test_url = "https://fbref.com/en/players/1da5c4d6/scout/365_m1/Hamza-Igamane-Scouting-Report"
    
    scraper = FBrefScraper(wait_time=15, headless=False)
    
    try:
        df, metadata, seasons = scraper.scrape_player_all_seasons(
            player_url=test_url,
            player_name="Hamza Igamane"
        )
        
        if df is not None:
            print("\n✅ Test réussi!")
            print(f"DataFrame shape: {df.shape}")
            print(f"Saisons: {df['season'].unique()}")
        else:
            print("\n❌ Test échoué")
    
    finally:
        scraper.close()