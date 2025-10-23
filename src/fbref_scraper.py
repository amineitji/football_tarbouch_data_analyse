"""
FBrefScraper - Version améliorée avec extraction de métadonnées + MINUTES JOUÉES
Extrait les données de scouting + infos du joueur (nom, âge, taille, minutes, etc.)
"""

import time
import pandas as pd
import re
from datetime import datetime
from bs4 import BeautifulSoup, Comment
from typing import Optional, Dict, Tuple


class FBrefScraper:
    """
    Scraper pour extraire les données de scouting + métadonnées depuis FBref
    """
    
    def __init__(self, wait_time: int = 10, headless: bool = True):
        """
        Initialise le scraper
        
        Args:
            wait_time: Temps d'attente pour le chargement des pages (secondes)
            headless: Mode headless du navigateur (True = invisible)
        """
        self.wait_time = wait_time
        self.headless = headless
        self.driver = None
        self.last_html = None
        
    def _log(self, message: str, level: str = "INFO"):
        """Log avec timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
    
    def _setup_driver(self):
        """Configure et retourne le driver Selenium"""
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            
            self._log("Configuration du driver Selenium...")
            
            chrome_options = Options()
            
            # Anti-détection
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # Performance
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            
            # User agent
            chrome_options.add_argument(
                'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            
            # Headless mode
            if self.headless:
                chrome_options.add_argument('--headless=new')
            
            driver = webdriver.Chrome(options=chrome_options)
            
            # Masquer webdriver
            driver.execute_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            )
            
            self._log("Driver Selenium configuré ✓", "SUCCESS")
            return driver
            
        except ImportError:
            self._log("Selenium non installé ! pip install selenium", "ERROR")
            raise
        except Exception as e:
            self._log(f"Erreur configuration driver : {e}", "ERROR")
            raise
    
    def _download_page(self, url: str) -> Optional[str]:
        """Télécharge une page avec Selenium"""
        try:
            self._log(f"Téléchargement : {url}")
            self.driver.get(url)
            
            # Attendre le chargement
            self._log(f"Attente du chargement ({self.wait_time}s)...")
            time.sleep(self.wait_time)
            
            page_source = self.driver.page_source
            
            # Vérifier Cloudflare
            if "cloudflare" in page_source.lower() and "checking" in page_source.lower():
                self._log("Challenge Cloudflare détecté, attente...", "WARNING")
                time.sleep(5)
                page_source = self.driver.page_source
            
            self._log(f"Page téléchargée ({len(page_source)} octets) ✓", "SUCCESS")
            self.last_html = page_source
            return page_source
            
        except Exception as e:
            self._log(f"Erreur téléchargement : {e}", "ERROR")
            return None
    
    def _extract_tables_from_comments(self, soup: BeautifulSoup, table_id: str) -> list:
        """Extrait les tables cachées dans les commentaires HTML"""
        tables = []
        comments = soup.find_all(string=lambda text: isinstance(text, Comment))
        
        self._log(f"Analyse de {len(comments)} commentaires HTML...")
        
        for comment in comments:
            comment_soup = BeautifulSoup(str(comment), 'html.parser')
            hidden_tables = comment_soup.find_all('table', {'id': table_id})
            if hidden_tables:
                tables.extend(hidden_tables)
        
        if tables:
            self._log(f"Trouvé {len(tables)} table(s) cachée(s)", "SUCCESS")
        
        return tables
    
    def _extract_table(self, html_content: str, table_id: str) -> Optional[BeautifulSoup]:
        """Extrait une table depuis le HTML"""
        self._log(f"Recherche de la table '{table_id}'...")
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Tables visibles
        visible_tables = soup.find_all('table', {'id': table_id})
        self._log(f"Tables visibles : {len(visible_tables)}")
        
        # Tables cachées
        hidden_tables = self._extract_tables_from_comments(soup, table_id)
        self._log(f"Tables cachées : {len(hidden_tables)}")
        
        all_tables = visible_tables + hidden_tables
        
        if not all_tables:
            self._log(f"Aucune table trouvée avec id='{table_id}'", "WARNING")
            return None
        
        self._log(f"Table '{table_id}' extraite ✓", "SUCCESS")
        return all_tables[0]
    
    def _parse_table_to_dataframe(self, table: BeautifulSoup) -> Optional[pd.DataFrame]:
        """Convertit une table HTML en DataFrame"""
        try:
            self._log("Parsing de la table en DataFrame...")
            
            df_list = pd.read_html(str(table))
            
            if not df_list:
                self._log("Aucune donnée trouvée dans la table", "WARNING")
                return None
            
            df = df_list[0]
            self._log(f"DataFrame créé : {df.shape[0]} lignes × {df.shape[1]} colonnes ✓", "SUCCESS")
            
            return df
            
        except Exception as e:
            self._log(f"Erreur parsing : {e}", "ERROR")
            return None
    
    def _extract_minutes_played(self, html_content: str) -> Optional[int]:
        """
        Extrait le nombre de minutes jouées depuis le scouting report
        Pattern : "Based on <strong>623 minutes</strong> played"
        """
        self._log("Extraction des minutes jouées...")
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        try:
            # Chercher le pattern "Based on X minutes"
            # Pattern exact trouvé : Based on <strong>623 minutes</strong> played
            
            # Méthode 1: Rechercher dans les divs avec style
            divs = soup.find_all('div', style=re.compile('max-width'))
            for div in divs:
                text = div.get_text()
                if 'Based on' in text and 'minutes' in text:
                    self._log(f"Texte trouvé : {text[:100]}...", "DEBUG")
                    # Pattern : "Based on 623 minutes" ou "Based on <strong>623 minutes</strong>"
                    match = re.search(r'Based on\s+(?:<strong>)?(\d+)\s+minutes?(?:</strong>)?', str(div))
                    if match:
                        minutes = int(match.group(1))
                        self._log(f"Minutes jouées trouvées : {minutes} min ✓", "SUCCESS")
                        return minutes
            
            # Méthode 2: Chercher directement dans le HTML brut
            match = re.search(r'Based on\s+<strong>(\d+)\s+minutes</strong>\s+played', html_content)
            if match:
                minutes = int(match.group(1))
                self._log(f"Minutes jouées trouvées (HTML brut) : {minutes} min ✓", "SUCCESS")
                return minutes
            
            # Méthode 3: Pattern plus général
            match = re.search(r'Based on\s+(?:<[^>]+>)?(\d+)(?:</[^>]+>)?\s+minutes', html_content, re.IGNORECASE)
            if match:
                minutes = int(match.group(1))
                self._log(f"Minutes jouées trouvées (pattern général) : {minutes} min ✓", "SUCCESS")
                return minutes
            
            # Méthode 4: Chercher "X 90's" et convertir
            match = re.search(r'Based on\s+(?:<[^>]+>)?(\d+\.?\d*)\s+90', html_content, re.IGNORECASE)
            if match:
                ninety_mins = float(match.group(1))
                minutes = int(ninety_mins * 90)
                self._log(f"Minutes jouées trouvées (90's) : {minutes} min ({ninety_mins} × 90) ✓", "SUCCESS")
                return minutes
            
            self._log("Minutes jouées non trouvées", "WARNING")
            return None
            
        except Exception as e:
            self._log(f"Erreur extraction minutes : {e}", "WARNING")
            import traceback
            traceback.print_exc()
            return None
    
    def _extract_player_metadata(self, html_content: str) -> Dict:
        """
        Extrait les métadonnées du joueur depuis le HTML
        Nom, âge, position, taille, poids, pied fort, nationalité, saison, compétition, minutes, etc.
        """
        self._log("Extraction des métadonnées du joueur...")
        
        soup = BeautifulSoup(html_content, 'html.parser')
        metadata = {}
        
        try:
            # Saison et compétition depuis le titre de la page
            title = soup.find('title')
            if title:
                title_text = title.get_text()
                # Ex: "Marco Verratti Scouting Report for 2022-2023 Champions League | FBref.com"
                self._log(f"Titre de la page : {title_text}", "DEBUG")
                
                # Extraire la saison (ex: 2022-2023)
                season_match = re.search(r'(\d{4}-\d{4})', title_text)
                if season_match:
                    metadata['season'] = season_match.group(1)
                    self._log(f"Saison trouvée : {metadata['season']}", "DEBUG")
                
                # Extraire la compétition (entre "for" et "|")
                comp_match = re.search(r'for\s+(.+?)\s*\|', title_text)
                if comp_match:
                    comp_text = comp_match.group(1).strip()
                    # Retirer la saison si elle est dans la compétition
                    if metadata.get('season'):
                        comp_text = comp_text.replace(metadata['season'], '').strip()
                    metadata['competition'] = comp_text
                    self._log(f"Compétition trouvée : {metadata['competition']}", "DEBUG")
            
            # Nom du joueur
            name_tag = soup.find('h1')
            if name_tag:
                name_span = name_tag.find('span')
                if name_span:
                    metadata['name'] = name_span.get_text(strip=True)
                else:
                    metadata['name'] = name_tag.get_text(strip=True)
                self._log(f"Nom trouvé : {metadata.get('name')}", "DEBUG")
            
            # Position et pied fort
            position_p = soup.find('p', string=lambda x: x and 'Position:' in str(x))
            if position_p:
                text = position_p.get_text()
                # Position: MF (CM-DM-WM) • Footed: Right
                if 'Position:' in text:
                    parts = text.split('Position:')[1]
                    if 'Footed:' in parts:
                        pos_part = parts.split('Footed:')[0].strip()
                        foot_part = parts.split('Footed:')[1].strip()
                        metadata['position'] = pos_part.replace('•', '').strip()
                        metadata['footed'] = foot_part
                    else:
                        metadata['position'] = parts.strip().replace('•', '').strip()
                self._log(f"Position : {metadata.get('position')}, Pied : {metadata.get('footed')}", "DEBUG")
            
            # Taille et poids
            size_p = soup.find('p', string=lambda x: x and 'cm' in str(x))
            if size_p:
                text = size_p.get_text()
                # 165cm, 59kg (5-5, 132lb)
                height_match = re.search(r'(\d+)cm', text)
                weight_match = re.search(r'(\d+)kg', text)
                if height_match:
                    metadata['height_cm'] = int(height_match.group(1))
                if weight_match:
                    metadata['weight_kg'] = int(weight_match.group(1))
                self._log(f"Taille : {metadata.get('height_cm')}cm, Poids : {metadata.get('weight_kg')}kg", "DEBUG")
            
            # Date de naissance et âge
            birth_span = soup.find('span', {'id': 'necro-birth'})
            if birth_span:
                metadata['birth_date'] = birth_span.get('data-birth')
                # Calculer l'âge
                if metadata['birth_date']:
                    birth = datetime.strptime(metadata['birth_date'], '%Y-%m-%d')
                    today = datetime.today()
                    age = today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))
                    metadata['age'] = age
                self._log(f"Date de naissance : {metadata.get('birth_date')}, Âge : {metadata.get('age')}", "DEBUG")
            
            # Lieu de naissance
            birth_place = soup.find('span', {'itemprop': 'birthPlace'})
            if birth_place:
                metadata['birth_place'] = birth_place.get_text(strip=True)
                self._log(f"Lieu de naissance : {metadata.get('birth_place')}", "DEBUG")
            
            # Citoyenneté
            citizenship_p = soup.find('p', string=lambda x: x and 'Citizenship:' in str(x))
            if citizenship_p:
                citizenship_link = citizenship_p.find('a')
                if citizenship_link:
                    metadata['citizenship'] = citizenship_link.get_text(strip=True)
                    self._log(f"Nationalité : {metadata.get('citizenship')}", "DEBUG")
            
            # Minutes jouées (NOUVEAU)
            minutes = self._extract_minutes_played(html_content)
            if minutes is not None:
                metadata['minutes_played'] = minutes
            
            self._log(f"Métadonnées extraites : {len(metadata)} champs ✓", "SUCCESS")
            
        except Exception as e:
            self._log(f"Erreur extraction métadonnées : {e}", "WARNING")
            import traceback
            traceback.print_exc()
        
        return metadata
    
    def scrape_player(self, url: str, table_id: str, player_name: str = None) -> Tuple[Optional[pd.DataFrame], Dict]:
        """
        Scrape les données d'un joueur + métadonnées
        
        Args:
            url: URL FBref du joueur
            table_id: ID de la table à extraire
            player_name: Nom du joueur (optionnel)
            
        Returns:
            Tuple (DataFrame avec les données, Dict avec métadonnées)
        """
        self._log("="*80)
        self._log(f"DÉBUT SCRAPING : {player_name or 'Joueur'}", "START")
        self._log("="*80)
        
        try:
            # Initialiser le driver si nécessaire
            if self.driver is None:
                self.driver = self._setup_driver()
            
            # Télécharger la page
            html_content = self._download_page(url)
            if not html_content:
                return None, {}
            
            # Extraire les métadonnées (incluant les minutes)
            metadata = self._extract_player_metadata(html_content)
            
            # Extraire la table
            table = self._extract_table(html_content, table_id)
            if table is None:
                return None, metadata
            
            # Parser en DataFrame
            df = self._parse_table_to_dataframe(table)
            if df is None:
                return None, metadata
            
            self._log("="*80)
            self._log(f"SCRAPING TERMINÉ ✓", "SUCCESS")
            self._log("="*80)
            
            return df, metadata
            
        except Exception as e:
            self._log(f"Erreur lors du scraping : {e}", "ERROR")
            import traceback
            traceback.print_exc()
            return None, {}
    
    def close(self):
        """Ferme le driver Selenium"""
        if self.driver:
            self.driver.quit()
            self._log("Driver Selenium fermé")
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
    
    def get_last_html(self) -> Optional[str]:
        """Retourne le dernier HTML téléchargé (pour debug)"""
        return self.last_html