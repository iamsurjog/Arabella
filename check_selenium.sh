#!/bin/bash
# Check if ChromeDriver is installed and accessible

echo "Checking Selenium/ChromeDriver setup..."

# Check if Chrome/Chromium is installed
if command -v google-chrome &> /dev/null; then
    echo "✓ Google Chrome found: $(google-chrome --version)"
elif command -v chromium &> /dev/null; then
    echo "✓ Chromium found: $(chromium --version)"
elif command -v chromium-browser &> /dev/null; then
    echo "✓ Chromium Browser found: $(chromium-browser --version)"
else
    echo "✗ Chrome/Chromium not found"
    echo "  Install with: sudo apt-get install chromium-browser (Ubuntu/Debian)"
    echo "            or: brew install --cask google-chrome (macOS)"
    exit 1
fi

# Check if ChromeDriver is installed
if command -v chromedriver &> /dev/null; then
    echo "✓ ChromeDriver found: $(chromedriver --version)"
else
    echo "✗ ChromeDriver not found"
    echo "  Install with: sudo apt-get install chromium-chromedriver (Ubuntu/Debian)"
    echo "            or: brew install chromedriver (macOS)"
    echo "  Or download from: https://chromedriver.chromium.org/"
    exit 1
fi

echo ""
echo "✓ Selenium setup is ready!"
echo ""
echo "Note: If you get 'chromedriver not in PATH' errors, you may need to:"
echo "  1. Add chromedriver to your PATH"
echo "  2. Or install selenium-manager (included with selenium>=4.6.0)"
