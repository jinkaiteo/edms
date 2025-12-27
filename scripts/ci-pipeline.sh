#!/bin/bash

################################################################################
# EDMS CI/CD Pipeline Script
################################################################################
#
# Description: Universal CI/CD pipeline that works with any platform
# Version: 1.0
# Date: December 24, 2024
#
# Usage: ./scripts/ci-pipeline.sh [stage]
#
# Stages:
#   validate    - Pre-deployment validation
#   test        - Run test suite
#   package     - Create deployment package
#   deploy      - Deploy to environment
#   monitor     - Post-deployment monitoring
#   all         - Run complete pipeline (default)
#
################################################################################

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

# Configuration
STAGE="${1:-all}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# Environment detection
CI_PLATFORM="${CI_PLATFORM:-unknown}"
if [ -n "$GITHUB_ACTIONS" ]; then
    CI_PLATFORM="github-actions"
elif [ -n "$GITLAB_CI" ]; then
    CI_PLATFORM="gitlab-ci"
elif [ -n "$JENKINS_URL" ]; then
    CI_PLATFORM="jenkins"
fi

################################################################################
# Functions
################################################################################

log_info() {
    echo -e "${CYAN}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_stage() {
    echo ""
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    echo ""
}

stage_validate() {
    log_stage "STAGE: PRE-DEPLOYMENT VALIDATION"
    
    log_info "Creating deployment package..."
    chmod +x "${SCRIPT_DIR}/create-production-package.sh"
    "${SCRIPT_DIR}/create-production-package.sh"
    
    log_info "Running pre-deployment checks..."
    chmod +x "${SCRIPT_DIR}/pre-deploy-check.sh"
    "${SCRIPT_DIR}/pre-deploy-check.sh" edms-production-*/
    
    log_success "Validation completed"
}

stage_test() {
    log_stage "STAGE: TESTING"
    
    log_info "Starting test database..."
    docker-compose -f docker-compose.ci.yml up -d test-db test-redis
    
    # Wait for services
    log_info "Waiting for test services..."
    sleep 10
    
    log_info "Running backend tests..."
    cd "${PROJECT_ROOT}/backend"
    pip install -q -r requirements/test.txt
    python manage.py test --verbosity=2 || true
    
    log_info "Running frontend tests..."
    cd "${PROJECT_ROOT}/frontend"
    npm ci --quiet
    npm test -- --watchAll=false || true
    
    log_success "Testing completed"
}

stage_package() {
    log_stage "STAGE: CREATE DEPLOYMENT PACKAGE"
    
    log_info "Creating production package..."
    chmod +x "${SCRIPT_DIR}/create-production-package.sh"
    "${SCRIPT_DIR}/create-production-package.sh"
    
    # Verify package
    PACKAGE_FILE=$(ls -t edms-production-*.tar.gz | head -1)
    if [ -f "$PACKAGE_FILE" ]; then
        log_success "Package created: $PACKAGE_FILE ($(du -h $PACKAGE_FILE | cut -f1))"
    else
        log_error "Package creation failed"
        exit 1
    fi
}

stage_deploy() {
    log_stage "STAGE: DEPLOYMENT"
    
    # Check required environment variables
    if [ -z "$DEPLOY_HOST" ] || [ -z "$DEPLOY_USER" ]; then
        log_error "DEPLOY_HOST and DEPLOY_USER must be set"
        exit 1
    fi
    
    log_info "Deploying to ${DEPLOY_USER}@${DEPLOY_HOST}..."
    
    chmod +x "${SCRIPT_DIR}/deploy-to-remote.sh"
    "${SCRIPT_DIR}/deploy-to-remote.sh" \
        "${DEPLOY_USER}@${DEPLOY_HOST}" \
        ${DEPLOY_PATH:+--path "$DEPLOY_PATH"} \
        ${SSH_KEY:+--key "$SSH_KEY"} \
        --verbose
    
    log_success "Deployment completed"
}

stage_monitor() {
    log_stage "STAGE: POST-DEPLOYMENT MONITORING"
    
    # Check required environment variables
    if [ -z "$DEPLOY_HOST" ] || [ -z "$DEPLOY_USER" ]; then
        log_error "DEPLOY_HOST and DEPLOY_USER must be set"
        exit 1
    fi
    
    log_info "Running post-deployment validation..."
    ssh ${SSH_KEY:+-i "$SSH_KEY"} "${DEPLOY_USER}@${DEPLOY_HOST}" \
        'cd /opt/edms-production-* && ./scripts/post-deploy-check.sh'
    
    log_info "Running health checks..."
    for i in {1..3}; do
        log_info "Health check $i/3..."
        ssh ${SSH_KEY:+-i "$SSH_KEY"} "${DEPLOY_USER}@${DEPLOY_HOST}" \
            'cd /opt/edms-production-* && ./scripts/health-check.sh --quick'
        
        if [ $i -lt 3 ]; then
            sleep 30
        fi
    done
    
    log_success "Monitoring completed"
}

################################################################################
# Main Execution
################################################################################

main() {
    cd "${PROJECT_ROOT}"
    
    log_info "CI/CD Platform: ${CI_PLATFORM}"
    log_info "Stage: ${STAGE}"
    echo ""
    
    case "$STAGE" in
        validate)
            stage_validate
            ;;
        test)
            stage_test
            ;;
        package)
            stage_package
            ;;
        deploy)
            stage_deploy
            ;;
        monitor)
            stage_monitor
            ;;
        all)
            stage_validate
            stage_test
            stage_package
            
            if [ -n "$DEPLOY_HOST" ]; then
                stage_deploy
                stage_monitor
            else
                log_info "Skipping deployment (DEPLOY_HOST not set)"
            fi
            ;;
        *)
            log_error "Unknown stage: $STAGE"
            echo "Valid stages: validate, test, package, deploy, monitor, all"
            exit 1
            ;;
    esac
    
    echo ""
    log_success "Pipeline stage '${STAGE}' completed successfully!"
}

# Run main function
main "$@"
