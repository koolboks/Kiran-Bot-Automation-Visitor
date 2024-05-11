#!/bin/bash

# Create a new virtual environment
python -m venv myenv

# Activate the virtual environment in Bash (Windows)
source myenv/Scripts/activate



# Install Python dependencies
pip install -r requirements.txt

# Install playwright
pip install playwright

# Install browser binaries
playwright install

# Run the executable
#./main.exe

# Run the main Script instead
python -m main
