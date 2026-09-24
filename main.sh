#!/usr/bin/env bash
set -euo pipefail

# Force delete any cached or stuck compilation artifacts
rm -f audio_analyzer

# Compile the stable 2D explicit code matrix
gcc main.c -o audio_analyzer -lm

# FIXED: Use 'export' so getenv() inside the compiled binary can find the parameters
export INPUT_FILE="audio/pure_sweep.wav"
export OUTPUT_FILE="audio/dashboard_data.csv"

# Execute the native binary 
./audio_analyzer
