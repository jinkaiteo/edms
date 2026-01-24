#!/bin/bash
# Quick test to verify Dockerfile has collectstatic

echo "Quick Verification: Checking Dockerfile has collectstatic..."
echo ""

if grep -q "collectstatic" infrastructure/containers/Dockerfile.backend.prod; then
    echo "✓ Dockerfile.backend.prod contains collectstatic command"
    echo ""
    echo "Found:"
    grep -n "collectstatic" infrastructure/containers/Dockerfile.backend.prod
    echo ""
else
    echo "✗ ERROR: Dockerfile.backend.prod is missing collectstatic!"
    echo "  Static files won't be baked into image!"
    exit 1
fi

echo "Checking docker-compose.prod.yml does NOT have collectstatic in startup..."
if grep "collectstatic" docker-compose.prod.yml | grep -q "command:"; then
    echo "✗ ERROR: docker-compose.prod.yml still has collectstatic in command"
    echo "  Optimization not applied!"
    exit 1
else
    echo "✓ docker-compose.prod.yml does not run collectstatic on startup"
    echo ""
fi

echo "Checking deployment scripts..."
if grep -q "collectstatic --noinput" deploy-interactive-fast.sh; then
    echo "✗ ERROR: deploy-interactive-fast.sh still has collectstatic"
    exit 1
else
    echo "✓ deploy-interactive-fast.sh does not run collectstatic"
fi

if grep -q "collectstatic --noinput" deploy-interactive.sh; then
    echo "✗ ERROR: deploy-interactive.sh still has collectstatic"
    exit 1
else
    echo "✓ deploy-interactive.sh does not run collectstatic"
fi

echo ""
echo "════════════════════════════════════════════════════════"
echo "✓ All quick checks passed!"
echo ""
echo "Summary:"
echo "  • Dockerfile has collectstatic (bakes into image): ✓"
echo "  • docker-compose startup skips collectstatic: ✓"
echo "  • Deployment scripts skip collectstatic: ✓"
echo ""
echo "Optimization is correctly implemented."
echo ""
echo "Next steps:"
echo "  1. Commit changes: git add . && git commit"
echo "  2. Push to staging: git push origin main"
echo "  3. On staging: ./test_optimized_deployment.sh"
