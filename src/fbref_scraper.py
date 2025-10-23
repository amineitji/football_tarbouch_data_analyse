"""
FBrefScraper - Classe pour scraper les données de scouting FBref
Gère le téléchargement et l'extraction des données d'un seul joueur
"""

import time
import pandas as pd
from datetime import datetime
from bs4 import BeautifulSoup, Comment
from typing import Optional, Dict, List


class FBrefScraper:
    """
    Scraper pour extraire les données de scouting depuis FBref
    Utilise Selenium pour contourner les protections Cloudflare
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
        """
        Télécharge une page avec Selenium
        
        Args:
            url: URL de la page à télécharger
            
        Returns:
            HTML de la page ou None si erreur
        """
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
    
    def _extract_tables_from_comments(self, soup: BeautifulSoup, table_id: str) -> List:
        """
        Extrait les tables cachées dans les commentaires HTML
        FBref cache souvent les tables dans <!-- ... -->
        
        Args:
            soup: Objet BeautifulSoup
            table_id: ID de la table à extraire
            
        Returns:
            Liste des tables trouvées
        """
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
        """
        Extrait une table (visible ou cachée) depuis le HTML
        
        Args:
            html_content: Contenu HTML de la page
            table_id: ID de la table à extraire
            
        Returns:
            Objet BeautifulSoup de la table ou None
        """
        self._log(f"Recherche de la table '{table_id}'...")
        
        soup = BeautifulSoup(html_content, 'lxml')
        
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
        """
        Convertit une table HTML en DataFrame pandas
        
        Args:
            table: Objet BeautifulSoup de la table
            
        Returns:
            DataFrame ou None si erreur
        """
        try:
            self._log("Parsing de la table en DataFrame...")
            
            # Utiliser pandas pour parser
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
    
    def scrape_player(self, url: str, table_id: str, player_name: str = None) -> Optional[pd.DataFrame]:
        """
        Scrape les données d'un joueur
        
        Args:
            url: URL FBref du joueur
            table_id: ID de la table à extraire (ex: 'scout_full_MF')
            player_name: Nom du joueur (pour les logs)
            
        Returns:
            DataFrame avec les données ou None si erreur
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
                return None
            
            # Extraire la table
            table = self._extract_table(html_content, table_id)
            if table is None:
                return None
            
            # Parser en DataFrame
            df = self._parse_table_to_dataframe(table)
            if df is None:
                return None
            
            # Ajouter des métadonnées
            df.attrs['player_name'] = player_name
            df.attrs['url'] = url
            df.attrs['table_id'] = table_id
            df.attrs['scraped_at'] = datetime.now().isoformat()
            
            self._log("="*80)
            self._log(f"SCRAPING TERMINÉ : {len(df)} statistiques extraites ✓", "SUCCESS")
            self._log("="*80)
            
            return df
            
        except Exception as e:
            self._log(f"Erreur lors du scraping : {e}", "ERROR")
            import traceback
            traceback.print_exc()
            return None
    
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


# Exemple d'utilisation
if __name__ == "__main__":
    # Configuration
    PLAYER_URL = 'https://fbref.com/en/players/1467af0d/scout/11454/Marco-Verratti-Scouting-Report'
    TABLE_ID = 'scout_full_MF'
    PLAYER_NAME = 'Marco Verratti'
    
    # Utilisation avec context manager
    with FBrefScraper(wait_time=10, headless=True) as scraper:
        df = scraper.scrape_player(PLAYER_URL, TABLE_ID, PLAYER_NAME)
        
        if df is not None:
            print("\n" + "="*80)
            print("APERÇU DES DONNÉES")
            print("="*80)
            print(df.head(10))
            
            # Sauvegarder
            output_file = 'verratti_raw_data.csv'
            df.to_csv(output_file, index=False, encoding='utf-8-sig')
            print(f"\n✓ Données sauvegardées : {output_file}")