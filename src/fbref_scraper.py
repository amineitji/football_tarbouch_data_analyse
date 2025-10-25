"""
FBrefScraper V5 - Extraction correcte des minutes de jeu
Scrape les minutes depuis la description "Based on X minutes played"
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
    """Scraper FBref avec extraction correcte des minutes"""
    
    def __init__(self, wait_time: int = 15, headless: bool = True):
        self.wait_time = wait_time
        self.headless = headless
        self.driver = None
        self._setup_driver()
    
    def _setup_driver(self):
        """Configure Chrome"""
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument('--headless=new')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        self.driver = webdriver.Chrome(options=chrome_options)
        print("✅ Driver initialisé")
    
    def _safe_get_page(self, url: str, max_retries: int = 3) -> bool:
        """Charge une page avec retry"""
        for attempt in range(max_retries):
            try:
                self.driver.get(url)
                time.sleep(2)
                return True
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"   ⚠️  Retry {attempt + 1}/{max_retries}...")
                    time.sleep(3)
        return False
    
    def _extract_minutes_from_description(self, soup: BeautifulSoup) -> Optional[float]:
        """
        Extrait les minutes depuis la description "Based on X minutes played"
        
        Exemple: "Based on 568 minutes played" → 568
        """
        try:
            # Chercher tous les divs avec "Based on"
            for div in soup.find_all('div'):
                text = div.get_text()
                if 'Based on' in text and 'minutes' in text:
                    # Pattern: "Based on 568 minutes played"
                    match = re.search(r'Based on\s+<strong>(\d+)\s+minutes</strong>', str(div))
                    if match:
                        minutes = int(match.group(1))
                        print(f"   ⏱️  Minutes extraites : {minutes}")
                        return float(minutes)
                    
                    # Pattern alternatif sans balise strong
                    match = re.search(r'Based on\s+(\d+)\s+minutes', text)
                    if match:
                        minutes = int(match.group(1))
                        print(f"   ⏱️  Minutes extraites : {minutes}")
                        return float(minutes)
            
            print(f"   ⚠️  Minutes non trouvées dans la description")
            return None
            
        except Exception as e:
            print(f"   ⚠️  Erreur extraction minutes: {e}")
            return None
    
    def _extract_metadata_from_page(self, soup: BeautifulSoup, player_name: str) -> Dict:
        """Extrait métadonnées du joueur"""
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
                        from datetime import datetime
                        birth_year = int(birth_date.split('-')[0])
                        metadata['age'] = datetime.now().year - birth_year
                
                # Taille
                height_elem = meta_info.find('span', string=re.compile(r'\d+cm'))
                if height_elem:
                    height_match = re.search(r'(\d+)cm', height_elem.text)
                    if height_match:
                        metadata['height_cm'] = int(height_match.group(1))
        
        except Exception as e:
            print(f"   ⚠️  Erreur métadonnées: {e}")
        
        return metadata
    
    def _detect_position_from_url(self, url: str) -> str:
        """Détecte position depuis URL"""
        positions = {
            'scout_full_GK': 'GK', 'scout_full_FW': 'FW',
            'scout_full_MF': 'MF', 'scout_full_DF': 'DF',
            'scout_full_AM': 'AM', 'scout_full_DM': 'DM',
            'scout_full_FB': 'FB', 'scout_full_CB': 'CB',
            'scout_full_WB': 'WB'
        }
        
        for table_id, pos in positions.items():
            if table_id in url:
                return pos
        return 'MF'
    
    def _get_table_id_for_position(self, position: str) -> str:
        """Table ID selon position"""
        position_map = {
            'GK': 'scout_full_GK', 'FW': 'scout_full_FW',
            'MF': 'scout_full_MF', 'DF': 'scout_full_DF',
            'AM': 'scout_full_AM', 'DM': 'scout_full_DM',
            'FB': 'scout_full_FB', 'CB': 'scout_full_CB',
            'WB': 'scout_full_WB'
        }
        return position_map.get(position.upper(), 'scout_full_MF')
    
    def _normalize_player_url(self, url: str) -> str:
        """Normalise URL pour extraire page principale"""
        if '/scout/' in url:
            match = re.search(r'players/([a-f0-9]+)/', url)
            if match:
                player_id = match.group(1)
                name_match = re.search(r'/([A-Za-z-]+)-Scouting-Report', url)
                if name_match:
                    player_name = name_match.group(1)
                    return f"https://fbref.com/en/players/{player_id}/{player_name}"
        return url
    
    def _get_scouting_report_links(self, player_url: str, exclude_365_days: bool = False) -> List[Dict[str, str]]:
        """Récupère tous les scouting reports disponibles"""
        print(f"\n🔍 Recherche scouting reports...")
        
        player_url = self._normalize_player_url(player_url)
        print(f"   📍 URL: {player_url}")
        
        if not self._safe_get_page(player_url):
            return []
        
        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        scouting_reports = []
        
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            if '/scout/' in href and 'Scouting-Report' in href:
                link_text = link.get_text(strip=True)
                
                if exclude_365_days and 'Last 365 Days' in link_text:
                    continue
                
                full_url = f"https://fbref.com{href}" if href.startswith('/') else href
                
                # Extraire saison
                season_match = re.search(r'(\d{4}-\d{4})', link_text)
                if season_match:
                    season = season_match.group(1)
                elif 'Last 365 Days' in link_text:
                    season = "2024-2025"
                elif re.search(r'(\d{4})', link_text):
                    year = re.search(r'(\d{4})', link_text).group(1)
                    season = f"{year}-{int(year)+1}"
                else:
                    season = "Unknown"
                
                # Extraire compétition
                competition = link_text.split('Scouting Report')[0].strip()
                if not competition:
                    competition = "Unknown"
                
                scouting_reports.append({
                    'url': full_url,
                    'season': season,
                    'competition': competition,
                    'text': link_text
                })
        
        # Supprimer doublons
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
                print(f"   {i}. {report['season']} - {report['competition']}")
        else:
            print(f"❌ Aucun scouting report trouvé")
        
        return unique_reports
    
    def _scrape_single_report(self, url: str, table_id: str, season: str, 
                             competition: str) -> Tuple[Optional[pd.DataFrame], Optional[float]]:
        """
        Scrape un seul scouting report + extrait les minutes
        
        Returns:
            (DataFrame, minutes_played)
        """
        if not self._safe_get_page(url):
            return None, None
        
        try:
            time.sleep(3)
            
            WebDriverWait(self.driver, self.wait_time).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "table tbody tr"))
            )
            
            time.sleep(2)
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # 1. EXTRAIRE LES MINUTES (PRIORITÉ)
            minutes_played = self._extract_minutes_from_description(soup)
            
            # 2. Chercher le tableau
            table = soup.find('table', {'id': table_id})
            
            if not table:
                stats_tables = soup.find_all('table', class_='stats_table')
                if stats_tables:
                    table = stats_tables[0]
                else:
                    all_tables = soup.find_all('table')
                    if all_tables:
                        table = all_tables[0]
                    else:
                        return None, minutes_played
            
            tbody = table.find('tbody')
            if not tbody or not tbody.find_all('tr'):
                print(f"   ⚠️  Tableau vide")
                return None, minutes_played
            
            df = pd.read_html(str(table))[0]
            
            if df.empty or len(df) < 3:
                print(f"   ⚠️  DataFrame trop petit")
                return None, minutes_played
            
            df['season'] = season
            df['competition'] = competition
            
            # Ajouter les minutes au DataFrame
            if minutes_played:
                df['minutes_played'] = minutes_played
            
            return df, minutes_played
        
        except TimeoutException:
            print(f"   ❌ Timeout")
            return None, None
        except Exception as e:
            print(f"   ❌ Erreur: {str(e)[:80]}")
            return None, None
    
    def scrape_player_all_seasons(self, player_url: str, player_name: str, 
                                  exclude_365_days: bool = False) -> Tuple[pd.DataFrame, Dict, List[Dict]]:
        """
        Scrape toutes les saisons avec minutes de jeu
        
        Returns:
            - DataFrame avec colonnes 'minutes_played'
            - Métadonnées
            - Liste des saisons
        """
        print(f"\n{'='*80}")
        print(f"🎯 SCRAPING MULTI-SAISONS - {player_name}")
        print(f"{'='*80}")
        
        scouting_reports = self._get_scouting_report_links(player_url, exclude_365_days)
        
        if not scouting_reports:
            print("\n❌ Aucun scouting report trouvé")
            return None, None, []
        
        first_report_url = scouting_reports[0]['url']
        position = self._detect_position_from_url(first_report_url)
        table_id = self._get_table_id_for_position(position)
        
        print(f"\n📊 Position: {position}")
        print(f"📊 Table ID: {table_id}")
        
        if self._safe_get_page(first_report_url):
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            metadata = self._extract_metadata_from_page(soup, player_name)
            metadata['position'] = position
            
            print(f"\n📊 Métadonnées:")
            for key, value in metadata.items():
                print(f"   • {key:<15} : {value}")
        else:
            metadata = {'name': player_name, 'position': position}
        
        all_seasons_data = []
        
        print(f"\n🔄 Scraping {len(scouting_reports)} saisons...")
        
        for i, report in enumerate(scouting_reports, 1):
            print(f"\n   [{i}/{len(scouting_reports)}] {report['season']} - {report['competition'][:40]}...")
            
            df_season, minutes = self._scrape_single_report(
                url=report['url'],
                table_id=table_id,
                season=report['season'],
                competition=report['competition']
            )
            
            if df_season is not None:
                all_seasons_data.append(df_season)
                print(f"   ✅ Minutes: {minutes if minutes else 'Non trouvées'}")
            else:
                print("   ❌")
            
            time.sleep(2)
        
        if not all_seasons_data:
            print("\n❌ Aucune donnée extraite")
            return None, metadata, scouting_reports
        
        df_all_seasons = pd.concat(all_seasons_data, ignore_index=True)
        
        print(f"\n{'='*80}")
        print(f"✅ SCRAPING TERMINÉ")
        print(f"{'='*80}")
        print(f"   Saisons extraites : {len(all_seasons_data)}/{len(scouting_reports)}")
        print(f"   Lignes totales    : {len(df_all_seasons)}")
        
        # Afficher les minutes par saison
        if 'minutes_played' in df_all_seasons.columns:
            print(f"\n⏱️  MINUTES PAR SAISON:")
            for season in df_all_seasons['season'].unique():
                season_data = df_all_seasons[df_all_seasons['season'] == season]
                minutes = season_data['minutes_played'].iloc[0] if len(season_data) > 0 else None
                print(f"   • {season:<20} : {minutes:.0f} min" if minutes else f"   • {season:<20} : N/A")
        
        return df_all_seasons, metadata, scouting_reports
    
    def close(self):
        """Ferme le driver"""
        if self.driver:
            self.driver.quit()
            print("\n🔒 Driver fermé")