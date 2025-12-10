# Environment Configuration Restore Instructions

## CRITICAL: Environment Variables

This backup includes environment configuration files that contain sensitive information:

1. **environment_variables.env** - Main Django environment file
   - Contains SECRET_KEY (REQUIRED for Django to start)
   - Contains database credentials
   - Contains ALLOWED_HOSTS configuration

2. **Django Settings** - Django configuration files
   - Contains application configuration
   - May contain additional sensitive settings

## Restore Process

1. **Copy environment file**:
   ```bash
   cp configuration/environment_variables.env /app/.env
   ```

2. **Copy Django settings** (if needed):
   ```bash
   cp -r configuration/django_settings/* /app/edms/settings/
   ```

3. **Set proper permissions**:
   ```bash
   chmod 600 /app/.env
   chmod 644 /app/edms/settings/*.py
   ```

4. **Verify environment variables are loaded**:
   ```bash
   python manage.py check
   ```

## Security Notes

- These files contain SECRET_KEY and database passwords
- Store this backup securely
- Rotate SECRET_KEY if this backup is compromised
- Review ALLOWED_HOSTS for your target environment

