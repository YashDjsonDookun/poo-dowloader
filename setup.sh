#!/bin/bash
echo "Installing Playwright browsers..."
python -m playwright install
playwright install --with-deps
echo "Playwright installation completed!"
