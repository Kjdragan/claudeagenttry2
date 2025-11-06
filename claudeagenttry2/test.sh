#!/bin/bash
# Test setup script

echo "🧪 Testing Research Orchestrator Setup..."
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  Warning: .env file not found"
    echo "   Copy .env.example to .env and add your API keys"
    echo ""
fi

# Run test
uv run python test_setup.py
