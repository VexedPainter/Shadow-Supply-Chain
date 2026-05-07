#!/usr/bin/env bash
# Build script for Render deployment
set -o errexit

pip install --upgrade pip
pip install -r requirements.txt

# Generate seed data if not present
python generate_data.py
