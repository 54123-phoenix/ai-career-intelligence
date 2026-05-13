#!/bin/bash
set -e

echo "=== AI Career Intelligence System ==="
echo "Starting services..."
docker-compose up --build -d

echo "Waiting for app to be ready..."
for i in $(seq 1 12); do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo ""
        echo "App is ready: http://localhost:8000"
        echo "API docs:     http://localhost:8000/docs"
        echo "Health check: http://localhost:8000/health"
        exit 0
    fi
    sleep 2
done

echo ""
echo "App may still be starting. Check:"
echo "  curl http://localhost:8000/health"
echo "  docker-compose logs -f"
