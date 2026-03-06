# Connexify License Server – Google Cloud Migration Guide

## Architecture

```
                 ┌──────────────┐
    Internet ───►│  Cloud Run   │◄──── Custom domain: license.connexify.co.za
                 │  (FastAPI)   │
                 └──────┬───────┘
                        │
              ┌─────────┴──────────┐
              │                    │
       ┌──────▼──────┐    ┌───────▼───────┐
       │ GCS Bucket  │    │  In-memory    │
       │ data/       │    │  (cache)      │
       │  ├ licenses │    │  LICENSE_DB   │
       │  └ users    │    │  PORTAL_USERS │
       │ static/     │    └───────────────┘
       │  ├ *.deb    │
       │  └ *.exe    │
       └─────────────┘
```

**Cloud Run** runs the FastAPI server. **GCS** provides persistent storage for JSON data and installer files. The in-memory dictionaries act as a fast cache; every mutation writes through to GCS.

## Prerequisites

1. **Google Cloud account**: `ponderingprotocols@gmail.com`
2. **gcloud CLI** installed: https://cloud.google.com/sdk/docs/install
3. **Authenticated**: `gcloud auth login ponderingprotocols@gmail.com`
4. **Project created** (first time only):
   ```bash
   gcloud projects create connexify-license --name "Connexify License Server"
   gcloud config set project connexify-license
   ```
5. **Billing enabled** on the project (Cloud Run free tier: 2M requests/month)

## Quick Deploy (PowerShell)

```powershell
cd render-license-server

# First time – full deploy:
.\deploy-gcp.ps1

# With custom parameters:
.\deploy-gcp.ps1 -ProjectId "my-project" -Region "europe-west1"

# Skip build (redeploy with same image):
.\deploy-gcp.ps1 -SkipBuild
```

## Quick Deploy (Bash)

```bash
cd render-license-server
chmod +x deploy-gcp.sh
./deploy-gcp.sh
```

## Step-by-Step Manual Deploy

### 1. Enable APIs

```bash
gcloud services enable run.googleapis.com cloudbuild.googleapis.com storage.googleapis.com
```

### 2. Create GCS Bucket

```bash
gsutil mb -p connexify-license -l africa-south1 -b on gs://connexify-license-data
```

### 3. Build & Deploy

```bash
cd render-license-server
gcloud builds submit --tag gcr.io/connexify-license/connexify-server .
gcloud run deploy connexify-server \
  --image gcr.io/connexify-license/connexify-server \
  --region africa-south1 \
  --allow-unauthenticated \
  --memory 512Mi \
  --set-env-vars "GCS_BUCKET=connexify-license-data,ADMIN_SECRET_TOKEN=connexify-admin-2026"
```

### 4. Verify

```bash
# Get the service URL
SERVICE_URL=$(gcloud run services describe connexify-server --region africa-south1 --format "value(status.url)")

# Health check
curl $SERVICE_URL/api/health
# Expected: {"status":"healthy","storage_backend":"gcs","gcs_bucket":"connexify-license-data",...}
```

## Data Migration from Render

### Automated (PowerShell)

```powershell
.\migrate-to-gcs.ps1
```

This script:
1. Calls the Render API to export licenses and portal users
2. Saves JSON files locally
3. Uploads them to `gs://connexify-license-data/data/`

### Manual

```bash
# Download from Render's persistent disk (via API)
curl "https://connexify-server.onrender.com/api/admin/licenses?admin_token=connexify-admin-2026" -o licenses.json

# Upload to GCS
gsutil cp license_database.json gs://connexify-license-data/data/license_database.json
gsutil cp portal_users.json     gs://connexify-license-data/data/portal_users.json

# Migrate installer files
gsutil cp connexa-setup.exe gs://connexify-license-data/static/connexa-setup.exe
```

## Custom Domain Setup

```bash
# Map domain to Cloud Run
gcloud run domain-mappings create \
  --service connexify-server \
  --region africa-south1 \
  --domain license.connexify.co.za

# Then update DNS:
#   CNAME  license.connexify.co.za  →  ghs.googlehosted.com
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `GCS_BUCKET` | _(empty)_ | GCS bucket name. Set to enable cloud storage |
| `ADMIN_SECRET_TOKEN` | `connexify-admin-2026` | Admin API authentication |
| `CONNEXA_VERSION` | `5.2.8` | Current app version |
| `SMTP_HOST` | `mail.connexify.co.za` | Email server |
| `SMTP_PORT` | `587` | SMTP port |
| `SMTP_USER` | `admin@connexify.co.za` | SMTP username |
| `SMTP_PASSWORD` | _(secret)_ | SMTP password |
| `PAYFAST_MERCHANT_ID` | `27484481` | PayFast merchant |
| `PAYFAST_MERCHANT_KEY` | _(secret)_ | PayFast key |
| `PAYFAST_PASSPHRASE` | _(secret)_ | PayFast passphrase |
| `SITE_URL` | `https://www.connexify.co.za` | Public site URL |

## How Storage Works

The `storage.py` module provides a transparent abstraction:

- **When `GCS_BUCKET` is set** (Cloud Run): JSON data is loaded from and saved to `gs://<bucket>/data/`. Files go to `gs://<bucket>/static/`. Local filesystem (`/tmp`) acts as a cache.
- **When `GCS_BUCKET` is empty** (Render / local dev): Uses local filesystem only. No GCS dependency needed.

This means the **same codebase** works on Render, Cloud Run, and local development without any changes.

## Cost Estimate

Cloud Run free tier (per month):
- 2 million requests
- 360,000 GB-seconds compute
- 1 GB outbound data

GCS:
- 5 GB storage free
- 5,000 Class A operations (writes)
- 50,000 Class B operations (reads)

**Expected cost: $0/month** for the current usage level (< 1000 requests/day).

## Rollback

To switch back to Render:
1. Remove `GCS_BUCKET` env var (or set it empty)
2. Push to the `bashierh/connexify-server` GitHub repo
3. Render auto-deploys from the repo

Both platforms can run simultaneously with the same codebase.
