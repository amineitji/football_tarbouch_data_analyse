# Makefile pour FBref Analyzer

.PHONY: help install run compare clean test setup

# Variables
PYTHON = python3
PIP = pip3
SRC_DIR = src
OUTPUT_DIRS = fbref_analysis_output tactical_analysis comparison_analysis seasons_analysis

help:
	@echo "╔═══════════════════════════════════════════════════════════════╗"
	@echo "║                                                               ║"
	@echo "║          ⚽ FBref Analyzer - Commandes disponibles ⚽         ║"
	@echo "║                                                               ║"
	@echo "╚═══════════════════════════════════════════════════════════════╝"
	@echo ""
	@echo "📦 Installation:"
	@echo "  make setup      - Installation complète (dépendances + structure)"
	@echo "  make install    - Installer uniquement les dépendances Python"
	@echo ""
	@echo "🚀 Exécution:"
	@echo "  make run        - Lancer l'analyseur (mode interactif)"
	@echo "  make compare    - Lancer en mode comparaison directe"
	@echo ""
	@echo "🧹 Maintenance:"
	@echo "  make clean      - Nettoyer les fichiers générés"
	@echo "  make clean-all  - Nettoyer tout (outputs + cache Python)"
	@echo "  make test       - Tester l'installation"
	@echo ""
	@echo "📋 Informations:"
	@echo "  make info       - Afficher la structure du projet"
	@echo ""

setup: install
	@echo "📁 Création de la structure des dossiers..."
	@mkdir -p $(OUTPUT_DIRS)
	@echo "✅ Structure créée"
	@echo ""
	@echo "🎉 Installation complète terminée!"
	@echo "👉 Utilisez 'make run' pour commencer"

install:
	@echo "╔═══════════════════════════════════════════════════════════════╗"
	@echo "║           📦 Installation des dépendances Python             ║"
	@echo "╚═══════════════════════════════════════════════════════════════╝"
	@echo ""
	@if [ -f requirements.txt ]; then \
		echo "📥 Installation depuis requirements.txt..."; \
		$(PIP) install -r requirements.txt; \
	else \
		echo "📥 Installation manuelle des packages..."; \
		$(PIP) install pandas numpy matplotlib seaborn selenium beautifulsoup4 lxml html5lib; \
	fi
	@echo ""
	@echo "✅ Dépendances installées avec succès"

run:
	@echo "╔═══════════════════════════════════════════════════════════════╗"
	@echo "║              🚀 Lancement de l'analyseur FBref               ║"
	@echo "╚═══════════════════════════════════════════════════════════════╝"
	@echo ""
	@cd $(SRC_DIR) && $(PYTHON) main.py

compare: run
	@echo "Mode comparaison lancé via l'interface interactive"

test:
	@echo "╔═══════════════════════════════════════════════════════════════╗"
	@echo "║                   🧪 Test de l'installation                  ║"
	@echo "╚═══════════════════════════════════════════════════════════════╝"
	@echo ""
	@echo "🔍 Vérification de Python..."
	@$(PYTHON) --version
	@echo ""
	@echo "🔍 Vérification des modules Python..."
	@$(PYTHON) -c "import pandas; print('  ✅ pandas')" 2>/dev/null || echo "  ❌ pandas manquant"
	@$(PYTHON) -c "import numpy; print('  ✅ numpy')" 2>/dev/null || echo "  ❌ numpy manquant"
	@$(PYTHON) -c "import matplotlib; print('  ✅ matplotlib')" 2>/dev/null || echo "  ❌ matplotlib manquant"
	@$(PYTHON) -c "import seaborn; print('  ✅ seaborn')" 2>/dev/null || echo "  ❌ seaborn manquant"
	@$(PYTHON) -c "import selenium; print('  ✅ selenium')" 2>/dev/null || echo "  ❌ selenium manquant"
	@$(PYTHON) -c "from bs4 import BeautifulSoup; print('  ✅ beautifulsoup4')" 2>/dev/null || echo "  ❌ beautifulsoup4 manquant"
	@echo ""
	@echo "🔍 Vérification de la structure du projet..."
	@test -f $(SRC_DIR)/main.py && echo "  ✅ main.py" || echo "  ❌ main.py manquant"
	@test -f $(SRC_DIR)/fbref_scraper.py && echo "  ✅ fbref_scraper.py" || echo "  ❌ fbref_scraper.py manquant"
	@test -f $(SRC_DIR)/data_cleaner.py && echo "  ✅ data_cleaner.py" || echo "  ❌ data_cleaner.py manquant"
	@test -f $(SRC_DIR)/player_analyzer.py && echo "  ✅ player_analyzer.py" || echo "  ❌ player_analyzer.py manquant"
	@test -f $(SRC_DIR)/player_comparator.py && echo "  ✅ player_comparator.py" || echo "  ❌ player_comparator.py manquant"
	@echo ""
	@echo "✅ Tests terminés"

clean:
	@echo "╔═══════════════════════════════════════════════════════════════╗"
	@echo "║              🧹 Nettoyage des fichiers générés               ║"
	@echo "╚═══════════════════════════════════════════════════════════════╝"
	@echo ""
	@echo "🗑️  Suppression des dossiers de sortie..."
	@rm -rf $(OUTPUT_DIRS)
	@echo "✅ Fichiers de sortie supprimés"

clean-all: clean
	@echo ""
	@echo "🗑️  Suppression du cache Python..."
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@find . -type f -name "*.pyo" -delete 2>/dev/null || true
	@find . -type d -name "*.egg-info" -ex