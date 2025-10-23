╔═══════════════════════════════════════════════════════════════╗
║         FBREF SCRAPER - GUIDE DE DÉMARRAGE RAPIDE            ║
╚═══════════════════════════════════════════════════════════════╝

🎯 OBJECTIF : Scraper les données de scouting FBref en CSV

📋 ÉTAPES D'INSTALLATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1️⃣  Rendre le script exécutable
   chmod +x install.sh

2️⃣  Lancer l'installation automatique
   ./install.sh

   OU installation manuelle :
   pip install --break-system-packages selenium beautifulsoup4 pandas lxml

3️⃣  Installer Chrome/Chromium
   sudo apt-get install -y chromium-browser chromium-chromedriver


🚀 UTILISATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

▶️  Lancer le scraper :
   python3 fbref_selenium_scraper.py

📊 Les données seront exportées dans :
   ./fbref_exports/scout_full_MF_table_1.csv


⚙️  PERSONNALISER L'URL
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Ouvrez fbref_selenium_scraper.py et modifiez :

CONFIG = {
    'url': 'VOTRE_URL_FBREF_ICI',
    'target_table_id': 'scout_full_MF',  # ou FW, DF, GK
    'wait_time': 10,  # Augmentez si la page est lente
}


📚 EXEMPLES D'URLS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Marco Verratti (MF) :
https://fbref.com/en/players/1467af0d/scout/11454/Marco-Verratti-Scouting-Report

Kylian Mbappé (FW) :
https://fbref.com/en/players/42fd9c7f/scout/11454/Kylian-Mbappe-Scouting-Report

Karim Benzema (FW) :
https://fbref.com/en/players/70d74ece/scout/11454/Karim-Benzema-Scouting-Report


🔍 IDs DE TABLES PAR POSITION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

• Milieu (MF) : scout_full_MF
• Attaquant (FW) : scout_full_FW  
• Défenseur (DF) : scout_full_DF
• Gardien (GK) : scout_full_GK


🛠️  RÉSOLUTION DE PROBLÈMES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

❌ Table non trouvée ?
   → Augmentez wait_time à 15 ou 20 secondes
   → Vérifiez l'ID dans page_source_selenium.html

❌ Selenium non trouvé ?
   → pip install --break-system-packages selenium

❌ Chrome/Chromium manquant ?
   → sudo apt-get install chromium-browser chromium-chromedriver

❌ Voir le navigateur en action ?
   → Commentez la ligne : chrome_options.add_argument('--headless=new')


💡 ASTUCES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✓ Le script contourne automatiquement Cloudflare
✓ Les logs détaillés vous guident en temps réel
✓ Le HTML brut est sauvegardé pour debug
✓ Les tables cachées sont automatiquement détectées


📧 BESOIN D'AIDE ?
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Lisez les logs (très détaillés avec timestamps)
2. Consultez page_source_selenium.html
3. Vérifiez le README.md pour plus de détails


⚠️  UTILISATION RESPONSABLE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

• Usage personnel uniquement
• Respectez les délais entre requêtes
• Ne surchargez pas les serveurs FBref
• Consultez les ToS de FBref


╔═══════════════════════════════════════════════════════════════╗
║                    BON SCRAPING ! 🎉                          ║
╚═══════════════════════════════════════════════════════════════╝