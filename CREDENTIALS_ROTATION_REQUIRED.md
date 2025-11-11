# URGENT: Credentials Rotation Required

## Overview

This repository previously contained exposed credentials in its git history. While the credentials have been removed from the current working directory and most of the git history has been cleaned, **you must rotate these credentials immediately** before making this repository public.

## Exposed Credentials

The following credentials were found in git history and must be rotated:

### 1. Neon PostgreSQL Database

**Exposed Information:**
- Host: `ep-cold-scene-a6mv9l89-pooler.us-west-2.aws.neon.tech`
- Database: `neondb`
- Username: `neondb_owner`
- Password: `npg_EJYSd2IA0lbp`

**Action Required:**
1. Go to https://console.neon.tech
2. Log into your account
3. Navigate to your database settings
4. Reset the password for user `neondb_owner`
5. Update your environment variables with the new password

### 2. NASA EONET API Key

**Exposed Key:** `hjp6PQBMN7kiHJf28k6EuTLIowh0AOcxPtxLkk1c`

**Action Required:**
1. Go to https://api.nasa.gov
2. Log into your account (or the account that generated this key)
3. Revoke/delete the key: `hjp6PQBMN7kiHJf28k6EuTLIowh0AOcxPtxLkk1c`
4. Generate a new API key
5. Update your environment variables with the new key

## Why This Is Critical

Even though the credentials have been removed from:
- The current working directory
- The main secrets file (`.streamlit/secrets.toml`)

They may still be accessible in git history commits. Anyone who clones the repository might be able to find these credentials by searching through old commits.

## Timeline

**ROTATE THESE CREDENTIALS BEFORE MAKING THE REPOSITORY PUBLIC**

1. Complete rotation: Before pushing to public repository
2. Verify new credentials work: Test locally with new credentials
3. Update all deployments: Update Streamlit Cloud, Hugging Face, or other deployments
4. Then proceed to make repository public

## After Rotation

Once you've rotated the credentials:

1. Update your local `.env` file with new values
2. Update Streamlit Cloud secrets (if deployed)
3. Update any other deployment configurations
4. Test the application to ensure it works with new credentials
5. Delete this file (`CREDENTIALS_ROTATION_REQUIRED.md`)

## Questions?

If you have questions about credential rotation, refer to:
- Neon Documentation: https://neon.tech/docs
- NASA API Documentation: https://api.nasa.gov/

## Security Best Practices

Going forward:
- Never commit credentials to git
- Use environment variables or secrets management
- Regularly rotate credentials
- Enable 2FA on service accounts
- Monitor access logs for suspicious activity
