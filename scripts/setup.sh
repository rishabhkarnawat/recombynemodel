#!/usr/bin/env bash
set -euo pipefail

# Initializes local development dependencies for Recombyne.
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r backend/requirements.txt

cd frontend
npm install
