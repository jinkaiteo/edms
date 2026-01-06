#!/bin/bash

# EDMS Quick Deploy Script
# Runs the interactive deployment immediately

if [ ! -f "./deploy-interactive.sh" ]; then
    echo "Error: deploy-interactive.sh not found"
    echo "Please run this script from the deployment package directory"
    exit 1
fi

chmod +x deploy-interactive.sh
./deploy-interactive.sh
