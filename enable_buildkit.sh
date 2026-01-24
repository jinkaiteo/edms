#!/bin/bash
# Enable BuildKit permanently for Docker

echo "═══════════════════════════════════════════════════════════════"
echo "  Enable Docker BuildKit Globally"
echo "═══════════════════════════════════════════════════════════════"
echo ""

echo "BuildKit provides:"
echo "  • Better caching (faster incremental builds)"
echo "  • Parallel layer builds"
echo "  • Advanced build features"
echo "  • No configuration changes needed"
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Docker first."
    exit 1
fi

echo "Current BuildKit status:"
docker version --format '{{.Server.Experimental}}' 2>/dev/null || echo "Unknown"
echo ""

# Enable globally in Docker daemon config
DOCKER_CONFIG="/etc/docker/daemon.json"

if [ -f "$DOCKER_CONFIG" ]; then
    echo "✓ Found existing Docker daemon config"
    if grep -q '"features"' "$DOCKER_CONFIG"; then
        echo "  BuildKit settings already present"
    else
        echo "  Adding BuildKit to config..."
        # Backup existing config
        sudo cp "$DOCKER_CONFIG" "$DOCKER_CONFIG.backup"
        # Add buildkit feature
        sudo jq '. + {"features": {"buildkit": true}}' "$DOCKER_CONFIG" > /tmp/daemon.json
        sudo mv /tmp/daemon.json "$DOCKER_CONFIG"
        echo "  ✓ Config updated"
    fi
else
    echo "Creating new Docker daemon config..."
    echo '{
  "features": {
    "buildkit": true
  }
}' | sudo tee "$DOCKER_CONFIG" > /dev/null
    echo "✓ Config created"
fi

# Enable in user environment
echo ""
echo "Adding to user environment (~/.bashrc)..."

if grep -q "DOCKER_BUILDKIT" ~/.bashrc 2>/dev/null; then
    echo "  Already in ~/.bashrc"
else
    echo "" >> ~/.bashrc
    echo "# Enable Docker BuildKit" >> ~/.bashrc
    echo "export DOCKER_BUILDKIT=1" >> ~/.bashrc
    echo "export COMPOSE_DOCKER_CLI_BUILD=1" >> ~/.bashrc
    echo "  ✓ Added to ~/.bashrc"
fi

# Enable for current session
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "✓ BuildKit enabled!"
echo ""
echo "Changes made:"
echo "  • Docker daemon config: $DOCKER_CONFIG"
echo "  • User environment: ~/.bashrc"
echo "  • Current session: active"
echo ""
echo "Next steps:"
echo "  1. Restart Docker daemon: sudo systemctl restart docker"
echo "  2. Reload shell: source ~/.bashrc"
echo "  3. Verify: docker buildx version"
echo ""
echo "No code changes needed - existing scripts will use BuildKit!"
echo "═══════════════════════════════════════════════════════════════"
