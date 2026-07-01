# Makefile – zh_tram_flow
# -------------------------
# Shortcuts für Entwicklung & Setup.
# Verwendung: make <target>
#
# Voraussetzung: uv installiert (pip install uv)

.PHONY: setup install kernel test lint clean help maps portfolio

setup: ## Virtuelle Umgebung erstellen + Dependencies installieren
	uv venv
	. .venv/bin/activate && uv pip install -e ".[dan,dsc,dev]"
	@echo ""
	@echo "✅ Setup fertig. Umgebung aktivieren mit:"
	@echo "   source .venv/bin/activate"

install: ## Dependencies (neu) installieren
	. .venv/bin/activate && uv pip install -e ".[dan,dsc,dev]"

kernel: ## Jupyter Kernel registrieren
	. .venv/bin/activate && python -m ipykernel install --user --name zh_tram_flow --display-name "Python (zh_tram_flow)"
	@echo "✅ Kernel 'zh_tram_flow' registriert."

test: ## Tests ausführen
	uv run --extra dev python -m pytest tests/ -v

lint: ## Code prüfen (ruff + black)
	. .venv/bin/activate && ruff check src/ && black --check src/

format: ## Code formatieren (black)
	. .venv/bin/activate && black src/

clean: ## Umgebung + Cache aufräumen
	rm -rf .venv __pycache__ src/*.egg-info .pytest_cache
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@echo "✅ Aufgeräumt."

maps: ## Alle interaktiven Karten (public/img/*.html) im Browser öffnen
	@for f in public/img/*.html; do open "$$f"; done
	@echo "✅ Karten geöffnet."

map-stops: ## Interaktive Haltestellen-Delay-Karte öffnen
	open public/img/geo-stop-delay-interactive.html

map-network: ## Interaktive Netzwerk-Delta-Karte öffnen
	open public/img/network-line-delta-map.html

map-meteo: ## Interaktive Wetter-Impact-Karte öffnen
	open public/img/meteo-weather-impact-map.html

# Generische Portfolio-Pipeline-Scripts leben im Skill (projektübergreifend wiederverwendbar,
# siehe /Users/kaywiegand/Workspace/skills/project-case/PORTFOLIO_PIPELINE.md), nicht im Projekt.
SKILL_SCRIPTS := /Users/kaywiegand/Workspace/skills/project-case/scripts

portfolio: ## Portfolio-Artefakte sicher regenerieren (archiviert alten Stand → archive/vN, dann index + Views aus slides.yaml/portfolio.md)
	uv run python $(SKILL_SCRIPTS)/archive_portfolio_artifacts.py
	uv run python $(SKILL_SCRIPTS)/generate_json_from_slides.py
	uv run python $(SKILL_SCRIPTS)/generate_html_from_json.py
	uv run python $(SKILL_SCRIPTS)/generate_index_from_portfolio.py
	uv run python $(SKILL_SCRIPTS)/convert_json_to_md.py
	uv run python $(SKILL_SCRIPTS)/print_slide_matrix.py
	@echo "✅ Portfolio regeneriert · alter Stand in public/archive/ · öffne public/index.html"

report: ## Notebook als HTML exportieren → public/report.html
	. .venv/bin/activate && jupyter nbconvert --to html --no-input --output-dir public --output report notebooks/04_insights.ipynb
	open public/report.html
	@echo "✅ Report exportiert und geöffnet."

dashboard: ## Dashboard starten (http://localhost:8501)
	uv run streamlit run apps/dashboard/app.py

precompute: ## Dashboard-Aggregationen vorberechnen (einmalig nach neuen Daten)
	uv run python apps/dashboard/precompute.py

deploy-pages: ## GitHub Pages Setup (one-time configuration)
	@echo "✓ GitHub Pages Setup (one-time):"
	@echo ""
	@echo "  1. Go to Repo Settings → Pages"
	@echo "  2. Under 'Build and deployment':"
	@echo "     • Source: Deploy from a branch"
	@echo "     • Branch: main"
	@echo "     • Folder: /public"
	@echo "  3. Click Save"
	@echo "  4. GitHub deploys automatically on every push to main"
	@echo ""
	@echo "  URLs will be:"
	@echo "  • Main: https://kaywiegand.github.io/zh-tram-flow/"
	@echo "  • Report: https://kaywiegand.github.io/zh-tram-flow/report.html"
	@echo "  • Presentation: https://kaywiegand.github.io/zh-tram-flow/presentation.html"

deploy-streamlit: ## Streamlit Cloud Setup (one-time configuration)
	@echo "✓ Streamlit Cloud Setup (one-time):"
	@echo ""
	@echo "  Prerequisites:"
	@echo "  • Run 'make precompute' locally once"
	@echo "  • Commit apps/dashboard/data/*.parquet to git"
	@echo ""
	@echo "  Steps:"
	@echo "  1. Go to https://share.streamlit.io"
	@echo "  2. Sign in with GitHub"
	@echo "  3. Click 'New app'"
	@echo "  4. Repository: kaywiegand/zh-tram-flow"
	@echo "  5. Branch: main"
	@echo "  6. File: apps/dashboard/app.py"
	@echo "  7. Click Deploy"
	@echo ""
	@echo "  Your dashboard will be live at: https://zh-tram-flow.streamlit.app"

help: ## Alle verfügbaren Targets anzeigen
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'
