#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════
#  Connexify License Server – Google Cloud deployment script
#  Account: ponderingprotocols@gmail.com
#
#  Prerequisites:
#    1. gcloud CLI installed  (https://cloud.google.com/sdk/docs/install)
#    2. Logged in:  gcloud auth login ponderingprotocols@gmail.com
#    3. Docker installed (or use Cloud Build)
# ═══════════════════════════════════════════════════════════════════
set -euo pipefail

# ── Configuration ─────────────────────────────────────────────────
PROJECT_ID="${GCP_PROJECT_ID:-connexify-license}"
REGION="${GCP_REGION:-africa-south1}"          # Johannesburg (closest to SA)
SERVICE_NAME="connexify-server"
BUCKET_NAME="${GCS_BUCKET:-connexify-license-data}"
IMAGE="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

# Secrets – set these as env vars before running, or they'll use defaults
ADMIN_TOKEN="${ADMIN_SECRET_TOKEN:-connexify-admin-2026}"
SMTP_PASSWORD="${SMTP_PASSWORD:-}"
PAYFAST_KEY="${PAYFAST_MERCHANT_KEY:-4xkai7s4ataw7}"
PAYFAST_PASSPHRASE="${PAYFAST_PASSPHRASE:-159951Bashier}"

echo "═══════════════════════════════════════════════════════════"
echo "  Connexify License Server – GCP Deployment"
echo "  Project:  ${PROJECT_ID}"
echo "  Region:   ${REGION}"
echo "  Service:  ${SERVICE_NAME}"
echo "  Bucket:   ${BUCKET_NAME}"
echo "═══════════════════════════════════════════════════════════"

# ── Step 1: Ensure project and enable APIs ────────────────────────
echo ""
echo "[1/6] Setting project and enabling APIs..."
gcloud config set project "${PROJECT_ID}" 2>/dev/null || true
gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com \
  storage.googleapis.com \
  --quiet

# ── Step 2: Create GCS bucket (if not exists) ────────────────────
echo ""
echo "[2/6] Creating GCS bucket: gs://${BUCKET_NAME} ..."
if gsutil ls -b "gs://${BUCKET_NAME}" 2>/dev/null; then
  echo "  Bucket already exists."
else
  gsutil mb -p "${PROJECT_ID}" -l "${REGION}" -b on "gs://${BUCKET_NAME}"
  echo "  Bucket created."
fi

# ── Step 3: Verify GCS data ─────────────────────────────────
echo ""
echo "[3/6] Data check..."
echo "  To upload existing data to GCS:"
echo "    gsutil cp license_database.json gs://${BUCKET_NAME}/data/license_database.json"
echo "    gsutil cp portal_users.json     gs://${BUCKET_NAME}/data/portal_users.json"
echo "  (skipping – run manually if needed)"

# ── Step 4: Build container image ─────────────────────────────────
echo ""
echo "[4/6] Building container image with Cloud Build..."
cd "$(dirname "$0")"
gcloud builds submit --tag "${IMAGE}" .

# ── Step 5: Deploy to Cloud Run ──────────────────────────────────
echo ""
echo "[5/6] Deploying to Cloud Run..."
gcloud run deploy "${SERVICE_NAME}" \
  --image "${IMAGE}" \
  --region "${REGION}" \
  --platform managed \
  --allow-unauthenticated \
  --memory 512Mi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 3 \
  --timeout 300 \
  --set-env-vars "\
GCS_BUCKET=${BUCKET_NAME},\
ADMIN_SECRET_TOKEN=${ADMIN_TOKEN},\
CONNEXA_VERSION=5.2.8,\
SMTP_HOST=mail.connexify.co.za,\
SMTP_PORT=587,\
SMTP_USER=admin@connexify.co.za,\
SMTP_PASSWORD=${SMTP_PASSWORD},\
FROM_EMAIL=admin@connexify.co.za,\
FROM_NAME=Connexify,\
COMPANY_NAME=Connexify,\
SUPPORT_EMAIL=admin@connexify.co.za,\
PAYFAST_MERCHANT_ID=27484481,\
PAYFAST_MERCHANT_KEY=${PAYFAST_KEY},\
PAYFAST_PASSPHRASE=${PAYFAST_PASSPHRASE},\
SITE_URL=https://www.connexify.co.za"

# ── Step 6: Get and display the URL ──────────────────────────────
echo ""
echo "[6/6] Deployment complete!"
SERVICE_URL=$(gcloud run services describe "${SERVICE_NAME}" --region "${REGION}" --format "value(status.url)")
echo ""
echo "═══════════════════════════════════════════════════════════"
echo "  ✅  Connexify Server is live!"
echo "  URL:    ${SERVICE_URL}"
echo "  Health: ${SERVICE_URL}/api/health"
echo "  Admin:  ${SERVICE_URL}/admin"
echo ""
echo "  Next steps:"
echo "  1. Verify health: curl ${SERVICE_URL}/api/health"
echo "  2. Upload data to GCS if needed (see Step 3 above)"
echo "  3. Map custom domain:  gcloud run domain-mappings create \\"
echo "       --service ${SERVICE_NAME} --region ${REGION} --domain license.connexify.co.za"
echo "  4. Update DNS: CNAME license.connexify.co.za → ghs.googlehosted.com"
echo "═══════════════════════════════════════════════════════════"
