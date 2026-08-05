SHELL := /bin/sh
.DEFAULT_GOAL := help

COMPOSE := podman compose --env-file .env -f compose.yml
PYTHON := .venv/bin/python

.PHONY: help setup config build start migrate schema-check seed seed-check health ps logs test lint check stop down db-shell

help: ## Afficher les commandes disponibles
	@awk 'BEGIN {FS = ":.*## "} /^[a-zA-Z_-]+:.*## / {printf "  %-12s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

setup: ## Créer la configuration locale et installer les dépendances
	python3 scripts/create_env.py
	python3 -m venv .venv
	.venv/bin/pip install --disable-pip-version-check --no-cache-dir -e './backend[dev]'
	cd frontend && npm ci --no-audit

config: .env ## Valider la configuration Compose résolue
	$(COMPOSE) config --quiet

build: config ## Construire les images de l'application
	$(COMPOSE) build

start: config ## Construire et démarrer tous les services
	$(COMPOSE) up -d --build
	$(COMPOSE) up -d --no-deps --force-recreate nginx
	python3 scripts/check_health.py

migrate: .env ## Appliquer les migrations SQL manuelles dans l'ordre
	$(COMPOSE) exec -T backend python -m scripts.migrate

schema-check: .env ## Tester les contraintes obligatoires sans conserver de données
	$(COMPOSE) exec -T backend python -m scripts.check_schema

seed: .env ## Créer 600 profils fictifs et leurs avatars privés
	$(COMPOSE) exec -T backend python -m scripts.seed

seed-check: .env ## Vérifier les profils complets et les objets MinIO du seed
	$(COMPOSE) exec -T backend python -m scripts.check_seed

health: ## Vérifier la disponibilité complète via Nginx
	python3 scripts/check_health.py

ps: .env ## Afficher l'état des services
	$(COMPOSE) ps

logs: .env ## Suivre les journaux de tous les services
	$(COMPOSE) logs --tail=100 -f

test: ## Exécuter les tests backend et frontend
	$(PYTHON) -m pytest backend
	cd frontend && npm test -- --run

lint: ## Vérifier le code backend et frontend
	.venv/bin/ruff check backend
	cd frontend && npm run lint && npm run format:check

check: lint test build ## Exécuter toutes les validations avant commit

stop: .env ## Arrêter les services sans les supprimer
	$(COMPOSE) stop

down: .env ## Supprimer les conteneurs et le réseau, conserver les volumes
	$(COMPOSE) down

db-shell: .env ## Ouvrir une console PostgreSQL locale
	$(COMPOSE) exec postgres sh -c 'PGPASSWORD="$$POSTGRES_PASSWORD" psql -U "$$POSTGRES_USER" -d "$$POSTGRES_DB"'

.env:
	@echo "Configuration absente : exécutez 'make setup'." >&2
	@exit 1
