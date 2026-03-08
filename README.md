# Connexify License Server + Website (Google Cloud Run)

Combined service deployed on **Google Cloud Run** (GCP):
- **Connexify company website** at `/` (landing page, features, pricing, downloads)
- **License API** at `/api/validate`, `/api/activate`, `/api/admin/*`
- **Static file downloads** for DEB and EXE installers at `/static/`
- **Social media management** at `/admin` (Twitter, LinkedIn, Facebook OAuth 2.0)

## Quick Deploy

### PowerShell (Windows)

```powershell
cd render-license-server
.\deploy-gcp.ps1
```

### Bash (Linux / macOS)

```bash
cd render-license-server
chmod +x deploy-gcp.sh
./deploy-gcp.sh
```

### Prerequisites

1. **Google Cloud account**: `ponderingprotocols@gmail.com`
2. **gcloud CLI** installed: https://cloud.google.com/sdk/docs/install
3. **Authenticated**: `gcloud auth login ponderingprotocols@gmail.com`
4. **Project**: `connexify-license` (region: `africa-south1` — Johannesburg)

### Environment Variables (set in Cloud Run)

| Variable | Value |
|----------|-------|
| `GCS_BUCKET` | `connexify-license-data` |
| `ADMIN_SECRET_TOKEN` | A strong secret for admin API access |
| `SMTP_HOST` | `mail.connexify.co.za` |
| `SMTP_PORT` | `587` |
| `SMTP_USER` | `admin@connexify.co.za` |
| `SMTP_PASSWORD` | SMTP password |
| `FROM_EMAIL` | `admin@connexify.co.za` |
| `FROM_NAME` | `Connexify` |
| `SITE_URL` | `https://www.connexify.co.za` |
| `PAYFAST_MERCHANT_ID` | PayFast merchant ID |
| `PAYFAST_MERCHANT_KEY` | PayFast key |

Your site will be live at: `https://www.connexify.co.za`

## Upload Installer Files

Installer files are too large for GitHub (>100MB each). Upload them after deployment:

```bash
# Upload DEB installer
curl -X POST https://www.connexify.co.za/api/admin/upload-installer \
  -F "admin_token=YOUR_TOKEN" \
  -F "file=@native-app/dist/connexa_5.2.8_amd64.deb"

# Upload EXE installer
curl -X POST https://www.connexify.co.za/api/admin/upload-installer \
  -F "admin_token=YOUR_TOKEN" \
  -F "file=@native-app/dist/Connexa-Setup-5.2.8.exe"

# Verify uploads
curl "https://www.connexify.co.za/api/admin/list-files?admin_token=YOUR_TOKEN"
```

Files are stored in GCS bucket `connexify-license-data`. Download URLs:
- `https://www.connexify.co.za/static/connexa_5.2.8_amd64.deb`
- `https://www.connexify.co.za/static/Connexa-Setup-5.2.8.exe`

## Admin API Examples

```bash
# Create a license
curl -X POST https://www.connexify.co.za/api/admin/create-license \
  -H "Content-Type: application/json" \
  -d '{"admin_token":"YOUR_TOKEN","duration_days":365,"customer_email":"client@example.com"}'

# List all licenses
curl "https://www.connexify.co.za/api/admin/list-licenses?admin_token=YOUR_TOKEN"

# Delete a license
curl -X POST https://www.connexify.co.za/api/admin/delete-license \
  -H "Content-Type: application/json" \
  -d '{"admin_token":"YOUR_TOKEN","license_key":"XXXXX-XXXXX-XXXXX-XXXXX-XXXXX"}'
```

## Local Development

```bash
pip install -r requirements.txt
python main.py
# Open http://localhost:8002
```

## How Storage Works

The `storage.py` module provides a transparent abstraction:

- **When `GCS_BUCKET` is set** (Cloud Run): JSON data is stored in `gs://<bucket>/data/`. Installer files go to `gs://<bucket>/static/`. Local `/tmp` acts as a cache.
- **When `GCS_BUCKET` is empty** (local dev): Uses local filesystem only. No GCS dependency needed.

## Cost Estimate

Cloud Run free tier (per month):
- 2 million requests
- 360,000 GB-seconds compute
- 1 GB outbound data

GCS free tier:
- 5 GB storage
- 5,000 Class A operations (writes)
- 50,000 Class B operations (reads)

**Expected cost: $0/month** for current usage levels.

## Important Notes

- Cloud Run scales to zero when idle — first request after idle takes ~2-3s (cold start)
- License data persists in GCS bucket `connexify-license-data`
- SMTP: Uses `mail.connexify.co.za` on port 587 with STARTTLS
- Custom domain mapped via `gcloud run domain-mappings`
