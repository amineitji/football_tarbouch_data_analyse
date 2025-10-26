# Makefile for FBref Universal Analyzer

# --- Variables ---
# Use python3 by default
PYTHON = python3
# Default pip command
PIP = $(PYTHON) -m pip
# Requirements file
REQS = requirements.txt
# Source directory (assuming all .py files are in the same directory as the Makefile)
SRC_DIR = ./src
# Main script
MAIN_SCRIPT = $(SRC_DIR)/main.py
# Output directories
OUTPUT_DIR = ./fbref_analysis_output
TACTICAL_DIR = ./tactical_analysis
COMPARISON_DIR = ./comparison_analysis
# Python cache directory name
CACHE_DIR = __pycache__

# Phony targets don't represent files
.PHONY: all install run clean help lint

# --- Targets ---

# Default target: show help
all: help

# Install dependencies from requirements.txt
# NOTE: You need to create a requirements.txt file!
install: $(REQS)
	@echo "--- Installing dependencies from $(REQS)... ---"
	$(PIP) install -r $(REQS)
	@echo "--- Dependencies installed. ---"

# Run the main analysis script
run:
	@echo "--- Running FBref Analyzer ---"
	$(PYTHON) $(MAIN_SCRIPT)
	@echo "--- Analysis finished. ---"

# Clean up generated files and directories
clean:
	@echo "--- Cleaning up generated files... ---"
	-rm -rf $(OUTPUT_DIR)
	-rm -rf $(TACTICAL_DIR)
	-rm -rf $(COMPARISON_DIR)
	-find $(SRC_DIR) -type d -name '$(CACHE_DIR)' -exec rm -rf {} +
	-find $(SRC_DIR) -type f -name '*.pyc' -delete
	-find $(SRC_DIR) -type f -name '*~' -delete
	@echo "--- Cleanup complete. ---"

# Lint the code using flake8 (optional, requires flake8 installed)
lint:
	@echo "--- Linting Python code with flake8... ---"
	$(PIP) show flake8 > /dev/null || (echo "flake8 not found, please run 'make install-dev' or 'pip install flake8'" && exit 1)
	flake8 $(SRC_DIR)/*.py
	@echo "--- Linting complete. ---"

# Help message
help:
	@echo "Makefile for FBref Universal Analyzer"
	@echo ""
	@echo "Usage:"
	@echo "  make install    Install required Python packages from $(REQS)"
	@echo "  make run        Run the main analysis script ($(MAIN_SCRIPT))"
	@echo "  make clean      Remove generated output files and cache"
	@echo "  make lint       Check Python code style using flake8 (requires flake8)"
	@echo "  make help       Show this help message"
	@echo ""
	@echo "Note: Ensure you have a '$(REQS)' file with necessary packages:"
	@echo "      pandas, numpy, matplotlib, selenium, beautifulsoup4, lxml, flake8 (optional)"

# --- Requirements File Check ---
# Check if requirements.txt exists for the install target
$(REQS):
	@echo "Error: '$(REQS)' not found."
	@echo "Please create it with your project dependencies (e.g., pandas, numpy, matplotlib, selenium, beautifulsoup4, lxml)."
	@exit 1