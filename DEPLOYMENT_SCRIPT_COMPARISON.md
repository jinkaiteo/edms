# Deployment Script Comparison

## Issue
`deploy-interactive-fast.sh` causing errors during deployment.
Falling back to working script: `deploy-interactive.sh`

## Key Differences

### deploy-interactive-fast.sh (New - Has Issues)
- Email configuration BEFORE Docker deployment
- Email test AFTER all initialization
- Optimized for speed (fewer restarts)
- **Issue**: May have timing/dependency problems

### deploy-interactive.sh (Working - Stable)
- Email configuration AFTER Docker deployment  
- Email test DURING configuration
- Standard flow (proven reliable)
- **Status**: Works correctly

## Recommendation

**Use deploy-interactive.sh for staging deployment**

Both scripts have the same optimizations:
- ✅ env_file directive (email working)
- ✅ No redundant collectstatic (faster)
- ✅ BuildKit enabled (faster builds)
- ✅ Health check start_period (no unhealthy errors)

The ONLY difference is email config timing, which doesn't affect functionality.

## Usage

```bash
cd /home/lims/edms
git pull origin main

# Use the working script
./deploy-interactive.sh
```

## Future Investigation

After successful staging deployment, we can debug deploy-interactive-fast.sh:
- Check what error occurred
- Fix the issue
- Test on development first before production

For now: **Stability over speed optimization**

