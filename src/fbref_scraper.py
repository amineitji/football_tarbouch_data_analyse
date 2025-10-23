"""
FBrefScraper V3 - Multi-saisons universel
Scrape n'importe quel joueur avec toutes ses saisons
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import pandas as pd
import time
import re
from typing import Dict, Optional, Tuple, List


class FBrefScraper:
    """Scraper FBref universel avec extraction multi-saisons"""
    
    def __init__(self, wait_time: int = 10, headless: bool = True):
        self.wait_time = wait_time
        self.headless = headless
        self.driver = None
        self._setup_driver()
    
    def _setup_driver(self):
        """Configure le driver Chrome"""
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        self.driver = webdriver.Chrome(options=chrome_options)
        print("✅ Driver Chrome initialisé")
    
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
            print(f"⚠️  Erreur extraction métadonnées: {e}")
        
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
        
        return 'MF'  # Par défaut
    
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
    
    def _get_scouting_report_links(self, player_url: str) -> List[Dict[str, str]]:
        """Récupère tous les liens de scouting reports disponibles"""
        print(f"\n🔍 Recherche des scouting reports disponibles...")
        
        self.driver.get(player_url)
        time.sleep(3)
        
        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        
        scouting_reports = []
        
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            if '/scout/' in href and 'Scouting-Report' in href:
                link_text = link.get_text(strip=True)
                full_url = f"https://fbref.com{href}" if href.startswith('/') else href
                
                season_match = re.search(r'(\d{4}-\d{4}|\d{4})', link_text)
                season = season_match.group(1) if season_match else "Unknown"
                
                competition = re.sub(r'\d{4}-\d{4}|\d{4}', '', link_text).strip()
                
                scouting_reports.append({
                    'url': full_url,
                    'season': season,
                    'competition': competition,
                    'text': link_text
                })
        
        seen = set()
        unique_reports = []
        for report in scouting_reports:
            key = (report['season'], report['competition'])
            if key not in seen:
                seen.add(key)
                unique_reports.append(report)
        
        print(f"✅ {len(unique_reports)} scouting reports trouvés")
        for i, report in enumerate(unique_reports, 1):
            print(f"   {i}. {report['season']} - {report['competition']}")
        
        return unique_reports
    
    def scrape_player_all_seasons(self, player_url: str, player_name: str) -> Tuple[pd.DataFrame, Dict, List[Dict]]:
        """
        Scrape toutes les saisons disponibles pour un joueur
        
        Returns:
            - DataFrame avec toutes les saisons (1 ligne par saison)
            - Métadonnées du joueur
            - Liste des saisons disponibles
        """
        print(f"\n{'='*80}")
        print(f"🎯 SCRAPING MULTI-SAISONS - {player_name}")
        print(f"{'='*80}")
        
        # 1. Récupérer tous les scouting reports
        scouting_reports = self._get_scouting_report_links(player_url)
        
        if not scouting_reports:
            print("❌ Aucun scouting report trouvé")
            return None, None, []
        
        # 2. Déterminer la position depuis le premier report
        first_report_url = scouting_reports[0]['url']
        position = self._detect_position_from_url(first_report_url)
        table_id = self._get_table_id_for_position(position)
        
        print(f"\n📊 Position détectée: {position}")
        print(f"📊 Table ID: {table_id}")
        
        # 3. Extraire les métadonnées
        self.driver.get(scouting_reports[0]['url'])
        time.sleep(2)
        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        metadata = self._extract_metadata_from_page(soup, player_name)
        metadata['position'] = position
        
        print(f"\n📊 Métadonnées extraites:")
        for key, value in metadata.items():
            print(f"   • {key:<15} : {value}")
        
        # 4. Scraper chaque saison
        all_seasons_data = []
        
        print(f"\n🔄 Scraping de {len(scouting_reports)} saisons...")
        
        for i, report in enumerate(scouting_reports, 1):
            print(f"\n   [{i}/{len(scouting_reports)}] {report['season']} - {report['competition']}...", end=' ')
            
            try:
                self.driver.get(report['url'])
                time.sleep(2)
                
                WebDriverWait(self.driver, self.wait_time).until(
                    EC.presence_of_element_located((By.ID, table_id))
                )
                
                soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                table = soup.find('table', {'id': table_id})
                
                if table:
                    df_season = pd.read_html(str(table))[0]
                    df_season['season'] = report['season']
                    df_season['competition'] = report['competition']
                    
                    all_seasons_data.append(df_season)
                    print("✅")
                else:
                    print("❌ (tableau non trouvé)")
            
            except Exception as e:
                print(f"❌ ({str(e)[:50]})")
                continue
            
            time.sleep(2)
        
        # 5. Combiner toutes les saisons
        if not all_seasons_data:
            print("\n❌ Aucune donnée extraite")
            return None, metadata, scouting_reports
        
        df_all_seasons = pd.concat(all_seasons_data, ignore_index=True)
        
        print(f"\n{'='*80}")
        print(f"✅ SCRAPING TERMINÉ")
        print(f"{'='*80}")
        print(f"   Saisons extraites  : {len(all_seasons_data)}")
        print(f"   Lignes totales     : {len(df_all_seasons)}")
        print(f"   Colonnes           : {len(df_all_seasons.columns)}")
        
        return df_all_seasons, metadata, scouting_reports
    
    def close(self):
        """Ferme le driver"""
        if self.driver:
            self.driver.quit()
            print("\n🔒 Driver fermé")