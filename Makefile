.PHONY: help start stop restart logs test clean setup status

help: ## Show this help message
	@echo "Tri-Duel Game - Available Commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

start: ## Start all services
	docker-compose up --build

start-bg: ## Start all services in background
	docker-compose up -d --build

stop: ## Stop all services
	docker-compose down

restart: ## Restart all services
	docker-compose down
	docker-compose up --build

logs: ## Show logs (make logs-player for specific service)
	docker-compose logs -f

logs-auth: ## Show auth service logs
	docker-compose logs -f auth_service

logs-player: ## Show player service logs
	docker-compose logs -f player_service

logs-game: ## Show game service logs
	docker-compose logs -f game_service

test: ## Run all tests
	@echo "Testing Player Service..."
	cd player_service/player_service && ../../venv/bin/pytest -v

test-player: ## Run player service tests
	cd player_service/player_service && ../../venv/bin/pytest -v

test-coverage: ## Run tests with coverage
	cd player_service/player_service && ../../venv/bin/pytest -v --cov=app --cov-report=term-missing

clean: ## Clean up containers, volumes, and cache
	docker-compose down -v
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -name "*.db" -delete 2>/dev/null || true
	@echo "✅ Cleanup complete!"

setup: ## Setup development environment
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "✅ Created .env file"; \
	fi
	@if [ ! -d venv ]; then \
		python3 -m venv venv; \
		./venv/bin/pip install --upgrade pip; \
		./venv/bin/pip install -r player_service/requirements.txt; \
		echo "✅ Virtual environment created"; \
	fi

status: ## Show service status
	docker-compose ps

health: ## Check all service health endpoints
	@echo "Checking service health..."
	@curl -s http://localhost:8001/health | jq . || echo "❌ Auth service not available"
	@curl -s http://localhost:8002/health | jq . || echo "❌ Player service not available"
	@curl -s http://localhost:8003/ | jq . || echo "❌ Game service not available"

build: ## Build Docker images
	docker-compose build

rebuild: ## Rebuild Docker images from scratch
	docker-compose build --no-cache
