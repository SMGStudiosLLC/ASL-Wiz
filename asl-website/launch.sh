#!/bin/bash

# Simple launch script for ASL Practice website
# Opens the website in the default browser

echo "🚀 Launching ASL Practice..."

# Check if we're in the right directory
if [ ! -f "index.html" ]; then
    echo "❌ Error: index.html not found. Please run this script from the asl-website directory."
    exit 1
fi

# Get the current directory path
CURRENT_DIR=$(pwd)

# Open in default browser
if command -v open &> /dev/null; then
    # macOS
    open "file://$CURRENT_DIR/index.html"
elif command -v xdg-open &> /dev/null; then
    # Linux
    xdg-open "file://$CURRENT_DIR/index.html"
elif command -v start &> /dev/null; then
    # Windows
    start "file://$CURRENT_DIR/index.html"
else
    echo "📋 Please open the following URL in your browser:"
    echo "file://$CURRENT_DIR/index.html"
fi

echo "✅ ASL Practice launched successfully!"
echo "📖 Check README.md for usage instructions and features."
