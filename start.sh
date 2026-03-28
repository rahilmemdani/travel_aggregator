#!/bin/bash

echo "🚀 Starting Travel Price Aggregator..."
echo ""
echo "📍 Application will be available at: http://localhost:5000"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

cd "$(dirname "$0")"
python app.py
