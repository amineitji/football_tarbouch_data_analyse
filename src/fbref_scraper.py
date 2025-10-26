"""
FBrefScraper V10 - Correction de l'import NumPy
- Ajout de 'import numpy as np'
- Correction de l'appel pd.np.random.rand() en np.random.rand()
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
import numpy as np # <-- AJOUT DE L'IMPORT
from typing import Dict, Optional, Tuple, List


class FBrefScraper:
    """Scraper FBref avec attente robuste et sélection de la bonne table"""
    
    def __init__(self, wait_time: int = 20, headless: bool = True):
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
        """Charge une page avec retry et gestion des cookies"""
        for attempt in range(max_retries):
            try:
                self.driver.get(url)
                time.sleep(2) 
                
                # --- GESTION COOKIES ---
                try:
                    cookie_button = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, "button.fc-button.fc-cta-consent"))
                    )
                    cookie_button.click()
                    print("   🍪 Cookie consent cliqué.")
                    time.sleep(1) 
                except (TimeoutException, NoSuchElementException):
                    print("   (Pas de banner cookie trouvé, ou déjà accepté)")
                # --- FIN ---

                return True
                
            except Exception as e:
                print(f"   ⚠️  Erreur chargement page: {e}")
                if attempt < max_retries - 1:
                    print(f"   ⚠️  Retry {attempt + 1}/{max_retries}...")
                    time.sleep(3)
        return False
    
    def _extract_minutes_from_description(self, soup: BeautifulSoup) -> Optional[float]:
        """Extrait les minutes depuis la description "Based on X minutes played" """
        try:
            # Cibler plus spécifiquement le footer pour les minutes
            footer_div = soup.find('div', class_='footer no_hide_long', id=re.compile(r'tfooter_scout_full_'))
            if footer_div:
                 match = re.search(r'Based on\s+<strong>(\d+)\s+minutes</strong>', str(footer_div))
                 if match:
                    minutes = int(match.group(1))
                    print(f"   ⏱️  Minutes extraites (footer) : {minutes}")
                    return float(minutes)
            
            # Fallback si non trouvé dans le footer spécifique (ancienne méthode)
            for div in soup.find_all('div'):
                text = div.get_text()
                if 'Based on' in text and 'minutes' in text:
                    match = re.search(r'Based on\s+<strong>(\d+)\s+minutes</strong>', str(div))
                    if match:
                        minutes = int(match.group(1))
                        print(f"   ⏱️  Minutes extraites (fallback) : {minutes}")
                        return float(minutes)
                    
                    match = re.search(r'Based on\s+(\d+)\s+minutes', text)
                    if match:
                        minutes = int(match.group(1))
                        print(f"   ⏱️  Minutes extraites (fallback) : {minutes}")
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
                position_p = meta_info.find('p', string=re.compile(r'Position:'))
                if position_p:
                     pos_text = position_p.get_text(strip=True)
                     match = re.search(r'Position:\s*(\w+)', pos_text)
                     if match:
                         metadata['position'] = match.group(1).split(',')[0] 

                # Âge
                birth_info = meta_info.find('span', {'id': 'necro-birth'})
                if birth_info:
                    birth_date = birth_info.get('data-birth', '')
                    if birth_date:
                        from datetime import datetime
                        birth_year = int(birth_date.split('-')[0])
                        metadata['age'] = datetime.now().year - birth_year
                
                # Taille
                height_p = meta_info.find('p', string=re.compile(r'\d+cm'))
                if height_p:
                     height_match = re.search(r'(\d+)cm', height_p.get_text())
                     if height_match:
                        metadata['height_cm'] = int(height_match.group(1))
        
        except Exception as e:
            print(f"   ⚠️  Erreur métadonnées: {e}")
        
        return metadata
    
    def _detect_position_from_url(self, url: str) -> str:
        """ OBSOLÈTE pour déterminer l'ID de table, mais gardé pour la position par défaut"""
        positions = {
            'scout_full_AM': 'AM', 'scout_full_DM': 'DM', 
            'scout_full_FB': 'FB', 'scout_full_CB': 'CB', 
            'scout_full_WB': 'WB', 'scout_full_GK': 'GK', 
            'scout_full_FW': 'FW', 'scout_full_MF': 'MF', 
            'scout_full_DF': 'DF',
        }
        for table_id_part, pos in positions.items():
             if f"scout#{table_id_part}" in url or f"/{table_id_part}/" in url or table_id_part in url.split('/')[-1]:
                 return pos
        return 'MF' 

    def _get_table_id_for_position(self, position: str) -> str:
        """Table ID selon position (moins utilisé maintenant)"""
        position_map = {
            'GK': 'scout_full_GK', 'FW': 'scout_full_FW',
            'MF': 'scout_full_MF', 'DF': 'scout_full_DF',
            'AM': 'scout_full_AM', 'DM': 'scout_full_DM',
            'FB': 'scout_full_FB', 'CB': 'scout_full_CB',
            'WB': 'scout_full_WB'
        }
        primary_pos = position.split(',')[0].strip().upper()
        return position_map.get(primary_pos, 'scout_full_MF')

    def _normalize_player_url(self, url: str) -> str:
        """Normalise URL pour extraire page principale"""
        if '/scout/' in url:
            match = re.search(r'players/([a-f0-9]+)/', url)
            if match:
                player_id = match.group(1)
                base_url_match = re.match(r'(https://fbref.com/en/players/[a-f0-9]+/)', url)
                if base_url_match:
                     name_match = re.search(r'/([A-Za-z-]+)$', url.split('/scout/')[0])
                     if name_match:
                        player_name = name_match.group(1)
                        return f"{base_url_match.group(1)}{player_name}"
                     else:
                        return base_url_match.group(1) 
        return url

    def _get_scouting_report_links(self, player_url: str, exclude_365_days: bool = False) -> List[Dict[str, str]]:
        """Récupère tous les scouting reports disponibles"""
        print(f"\n🔍 Recherche scouting reports...")
        
        player_main_url = self._normalize_player_url(player_url)
        print(f"   📍 URL principale: {player_main_url}")
        
        if not self._safe_get_page(player_main_url):
            print("   ❌ Impossible de charger la page principale.")
            return []
        
        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        scouting_reports = []
        
        scouting_section = soup.find('div', id='inner_nav') 
        if not scouting_section:
             scouting_section = soup 

        links = scouting_section.find_all('a', href=re.compile(r'/scout/'))
        print(f"   🔎 {len(links)} liens potentiels trouvés...")

        for link in links:
            href = link.get('href', '')
            if 'Scouting-Report' in href: 
                link_text = link.get_text(strip=True)
                
                if exclude_365_days and ('Last 365 Days' in link_text or '365_m1' in href):
                    continue
                
                full_url = f"https://fbref.com{href}" if href.startswith('/') else href
                
                season_match = re.search(r'(\d{4}-\d{4})', link_text)
                season = "Unknown" 
                if season_match:
                    season = season_match.group(1)
                elif 'Last 365 Days' in link_text or '365_m1' in href:
                    current_year = pd.Timestamp.now().year
                    current_month = pd.Timestamp.now().month
                    season_start = current_year - 1 if current_month < 7 else current_year
                    # Correction pour la saison actuelle basée sur la date système
                    # Si nous sommes en Octobre 2025, la saison en cours est 2025-2026
                    season_start_correct = current_year if current_month >= 7 else current_year -1
                    season = f"{season_start_correct}-{season_start_correct + 1}"

                elif re.search(r'(\d{4})', link_text): 
                     year = re.search(r'(\d{4})', link_text).group(1)
                     # Assumons que l'année mentionnée est l'année de début de saison
                     season = f"{year}-{int(year)+1}"
                
                competition = link_text.replace(season, '').replace('Scouting Report', '').strip()
                if not competition or competition == season: 
                    comp_match = re.search(r'/scout/\d+/(.*?)-Scouting-Report', href)
                    if comp_match:
                         # Extraction plus générique du nom du joueur pour le retirer
                         player_name_in_url_part = full_url.split('/scout/')[0].split('/')[-1]
                         competition = comp_match.group(1).replace('-', ' ').replace(player_name_in_url_part,'').strip()
                         competition = competition.replace(season,'').strip()

                if not competition: competition = "Unknown Competition"

                scouting_reports.append({
                    'url': full_url,
                    'season': season,
                    'competition': competition,
                    'text': link_text 
                })
        
        seen_urls = set()
        unique_reports = []
        for report in scouting_reports:
            if report['url'] not in seen_urls:
                seen_urls.add(report['url'])
                unique_reports.append(report)
        
        if unique_reports:
            print(f"✅ {len(unique_reports)} scouting reports uniques trouvés:")
            for i, report in enumerate(unique_reports, 1):
                # Nettoyage affichage compétition si contient des chiffres seuls (potentiellement ID)
                display_comp = re.sub(r'^\d+\s*', '', report['competition']).strip()
                print(f"   {i}. {report['season']} - {display_comp} ('{report['text']}')")
        else:
            print(f"❌ Aucun scouting report trouvé")
        
        return unique_reports
    
    def _scrape_single_report(self, url: str, season: str, 
                             competition: str) -> Tuple[Optional[pd.DataFrame], Optional[float]]:
        """ Scrape un seul scouting report en attendant le footer """
        if not self._safe_get_page(url):
            return None, None
        
        try:
            wait_condition = (By.CSS_SELECTOR, "div.footer.no_hide_long strong")
            print(f"      -> Attente du footer ({self.wait_time}s max)...")
            
            WebDriverWait(self.driver, self.wait_time).until(
                EC.presence_of_element_located(wait_condition)
            )
            print("      -> Footer trouvé.")
            
            time.sleep(3) 
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            minutes_played = self._extract_minutes_from_description(soup)
            
            all_scout_tables = soup.find_all('table', {'id': re.compile(r'^scout_full_')})
            
            if not all_scout_tables:
                print(f"   ⚠️  Aucune table (id commençant par 'scout_full_') trouvée après l'attente.")
                return None, minutes_played
            
            table = all_scout_tables[-1] 
            table_id_found = table.get('id')
            print(f"      -> Tableau complet trouvé : {table_id_found}")
            
            tbody = table.find('tbody')
            if not tbody or not tbody.find_all('tr'):
                print(f"   ⚠️  Tableau '{table_id_found}' est vide.")
                return None, minutes_played
            
            try:
                df_list = pd.read_html(str(table))
                if not df_list:
                    print(f"   ⚠️  pd.read_html n'a retourné aucune table pour '{table_id_found}'.")
                    return None, minutes_played
                df = df_list[0]
            except ValueError as e:
                print(f"   ⚠️  Erreur pandas lors de la lecture de la table '{table_id_found}': {e}")
                return None, minutes_played

            if df.empty or len(df) < 3:
                print(f"   ⚠️  DataFrame extrait de '{table_id_found}' est trop petit ou vide.")
                return None, minutes_played
            
            stat_col = None
            per90_col = None
            
            for col in df.columns:
                col_str = str(col).lower().strip()
                if 'statistic' in col_str:
                    stat_col = col
                elif 'per' in col_str and '90' in col_str:
                    per90_col = col
            
            if stat_col is None and len(df.columns) >= 1: stat_col = df.columns[0]
            if per90_col is None and len(df.columns) >= 2: per90_col = df.columns[1]

            if stat_col is None or per90_col is None:
                 print(f"   ⚠️  Impossible de trouver les colonnes 'Statistic' ou 'Per 90' dans la table '{table_id_found}'. Colonnes: {df.columns}")
                 return None, minutes_played

            df_clean = df.copy()
            df_clean = df_clean[pd.to_numeric(df_clean[per90_col], errors='coerce').notna()]
            df_clean = df_clean[df_clean[stat_col].notna()]
            df_clean = df_clean[df_clean[stat_col].astype(str).str.strip() != ""]
            df_clean = df_clean[~df_clean[stat_col].astype(str).str.contains("Statistic|Per 90|Percentile", case=False, regex=True)] 

            stats_dict = {}
            for _, row in df_clean.iterrows():
                stat_name = str(row[stat_col]).strip()
                stat_value = str(row[per90_col]).strip()
                stat_name_clean = re.sub(r'[^\w%]+', '_', stat_name) 
                stat_name_clean = stat_name_clean.replace('%','pct').strip('_') 
                if stat_name_clean: 
                    stats_dict[stat_name_clean] = stat_value
            
            if not stats_dict:
                 print(f"   ⚠️  Aucune stat valide extraite après nettoyage pour la table '{table_id_found}'.")
                 return None, minutes_played

            df_horizontal = pd.DataFrame([stats_dict])
            
            df_horizontal.insert(0, 'season', season)
            df_horizontal.insert(1, 'competition', competition)
            
            if minutes_played:
                df_horizontal.insert(2, 'minutes_played', minutes_played)
            
            return df_horizontal, minutes_played
        
        except TimeoutException:
            print(f"   ❌ Timeout en attendant le footer de la page.")
            return None, None
        except Exception as e:
            print(f"   ❌ Erreur inattendue: {str(e)[:150]}")
            import traceback
            traceback.print_exc() 
            return None, None
    
    def scrape_player_all_seasons(self, player_url: str, player_name: str, 
                                  exclude_365_days: bool = False) -> Tuple[pd.DataFrame, Dict, List[Dict]]:
        """ Scrape toutes les saisons avec la nouvelle logique d'attente/sélection """
        print(f"\n{'='*80}")
        print(f"🎯 SCRAPING MULTI-SAISONS - {player_name}")
        print(f"{'='*80}")
        
        scouting_reports = self._get_scouting_report_links(player_url, exclude_365_days)
        
        if not scouting_reports:
            print("\n❌ Aucun scouting report trouvé sur la page principale.")
            if '/scout/' in player_url and 'Scouting-Report' in player_url:
                 print(f"   ℹ️ Tentative de scraper directement l'URL fournie: {player_url}")
                 season = "UnknownSeason"
                 competition = "UnknownCompetition"
                 scouting_reports = [{'url': player_url, 'season': season, 'competition': competition, 'text': 'Direct URL'}]
            else:
                 return None, {'name': player_name, 'position': 'Unknown'}, []

        first_report_url_meta = scouting_reports[0]['url']
        metadata = {'name': player_name, 'position': 'Unknown'} 
        
        if self._safe_get_page(first_report_url_meta):
            soup_meta = BeautifulSoup(self.driver.page_source, 'html.parser')
            metadata = self._extract_metadata_from_page(soup_meta, player_name)
            if 'position' not in metadata or not metadata['position']:
                 metadata['position'] = self._detect_position_from_url(first_report_url_meta) 
            print(f"\n📊 Métadonnées (extraites de {first_report_url_meta}):")
            for key, value in metadata.items():
                print(f"   • {key:<15} : {value}")
        else:
             print(f"   ⚠️ Impossible de charger {first_report_url_meta} pour les métadonnées.")
             metadata['position'] = self._detect_position_from_url(player_url)

        all_seasons_data = []
        
        print(f"\n🔄 Scraping {len(scouting_reports)} saison(s)/rapport(s)...")
        
        for i, report in enumerate(scouting_reports, 1):
            print(f"\n   [{i}/{len(scouting_reports)}] {report['season']} - {report['competition'][:40]}...")
            print(f"      -> URL: {report['url']}")
            
            df_season, minutes = self._scrape_single_report(
                url=report['url'],
                season=report['season'],
                competition=report['competition']
            )
            
            if df_season is not None:
                all_seasons_data.append(df_season)
                print(f"   ✅ Données extraites. Minutes: {minutes if minutes else 'Non trouvées'}")
            else:
                print(f"   ❌ Échec de l'extraction pour ce rapport.")
            
            # --- CORRECTION ICI ---
            time.sleep(1 + np.random.rand()) # Utiliser np directement
            # --- FIN CORRECTION ---

        if not all_seasons_data:
            print("\n❌ Aucune donnée n'a pu être extraite pour aucun rapport.")
            return None, metadata, scouting_reports
        
        try:
             df_all_seasons = pd.concat(all_seasons_data, ignore_index=True, sort=False)
        except Exception as e:
             print(f"\n❌ Erreur lors de la concaténation des DataFrames: {e}")
             return all_seasons_data[0] if all_seasons_data else None, metadata, scouting_reports

        print(f"\n{'='*80}")
        print(f"✅ SCRAPING TERMINÉ")
        print(f"{'='*80}")
        print(f"   Rapports extraits avec succès : {len(all_seasons_data)}/{len(scouting_reports)}")
        print(f"   Lignes totales    : {len(df_all_seasons)}")
        
        if 'minutes_played' in df_all_seasons.columns:
            print(f"\n⏱️  MINUTES PAR RAPPORT:")
            grouped = df_all_seasons.groupby(['season', 'competition'])['minutes_played'].first()
            for (season, competition), minutes in grouped.items():
                 minutes_str = f"{minutes:.0f} min" if pd.notna(minutes) else "N/A"
                 # Nettoyage affichage compétition
                 display_comp = re.sub(r'^\d+\s*', '', competition).strip()
                 print(f"   • {season:<12} | {display_comp:<40} : {minutes_str}")

        return df_all_seasons, metadata, scouting_reports
    
    def close(self):
        """Ferme le driver"""
        if self.driver:
            try:
                self.driver.quit()
                print("\n🔒 Driver fermé")
            except Exception as e:
                print(f"   ⚠️ Erreur lors de la fermeture du driver: {e}")