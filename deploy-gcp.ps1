# ═══════════════════════════════════════════════════════════════════
#  Connexify License Server – Google Cloud deployment (PowerShell)
#  Account: ponderingprotocols@gmail.com
#
#  Prerequisites:
#    1. gcloud CLI installed  (https://cloud.google.com/sdk/docs/install)
#    2. Logged in:  gcloud auth login ponderingprotocols@gmail.com
# ═══════════════════════════════════════════════════════════════════

param(
    [string]$ProjectId    = "connexify-license",
    [string]$Region       = "africa-south1",          # Johannesburg
    [string]$ServiceName  = "connexify-server",
    [string]$BucketName   = "connexify-license-data",
    [string]$AdminToken   = "connexify-admin-2026",
    [string]$SmtpPassword = "159951B@sh!",
    [switch]$SkipBuild    = $false
)

$ErrorActionPreference = "Stop"
$Image = "gcr.io/$ProjectId/$ServiceName"

Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  Connexify License Server – GCP Deployment"
Write-Host "  Project:  $ProjectId"
Write-Host "  Region:   $Region"
Write-Host "  Service:  $ServiceName"
Write-Host "  Bucket:   $BucketName"
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan

# ── Step 1: Set project and enable APIs ───────────────────────────
Write-Host "`n[1/6] Setting project and enabling APIs..." -ForegroundColor Yellow
gcloud config set project $ProjectId 2>$null
gcloud services enable `
    run.googleapis.com `
    cloudbuild.googleapis.com `
    artifactregistry.googleapis.com `
    storage.googleapis.com `
    --quiet

# ── Step 2: Create GCS bucket ────────────────────────────────────
Write-Host "`n[2/6] Creating GCS bucket: gs://$BucketName ..." -ForegroundColor Yellow
$bucketExists = gsutil ls -b "gs://$BucketName" 2>$null
if ($bucketExists) {
    Write-Host "  Bucket already exists."
} else {
    gsutil mb -p $ProjectId -l $Region -b on "gs://$BucketName"
    Write-Host "  Bucket created."
}

# ── Step 3: Data migration reminder ──────────────────────────────
Write-Host "`n[3/6] Data migration check..." -ForegroundColor Yellow
Write-Host "  If migrating from Render, upload existing data:"
Write-Host "    gsutil cp license_database.json gs://$BucketName/data/license_database.json"
Write-Host "    gsutil cp portal_users.json     gs://$BucketName/data/portal_users.json"

# ── Step 4: Build container image ─────────────────────────────────
if (-not $SkipBuild) {
    Write-Host "`n[4/6] Building container with Cloud Build..." -ForegroundColor Yellow
    Push-Location (Split-Path -Parent $MyInvocation.MyCommand.Definition)
    gcloud builds submit --tag $Image .
    Pop-Location
} else {
    Write-Host "`n[4/6] Skipping build (-SkipBuild flag set)." -ForegroundColor DarkGray
}

# ── Step 5: Deploy to Cloud Run ──────────────────────────────────
Write-Host "`n[5/6] Deploying to Cloud Run..." -ForegroundColor Yellow

$envVars = @(
    "GCS_BUCKET=$BucketName",
    "ADMIN_SECRET_TOKEN=$AdminToken",
    "CONNEXA_VERSION=5.2.8",
    "SMTP_HOST=mail.connexify.co.za",
    "SMTP_PORT=587",
    "SMTP_USER=admin@connexify.co.za",
    "SMTP_PASSWORD=$SmtpPassword",
    "FROM_EMAIL=admin@connexify.co.za",
    "FROM_NAME=Connexify",
    "COMPANY_NAME=Connexify",
    "SUPPORT_EMAIL=admin@connexify.co.za",
    "PAYFAST_MERCHANT_ID=27484481",
    "PAYFAST_MERCHANT_KEY=4xkai7s4ataw7",
    "PAYFAST_PASSPHRASE=159951Bashier",
    "SITE_URL=https://www.connexify.co.za"
) -join ","

gcloud run deploy $ServiceName `
    --image $Image `
    --region $Region `
    --platform managed `
    --allow-unauthenticated `
    --memory 512Mi `
    --cpu 1 `
    --min-instances 0 `
    --max-instances 3 `
    --timeout 300 `
    --set-env-vars $envVars

# ── Step 6: Show result ──────────────────────────────────────────
Write-Host "`n[6/6] Deployment complete!" -ForegroundColor Green
$serviceUrl = gcloud run services describe $ServiceName --region $Region --format "value(status.url)"

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  Connexify Server is live!" -ForegroundColor Green
Write-Host "  URL:    $serviceUrl"
Write-Host "  Health: $serviceUrl/api/health"
Write-Host "  Admin:  $serviceUrl/admin"
Write-Host ""
Write-Host "  Next steps:"
Write-Host "  1. Verify: Invoke-WebRequest $serviceUrl/api/health | Select Content"
Write-Host "  2. Map domain: gcloud run domain-mappings create --service $ServiceName --region $Region --domain license.connexify.co.za"
Write-Host "  3. Update DNS: CNAME license.connexify.co.za -> ghs.googlehosted.com"
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
