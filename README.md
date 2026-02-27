# Connexify License Server + Website (Render Deployment)

Combined service that runs on [Render.com](https://render.com) free tier:
- **Connexify company website** at `/` (landing page, features, pricing, downloads)
- **License API** at `/api/validate`, `/api/activate`, `/api/admin/*`
- **Static file downloads** for DEB and EXE installers at `/static/`

## Quick Deploy to Render

### 1. Create a GitHub repo for this folder

```bash
cd render-license-server
git init
git add .
git commit -m "Connexify license server + website"
git remote add origin https://github.com/YOUR_USERNAME/connexify-server.git
git push -u origin main
```

### 2. Deploy on Render

1. Go to [render.com](https://render.com) and sign up (free)
2. Click **New** → **Web Service**
3. Connect your GitHub repo
4. Render will auto-detect the `render.yaml` — confirm the settings
5. Set **Environment Variables** (click "Environment" tab):

| Variable | Value |
|----------|-------|
| `ADMIN_SECRET_TOKEN` | A strong secret for admin API access |
| `SMTP_USER` | Your Gmail address (for license emails) |
| `SMTP_PASSWORD` | Gmail App Password (not your regular password) |
| `FROM_EMAIL` | Your sending email address |

6. Click **Create Web Service**

Your site will be live at: `https://connexify.co.za`

### 3. Upload installer files

Installer files are too large for GitHub (>100MB each). Upload them after deployment using the admin API:

```bash
# Upload DEB installer
curl -X POST https://license-connexify.co.za/api/admin/upload-installer \
  -F "admin_token=YOUR_TOKEN" \
  -F "file=@native-app/dist/connexa_5.2.8_amd64.deb"

# Upload EXE installer
curl -X POST https://license-connexify.co.za/api/admin/upload-installer \
  -F "admin_token=YOUR_TOKEN" \
  -F "file=@native-app/dist/Connexa-Setup-5.2.8.exe"

# Verify uploads
curl "https://license-connexify.co.za/api/admin/list-files?admin_token=YOUR_TOKEN"
```

Files are stored on Render's persistent disk (1GB). Download URLs:
- `https://license-connexify.co.za/static/connexa_5.2.8_amd64.deb`
- `https://license-connexify.co.za/static/Connexa-Setup-5.2.8.exe`

### 4. Update the license server URL in the app

In `electron/license.cjs`, change:
```javascript
this.serverUrl = process.env.LICENSE_SERVER_URL || 'https://connexify.co.za';
```

## Admin API Examples

```bash
# Create a license
curl -X POST https://connexify.co.za/api/admin/create-license \
  -H "Content-Type: application/json" \
  -d '{"admin_token":"YOUR_TOKEN","duration_days":365,"customer_email":"client@example.com"}'

# List all licenses
curl "https://connexify.co.za/api/admin/list-licenses?admin_token=YOUR_TOKEN"

# Delete a license
curl -X POST https://connexify.co.za/api/admin/delete-license \
  -H "Content-Type: application/json" \
  -d '{"admin_token":"YOUR_TOKEN","license_key":"XXXXX-XXXXX-XXXXX-XXXXX-XXXXX"}'
```

## Local Development

```bash
pip install -r requirements.txt
python main.py
# Open http://localhost:8002
```

## Important Notes

- Render free tier spins down after 15 minutes of inactivity (first request after idle takes ~30s)
- License data persists on Render's disk mount at `/opt/render/project/data/`
- The disk is included in the `render.yaml` configuration (1GB)
- SMTP: Use a Gmail App Password (Google Account → Security → App Passwords)
