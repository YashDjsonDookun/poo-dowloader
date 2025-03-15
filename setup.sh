#!/bin/bash
echo "Installing Playwright browsers..."
playwright install
python -m playwright install
playwright install --with-deps
echo "Playwright installation completed!"
