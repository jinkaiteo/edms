#!/bin/bash
# CI/CD Container Entrypoint Script

set -e

echo "========================================="
echo "EDMS CI/CD Runner"
echo "========================================="
echo ""

# Display environment
echo "Environment:"
echo "  CI: ${CI:-false}"
echo "  Workspace: ${WORKSPACE:-/workspace}"
echo "  User: $(whoami)"
echo ""

# Execute command
exec "$@"
