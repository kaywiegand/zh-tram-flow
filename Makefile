# Makefile – zh_tram_flow
# -------------------------
# Shortcuts für Entwicklung & Setup.
# Verwendung: make <target>
#
# Voraussetzung: uv installiert (pip install uv)

.PHONY: setup install kernel test lint clean help maps

setup: ## Virtuelle Umgebung erstellen + Dependencies installieren
	uv venv
	. .venv/bin/activate && uv pip install -e ".[dan,dev]"
	@echo ""
	@echo "✅ Setup fertig. Umgebung aktivieren mit:"
	@echo "   source .venv/bin/activate"

install: ## Dependencies (neu) installieren
	. .venv/bin/activate && uv pip install -e ".[dan,dev]"

kernel: ## Jupyter Kernel registrieren
	. .venv/bin/activate && python -m ipykernel install --user --name zh_tram_flow --display-name "Python (zh_tram_flow)"
	@echo "✅ Kernel 'zh_tram_flow' registriert."

test: ## Tests ausführen
	. .venv/bin/activate && pytest tests/ -v

lint: ## Code prüfen (ruff + black)
	. .venv/bin/activate && ruff check src/ && black --check src/

format: ## Code formatieren (black)
	. .venv/bin/activate && black src/

clean: ## Umgebung + Cache aufräumen
	rm -rf .venv __pycache__ src/*.egg-info .pytest_cache
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@echo "✅ Aufgeräumt."

maps: ## Alle Karten (reports/figures/*.html) im Browser öffnen
	@for f in reports/figures/*.html; do open "$$f"; done
	@echo "✅ Karten geöffnet."

map-tram: ## tram_lines_map.html im Browser öffnen
	open reports/figures/tram_lines_map.html

map-network: ## network_changes_map.html im Browser öffnen
	open reports/figures/network_changes_map.html

report: ## Notebook als HTML exportieren (kein Code sichtbar)
	. .venv/bin/activate && jupyter nbconvert --to html --no-input notebooks/04_insights.ipynb --output ../reports/report.html
	open reports/report.html
	@echo "✅ Report exportiert und geöffnet."

help: ## Alle verfügbaren Targets anzeigen
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'
