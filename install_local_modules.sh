#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

echo "Installing tryton..."
cd "$SCRIPT_DIR/tryton"
pip install .

echo "Installing trytond..."
cd "$SCRIPT_DIR/trytond"
pip install .

echo "Installing naiad..."
cd "$SCRIPT_DIR/naiad"
pip install .

echo "All local modules installed successfully." 