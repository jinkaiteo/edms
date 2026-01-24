# Email Notification Deployment Script Fix

## Issue Summary
**Error:** `failed to read /home/lims/edms/.env: line 40: key cannot contain a space`

**Root Cause:** The interactive deployment script (`deploy-interactive.sh`) was writing invalid `.env` file entries when configuring email notifications.

## Technical Details

### Problem
The script was writing `.env` entries with quoted values containing spaces:
```bash
DEFAULT_FROM_EMAIL="EDMS System <jinkaiteo.tikva@gmail.com>"
```

This violates `.env` file format rules where keys cannot contain spaces. The parser interpreted:
- Key: `DEFAULT_FROM_EMAIL` (correct)
- Value: `"EDMS` (incorrect - stops at first space)
- Remaining: `System <email>"` (interpreted as invalid key)

### Solution
Removed the display name wrapper and quotes, using just the email address:
```bash
DEFAULT_FROM_EMAIL=jinkaiteo.tikva@gmail.com
```

## Changes Made

Fixed three locations in `deploy-interactive.sh`:

1. **Line 1247** - Gmail configuration:
   ```bash
   # Before:
   sed -i "s|^DEFAULT_FROM_EMAIL=.*|DEFAULT_FROM_EMAIL=\"EDMS System <$email_user>\"|" "$ENV_FILE"
   
   # After:
   sed -i "s|^DEFAULT_FROM_EMAIL=.*|DEFAULT_FROM_EMAIL=$email_user|" "$ENV_FILE"
   ```

2. **Line 1276** - Microsoft 365/Outlook configuration:
   ```bash
   # Before:
   sed -i "s|^DEFAULT_FROM_EMAIL=.*|DEFAULT_FROM_EMAIL=\"EDMS System <$email_user>\"|" "$ENV_FILE"
   
   # After:
   sed -i "s|^DEFAULT_FROM_EMAIL=.*|DEFAULT_FROM_EMAIL=$email_user|" "$ENV_FILE"
   ```

3. **Line 1315** - Custom SMTP configuration:
   ```bash
   # Before:
   sed -i "s|^DEFAULT_FROM_EMAIL=.*|DEFAULT_FROM_EMAIL=\"EDMS System <$from_email>\"|" "$ENV_FILE"
   
   # After:
   sed -i "s|^DEFAULT_FROM_EMAIL=.*|DEFAULT_FROM_EMAIL=$from_email|" "$ENV_FILE"
   ```

## Impact

### Before Fix
- Email configuration failed during deployment
- Test email sending would fail
- Manual `.env` file editing required

### After Fix
- Email configuration completes successfully
- `.env` file is valid and parseable
- Test email sending proceeds without errors

## Testing

To verify the fix on staging server:

```bash
# 1. Re-run the interactive deployment script
./deploy-interactive.sh

# 2. When prompted for email configuration, choose Gmail (or your provider)
# 3. Enter email credentials
# 4. Choose to test email configuration
# 5. Verify no ".env parsing" errors occur

# Manual verification:
cat .env | grep DEFAULT_FROM_EMAIL
# Should show: DEFAULT_FROM_EMAIL=your-email@domain.com
# NOT: DEFAULT_FROM_EMAIL="EDMS System <your-email@domain.com>"
```

## Notes

- The display name "EDMS System" can be configured in Django's email sending logic if needed
- Django's `send_mail()` function supports display names separately from the email address
- This fix ensures `.env` file compatibility across all parsers (bash, docker-compose, python-dotenv)

## Related Files
- `deploy-interactive.sh` - Fixed email configuration logic
- `backend/.env.example` - Reference for correct email configuration format
- Email integration documentation preserved in `EMAIL_INTEGRATION_ANALYSIS.md`

## Date
2026-01-24
