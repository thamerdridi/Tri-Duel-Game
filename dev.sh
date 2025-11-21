#!/bin/bash

# Tri-Duel Development Helper Script

set -e

echo "🎮 Tri-Duel Game Services Management"
echo "===================================="
echo ""

case "$1" in
  start)
    echo "🚀 Starting all services..."
    docker-compose up --build
    ;;
    
  start-bg)
    echo "🚀 Starting all services in background..."
    docker-compose up -d --build
    ;;
    
  stop)
    echo "🛑 Stopping all services..."
    docker-compose down
    ;;
    
  restart)
    echo "🔄 Restarting all services..."
    docker-compose down
    docker-compose up --build
    ;;
    
  logs)
    echo "📋 Showing logs..."
    docker-compose logs -f "${2:-}"
    ;;
    
  test)
    echo "🧪 Running tests..."
    if [ -z "$2" ]; then
      echo "Testing all services..."
      echo ""
      echo "=== Player Service Tests ==="
      cd player_service/player_service && ../../venv/bin/pytest -v
      cd ../..
      echo ""
      echo "✅ All tests completed!"
    elif [ "$2" = "player" ]; then
      echo "Testing Player Service..."
      cd player_service/player_service && ../../venv/bin/pytest -v
    elif [ "$2" = "auth" ]; then
      echo "Testing Auth Service..."
      cd auth_service && pytest -v
    elif [ "$2" = "game" ]; then
      echo "Testing Game Service..."
      cd game_service && pytest -v
    fi
    ;;
    
  clean)
    echo "🧹 Cleaning up..."
    docker-compose down -v
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name "*.pyc" -delete 2>/dev/null || true
    find . -name "*.db" -delete 2>/dev/null || true
    echo "✅ Cleanup complete!"
    ;;
    
  setup)
    echo "🔧 Setting up development environment..."
    
    # Copy env example if .env doesn't exist
    if [ ! -f .env ]; then
      cp .env.example .env
      echo "✅ Created .env file from .env.example"
      echo "⚠️  Please update .env with your configuration"
    fi
    
    # Setup Player Service venv
    if [ ! -d "venv" ]; then
      echo "Creating virtual environment..."
      python3 -m venv venv
      source venv/bin/activate
      pip install --upgrade pip
      pip install -r player_service/requirements.txt
      echo "✅ Virtual environment created"
    fi
    
    echo "✅ Setup complete!"
    ;;
    
  status)
    echo "📊 Service Status:"
    docker-compose ps
    ;;
    
  curl-test)
    echo "🔍 Testing service endpoints..."
    echo ""
    echo "Auth Service (8001):"
    curl -s http://localhost:8001/health | jq . || echo "❌ Not available"
    echo ""
    echo "Player Service (8002):"
    curl -s http://localhost:8002/health | jq . || echo "❌ Not available"
    echo ""
    echo "Game Service (8003):"
    curl -s http://localhost:8003/ | jq . || echo "❌ Not available"
    ;;
    
  help|*)
    echo "Usage: ./dev.sh [command]"
    echo ""
    echo "Commands:"
    echo "  start        Start all services"
    echo "  start-bg     Start all services in background"
    echo "  stop         Stop all services"
    echo "  restart      Restart all services"
    echo "  logs [svc]   Show logs (optional: auth|player|game)"
    echo "  test [svc]   Run tests (optional: auth|player|game)"
    echo "  clean        Clean up containers, volumes, and cache"
    echo "  setup        Setup development environment"
    echo "  status       Show service status"
    echo "  curl-test    Test all service health endpoints"
    echo "  help         Show this help message"
    echo ""
    echo "Examples:"
    echo "  ./dev.sh start              # Start all services"
    echo "  ./dev.sh logs player        # Show player service logs"
    echo "  ./dev.sh test player        # Run player service tests"
    echo "  ./dev.sh stop               # Stop everything"
    ;;
esac
