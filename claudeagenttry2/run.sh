#!/bin/bash
# Quick launcher for Research Orchestrator

echo "🚀 Launching Research Orchestrator..."
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  Warning: .env file not found"
    echo "   Copy .env.example to .env and add your API keys"
    echo ""
fi

# Activate UV environment and run
uv run streamlit run app.py
