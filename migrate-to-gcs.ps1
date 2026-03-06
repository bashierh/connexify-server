# ═══════════════════════════════════════════════════════════════════
#  Migrate data from Render → Google Cloud Storage
#  Downloads JSON data from the live Render instance and uploads
#  it to the GCS bucket so Cloud Run has all existing licenses.
# ═══════════════════════════════════════════════════════════════════

param(
    [string]$RenderUrl   = "https://connexify-server.onrender.com",
    [string]$AdminToken  = "connexify-admin-2026",
    [string]$BucketName  = "connexify-license-data",
    [string]$OutDir      = "./migration-data"
)

$ErrorActionPreference = "Stop"

Write-Host "Connexify: Render → GCS Data Migration" -ForegroundColor Cyan
Write-Host "  Source: $RenderUrl"
Write-Host "  Target: gs://$BucketName/data/"
Write-Host ""

# Create temp dir
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

# ── 1. Export licenses from Render ────────────────────────────────
Write-Host "[1/4] Fetching license database from Render..." -ForegroundColor Yellow
try {
    $licenses = Invoke-RestMethod -Uri "$RenderUrl/api/admin/list-licenses?admin_token=$AdminToken" -Method Get
    Write-Host "  Found $($licenses.total) licenses."

    # Also fetch full database dump if available
    $dbData = @{ licenses = @{}; activations = @{} }
    foreach ($lic in $licenses.licenses) {
        $key = $lic.key
        $dbData.licenses[$key] = $lic
    }

    $dbJson = $dbData | ConvertTo-Json -Depth 10
    $dbJson | Out-File -FilePath "$OutDir/license_database.json" -Encoding UTF8
    Write-Host "  Saved to $OutDir/license_database.json"
} catch {
    Write-Host "  WARNING: Could not fetch licenses: $_" -ForegroundColor Red
    Write-Host "  You may need to manually export license_database.json from Render's disk."
}

# ── 2. Export portal users ────────────────────────────────────────
Write-Host "`n[2/4] Fetching portal users from Render..." -ForegroundColor Yellow
try {
    $users = Invoke-RestMethod -Uri "$RenderUrl/api/admin/portal-users?token=$AdminToken" -Method Get
    Write-Host "  Found $($users.users.Count) portal users."

    # Build portal_users.json format (email -> user object)
    $portalData = @{}
    foreach ($u in $users.users) {
        $portalData[$u.email] = $u
    }
    $portalJson = $portalData | ConvertTo-Json -Depth 10
    $portalJson | Out-File -FilePath "$OutDir/portal_users.json" -Encoding UTF8
    Write-Host "  Saved to $OutDir/portal_users.json"
} catch {
    Write-Host "  WARNING: Could not fetch portal users: $_" -ForegroundColor Red
    Write-Host "  Portal users endpoint may not exist. Manual export needed."
}

# ── 3. Upload to GCS ─────────────────────────────────────────────
Write-Host "`n[3/4] Uploading to GCS bucket: gs://$BucketName/data/ ..." -ForegroundColor Yellow
$filesToUpload = Get-ChildItem "$OutDir/*.json" -ErrorAction SilentlyContinue
if ($filesToUpload.Count -eq 0) {
    Write-Host "  No JSON files to upload." -ForegroundColor Red
    exit 1
}
foreach ($f in $filesToUpload) {
    Write-Host "  Uploading $($f.Name)..."
    gsutil cp $f.FullName "gs://$BucketName/data/$($f.Name)"
}
Write-Host "  Upload complete."

# ── 4. List installer files on Render ─────────────────────────────
Write-Host "`n[4/4] Checking for installer files..." -ForegroundColor Yellow
try {
    $files = Invoke-RestMethod -Uri "$RenderUrl/api/admin/list-files?admin_token=$AdminToken" -Method Get
    if ($files.files.Count -gt 0) {
        Write-Host "  Found $($files.files.Count) installer files on Render:"
        foreach ($fi in $files.files) {
            Write-Host "    - $($fi.name) ($($fi.size_mb) MB)"
        }
        Write-Host ""
        Write-Host "  To migrate installer files, download them from:"
        Write-Host "    $RenderUrl/static/<filename>"
        Write-Host "  Then upload to GCS:"
        Write-Host "    gsutil cp <file> gs://$BucketName/static/<filename>"
    } else {
        Write-Host "  No installer files found."
    }
} catch {
    Write-Host "  Could not list files: $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  Migration data saved to: $OutDir/" -ForegroundColor Green
Write-Host "  Verify in GCS:  gsutil ls gs://$BucketName/data/"
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
