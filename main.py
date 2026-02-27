"""
Connexa License Server + Connexify Website
Deployed on Render.com free tier
"""

from fastapi import FastAPI, HTTPException, Request, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from pydantic import BaseModel
from datetime import datetime, timedelta
import hashlib
import secrets
import os
import json
import urllib.parse
from pathlib import Path
from typing import Optional

# ── Email service (inline, no external dependency) ──
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ── Website templates ──
from templates import WEBSITE_TEMPLATE, GET_STARTED_TEMPLATE, DOCS_TEMPLATE

app = FastAPI(title="Connexa License Server", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Configuration ──
LICENSE_DB_FILE = Path(os.getenv("LICENSE_DB_FILE", "/opt/render/project/data/license_database.json"))
# Fallback for local dev
if not LICENSE_DB_FILE.parent.exists():
    LICENSE_DB_FILE = Path("./license_database.json")

ADMIN_TOKEN = os.getenv("ADMIN_SECRET_TOKEN", "your-admin-secret-token-change-this")
CURRENT_VERSION = os.getenv("CONNEXA_VERSION", "5.2.8")
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASS = os.getenv("SMTP_PASSWORD", "")
FROM_EMAIL = os.getenv("FROM_EMAIL", SMTP_USER)
FROM_NAME = os.getenv("FROM_NAME", "Bashier Hendricks")
COMPANY_NAME = os.getenv("COMPANY_NAME", "Connexify")
SUPPORT_EMAIL = os.getenv("SUPPORT_EMAIL", "admin@connexify.co.za")

# ── PayFast configuration ──
PAYFAST_MERCHANT_ID = os.getenv("PAYFAST_MERCHANT_ID", "27484481")
PAYFAST_MERCHANT_KEY = os.getenv("PAYFAST_MERCHANT_KEY", "4xkai7s4ataw7")
PAYFAST_PASSPHRASE = os.getenv("PAYFAST_PASSPHRASE", "159951Bashier")
PAYFAST_URL = os.getenv("PAYFAST_URL", "https://www.payfast.co.za/eng/process")
SITE_URL = os.getenv("SITE_URL", "https://www.connexify.co.za")

# In-memory database
LICENSE_DATABASE = {}
ACTIVATION_DATABASE = {}


def load_database():
    global LICENSE_DATABASE, ACTIVATION_DATABASE
    if LICENSE_DB_FILE.exists():
        try:
            with open(LICENSE_DB_FILE, 'r') as f:
                data = json.load(f)
                LICENSE_DATABASE = data.get('licenses', {})
                ACTIVATION_DATABASE = data.get('activations', {})
                print(f"Loaded {len(LICENSE_DATABASE)} licenses")
        except Exception as e:
            print(f"Error loading database: {e}")


def save_database():
    try:
        LICENSE_DB_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(LICENSE_DB_FILE, 'w') as f:
            json.dump({
                'licenses': LICENSE_DATABASE,
                'activations': ACTIVATION_DATABASE
            }, f, indent=2)
    except Exception as e:
        print(f"Error saving database: {e}")


def generate_license_key() -> str:
    parts = []
    for _ in range(5):
        part = ''.join(secrets.choice('ABCDEFGHJKLMNPQRSTUVWXYZ23456789') for _ in range(5))
        parts.append(part)
    return '-'.join(parts)


def hash_hardware_id(hardware_id: str) -> str:
    return hashlib.sha256(hardware_id.encode()).hexdigest()


def send_license_email(customer_email: str, license_key: str, expires_date: str, duration_days: int):
    """Send license welcome email via SMTP"""
    if not SMTP_USER or not SMTP_PASS:
        print("Email not configured, skipping")
        return False
    
    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; background: #0f172a; color: #e2e8f0; padding: 40px; border-radius: 12px;">
        <h1 style="color: #3b82f6; text-align: center;">Welcome to Connexa</h1>
        <p style="text-align: center; color: #94a3b8;">Professional Network Management Platform</p>
        <div style="background: #1e293b; border: 1px solid #334155; border-radius: 8px; padding: 24px; margin: 24px 0; text-align: center;">
            <p style="color: #94a3b8; margin: 0 0 8px;">Your License Key</p>
            <p style="font-size: 24px; font-weight: bold; color: #22d3ee; letter-spacing: 2px; font-family: monospace; margin: 0;">{license_key}</p>
        </div>
        <p>License Duration: <strong>{duration_days} days</strong> (expires {expires_date[:10]})</p>
        <p>Download: <a href="https://www.connexify.co.za/downloads" style="color: #3b82f6;">www.connexify.co.za/downloads</a></p>
        <hr style="border: none; border-top: 1px solid #334155; margin: 24px 0;">
        <p style="font-size: 12px; color: #64748b; text-align: center;">Need help? Contact {SUPPORT_EMAIL}</p>
        <p style="font-size: 12px; color: #64748b; text-align: center;">&copy; {datetime.now().year} {COMPANY_NAME} (Pty) Ltd</p>
    </div>
    """
    
    msg = MIMEMultipart('alternative')
    msg['Subject'] = f'Welcome to Connexa - Your License Key'
    msg['From'] = f'{FROM_NAME} <{FROM_EMAIL}>'
    msg['To'] = customer_email
    msg.attach(MIMEText(html, 'html'))
    
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.sendmail(FROM_EMAIL, customer_email, msg.as_string())
    
    return True


# ── Pydantic Models ──

class LicenseValidationRequest(BaseModel):
    license_key: str
    hardware_id: str
    app_version: str
    platform: str

class LicenseActivationRequest(BaseModel):
    license_key: str
    hardware_id: str
    customer_email: str = ""

class LicenseResponse(BaseModel):
    valid: bool
    message: str
    expires: Optional[str] = None

class CreateLicenseRequest(BaseModel):
    duration_days: int = 365
    customer_email: str = ""
    admin_token: str
    is_demo: bool = False

class DeleteLicenseRequest(BaseModel):
    license_key: str
    admin_token: str

class ResendEmailRequest(BaseModel):
    license_key: str
    admin_token: str
    customer_email: str = ""

class ImportLicenseRequest(BaseModel):
    admin_token: str
    license_key: str
    expires: str
    customer_email: str = ""
    hardware_id: Optional[str] = None
    duration_days: int = 365
    is_demo: bool = False


# ── Startup ──

@app.on_event("startup")
async def startup_event():
    load_database()
    if not LICENSE_DATABASE:
        LICENSE_DATABASE['DEMO1-DEMO2-DEMO3-DEMO4-DEMO5'] = {
            'key': 'DEMO1-DEMO2-DEMO3-DEMO4-DEMO5',
            'created_at': datetime.now().isoformat(),
            'expires': (datetime.now() + timedelta(days=7)).isoformat(),
            'active': True,
            'customer_email': 'demo@example.com',
            'hardware_id': None,
            'duration_days': 7,
            'is_demo': True,
            'max_users': -1
        }
        save_database()
        print("Created demo license")


# ══════════════════════════════════════════════════════════════════
#   WEBSITE HTML (built from templates)
# ══════════════════════════════════════════════════════════════════

def _render_template(template: str) -> str:
    return (template
        .replace("__VERSION__", CURRENT_VERSION)
        .replace("__EMAIL__", SUPPORT_EMAIL)
        .replace("__YEAR__", str(datetime.now().year))
        .replace("__COMPANY__", COMPANY_NAME))

WEBSITE_HTML = _render_template(WEBSITE_TEMPLATE)
GET_STARTED_HTML = _render_template(GET_STARTED_TEMPLATE)
DOCS_HTML = _render_template(DOCS_TEMPLATE)


# ══════════════════════════════════════════════════════════════════
#   ROUTES - Website
# ══════════════════════════════════════════════════════════════════

@app.get("/", response_class=HTMLResponse)
async def homepage():
    """Connexify company website"""
    return HTMLResponse(content=WEBSITE_HTML)


@app.get("/get-started", response_class=HTMLResponse)
async def get_started_page():
    """Step-by-step get started wizard"""
    return HTMLResponse(content=GET_STARTED_HTML)


@app.get("/docs", response_class=HTMLResponse)
async def docs_page():
    """Client-friendly documentation"""
    return HTMLResponse(content=DOCS_HTML)


class ContactFormRequest(BaseModel):
    name: str
    email: str
    company: str = ""
    subject: str = "General Inquiry"
    message: str


@app.post("/api/contact")
async def submit_contact_form(request: ContactFormRequest):
    """Handle contact form submissions"""
    if SMTP_USER and SMTP_PASS:
        try:
            msg = MIMEMultipart()
            msg['Subject'] = f'Connexify Contact: {request.subject}'
            msg['From'] = f'{FROM_NAME} <{FROM_EMAIL}>'
            msg['To'] = SUPPORT_EMAIL
            msg['Reply-To'] = request.email
            body = f"Name: {request.name}\nEmail: {request.email}\nCompany: {request.company}\nSubject: {request.subject}\n\nMessage:\n{request.message}"
            msg.attach(MIMEText(body, 'plain'))
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
                server.starttls()
                server.login(SMTP_USER, SMTP_PASS)
                server.sendmail(FROM_EMAIL, SUPPORT_EMAIL, msg.as_string())
        except Exception as e:
            print(f"Contact form email error: {e}")
    return {"success": True, "message": "Thank you! We'll get back to you within 24 hours."}


# ══════════════════════════════════════════════════════════════════
#   ROUTES - PayFast Payment Integration
# ══════════════════════════════════════════════════════════════════

def generate_payfast_signature(data: dict) -> str:
    """Generate PayFast MD5 signature from payment data."""
    # Build param string in exact order
    pf_string = "&".join(f"{k}={urllib.parse.quote_plus(str(v).strip())}" for k, v in data.items() if v)
    if PAYFAST_PASSPHRASE:
        pf_string += f"&passphrase={urllib.parse.quote_plus(PAYFAST_PASSPHRASE.strip())}"
    return hashlib.md5(pf_string.encode()).hexdigest()


class PayFastCheckoutRequest(BaseModel):
    name: str
    email: str
    company: str = ""
    plan: str = "professional"


@app.post("/api/payfast/checkout")
async def payfast_checkout(request: PayFastCheckoutRequest):
    """Generate PayFast payment URL and redirect data."""
    if request.plan != "professional":
        raise HTTPException(status_code=400, detail="Only professional plan supports online payment")

    # Unique payment ID for tracking
    payment_id = secrets.token_hex(8)

    # Build PayFast data dict (ORDER MATTERS for signature)
    data = {
        "merchant_id": PAYFAST_MERCHANT_ID,
        "merchant_key": PAYFAST_MERCHANT_KEY,
        "return_url": f"{SITE_URL}/api/payfast/return?payment_id={payment_id}",
        "cancel_url": f"{SITE_URL}/api/payfast/cancel",
        "notify_url": f"{SITE_URL}/api/payfast/notify",
        "name_first": request.name.split()[0] if request.name else "",
        "name_last": " ".join(request.name.split()[1:]) if len(request.name.split()) > 1 else "",
        "email_address": request.email,
        "m_payment_id": payment_id,
        "amount": "500.00",
        "item_name": "Connexa Professional License - 1 Year",
        "item_description": "Unlimited devices, all features, priority support",
        "custom_str1": request.email,
        "custom_str2": request.company,
        "custom_str3": request.plan,
    }

    # Generate signature
    signature = generate_payfast_signature(data)
    data["signature"] = signature

    # Build the full redirect URL
    query_string = "&".join(f"{k}={urllib.parse.quote_plus(str(v))}" for k, v in data.items())
    redirect_url = f"{PAYFAST_URL}?{query_string}"

    return {"redirect_url": redirect_url, "payment_id": payment_id}


@app.post("/api/payfast/notify")
async def payfast_notify(request: Request):
    """PayFast ITN (Instant Transaction Notification) callback.
    Automatically creates and emails license on successful payment."""
    form_data = await request.form()
    data = dict(form_data)

    print(f"[PayFast ITN] Received: {json.dumps({k: v for k, v in data.items() if k != 'signature'}, default=str)}")

    payment_status = data.get("payment_status", "")
    pf_payment_id = data.get("pf_payment_id", "")
    m_payment_id = data.get("m_payment_id", "")
    amount_gross = data.get("amount_gross", "0")
    customer_email = data.get("custom_str1", data.get("email_address", ""))
    company = data.get("custom_str2", "")
    name_first = data.get("name_first", "")
    name_last = data.get("name_last", "")

    if payment_status == "COMPLETE":
        # Payment successful — generate license
        license_key = generate_license_key()
        expires = datetime.now() + timedelta(days=365)

        LICENSE_DATABASE[license_key] = {
            'key': license_key,
            'created_at': datetime.now().isoformat(),
            'expires': expires.isoformat(),
            'active': True,
            'customer_email': customer_email,
            'hardware_id': None,
            'duration_days': 365,
            'is_demo': False,
            'max_users': 1,
            'payment': {
                'method': 'payfast',
                'pf_payment_id': pf_payment_id,
                'm_payment_id': m_payment_id,
                'amount': amount_gross,
                'customer_name': f"{name_first} {name_last}".strip(),
                'company': company,
                'completed_at': datetime.now().isoformat()
            }
        }
        save_database()
        print(f"[PayFast ITN] License created: {license_key} for {customer_email}")

        # Send license email
        if SMTP_USER and customer_email:
            try:
                send_license_email(customer_email, license_key, expires.isoformat(), 365)
                print(f"[PayFast ITN] License email sent to {customer_email}")
            except Exception as e:
                print(f"[PayFast ITN] Email error: {e}")

    elif payment_status == "CANCELLED":
        print(f"[PayFast ITN] Payment cancelled: {m_payment_id}")
    else:
        print(f"[PayFast ITN] Status: {payment_status} for {m_payment_id}")

    return {"status": "ok"}


@app.get("/api/payfast/return", response_class=HTMLResponse)
async def payfast_return(payment_id: str = ""):
    """Success page after PayFast payment."""
    html = f"""<!DOCTYPE html><html lang="en"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Payment Successful - {COMPANY_NAME}</title>
<script src="https://cdn.tailwindcss.com"></script>
<style>body{{background:#0a0a0f;font-family:'Inter',system-ui,sans-serif}}</style>
</head><body class="min-h-screen flex items-center justify-center p-4">
<div class="max-w-md w-full bg-gray-900/60 border border-green-500/20 rounded-2xl p-10 text-center">
<div class="w-20 h-20 bg-green-500/10 rounded-full flex items-center justify-center mx-auto mb-6">
<span class="text-5xl">&#10003;</span>
</div>
<h1 class="text-2xl font-bold text-white mb-3">Payment Successful!</h1>
<p class="text-gray-400 mb-6">Thank you for purchasing Connexa Professional. Your license key has been generated and emailed to you.</p>
<div class="bg-gray-800/50 rounded-lg p-4 mb-6">
<p class="text-sm text-gray-500 mb-1">Payment Reference</p>
<p class="text-white font-mono text-sm">{payment_id}</p>
</div>
<p class="text-gray-500 text-sm mb-6">Check your email inbox (and spam folder) for your license key and activation instructions.</p>
<div class="space-y-3">
<a href="/get-started" class="block w-full py-3 rounded-lg bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium transition no-underline">Download &amp; Activate</a>
<a href="/" class="block w-full py-3 rounded-lg border border-gray-700 text-gray-400 hover:text-white text-sm transition no-underline">Return to Homepage</a>
</div></div></body></html>"""
    return html


@app.get("/api/payfast/cancel", response_class=HTMLResponse)
async def payfast_cancel():
    """Page shown when user cancels PayFast payment."""
    html = f"""<!DOCTYPE html><html lang="en"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Payment Cancelled - {COMPANY_NAME}</title>
<script src="https://cdn.tailwindcss.com"></script>
<style>body{{background:#0a0a0f;font-family:'Inter',system-ui,sans-serif}}</style>
</head><body class="min-h-screen flex items-center justify-center p-4">
<div class="max-w-md w-full bg-gray-900/60 border border-yellow-500/20 rounded-2xl p-10 text-center">
<div class="w-20 h-20 bg-yellow-500/10 rounded-full flex items-center justify-center mx-auto mb-6">
<span class="text-5xl">&#9888;</span>
</div>
<h1 class="text-2xl font-bold text-white mb-3">Payment Cancelled</h1>
<p class="text-gray-400 mb-6">Your payment was not completed. No charges have been made. You can try again anytime.</p>
<div class="space-y-3">
<a href="/get-started?plan=professional" class="block w-full py-3 rounded-lg bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium transition no-underline">Try Again</a>
<a href="/" class="block w-full py-3 rounded-lg border border-gray-700 text-gray-400 hover:text-white text-sm transition no-underline">Return to Homepage</a>
</div></div></body></html>"""
    return html


@app.get("/health")
async def health_check():
    return {"service": "Connexa License Server", "status": "running", "version": "1.0.0", "licenses": len(LICENSE_DATABASE)}


# Serve static files for downloads (DEB / EXE)
STATIC_DIR = Path(__file__).parent / "static"
STATIC_DIR.mkdir(exist_ok=True)

from fastapi.staticfiles import StaticFiles
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


# ══════════════════════════════════════════════════════════════════
#   ROUTES - License API
# ══════════════════════════════════════════════════════════════════

@app.post("/api/validate", response_model=LicenseResponse)
async def validate_license(request: LicenseValidationRequest):
    license_key = request.license_key
    hardware_id_hash = hash_hardware_id(request.hardware_id)
    
    if license_key not in LICENSE_DATABASE:
        return LicenseResponse(valid=False, message="Invalid license key")
    
    lic = LICENSE_DATABASE[license_key]
    
    if not lic.get('active', False):
        return LicenseResponse(valid=False, message="License has been deactivated")
    
    expires = datetime.fromisoformat(lic['expires'])
    if datetime.now() > expires:
        return LicenseResponse(valid=False, message="License has expired")
    
    bound = lic.get('hardware_id')
    if bound and bound != hardware_id_hash:
        return LicenseResponse(valid=False, message="License is bound to different hardware")
    
    if not bound:
        lic['hardware_id'] = hardware_id_hash
        lic['first_activation'] = datetime.now().isoformat()
        save_database()
    
    lic['last_validated'] = datetime.now().isoformat()
    save_database()
    
    return LicenseResponse(valid=True, message="License is valid", expires=lic['expires'])


@app.post("/api/activate", response_model=LicenseResponse)
async def activate_license(request: LicenseActivationRequest):
    val_req = LicenseValidationRequest(
        license_key=request.license_key,
        hardware_id=request.hardware_id,
        app_version="1.0.0",
        platform="unknown"
    )
    result = await validate_license(val_req)
    if result.valid:
        ACTIVATION_DATABASE[request.license_key] = {
            'email': request.customer_email,
            'activated_at': datetime.now().isoformat(),
            'hardware_id': hash_hardware_id(request.hardware_id)
        }
        save_database()
    return result


@app.post("/api/deactivate")
async def deactivate_license(license_key: str, admin_token: str):
    if admin_token != ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="Unauthorized")
    if license_key in LICENSE_DATABASE:
        LICENSE_DATABASE[license_key]['hardware_id'] = None
        LICENSE_DATABASE[license_key]['deactivated_at'] = datetime.now().isoformat()
        save_database()
        return {"success": True, "message": "License deactivated and unbound"}
    raise HTTPException(status_code=404, detail="License not found")


@app.post("/api/admin/create-license")
async def create_license(request: CreateLicenseRequest):
    if request.admin_token != ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    license_key = generate_license_key()
    expires = datetime.now() + timedelta(days=request.duration_days)
    
    LICENSE_DATABASE[license_key] = {
        'key': license_key,
        'created_at': datetime.now().isoformat(),
        'expires': expires.isoformat(),
        'active': True,
        'customer_email': request.customer_email,
        'hardware_id': None,
        'duration_days': request.duration_days,
        'is_demo': request.is_demo,
        'max_users': -1 if request.is_demo else 1
    }
    save_database()
    
    email_sent = False
    email_error = None
    if SMTP_USER and request.customer_email:
        try:
            send_license_email(request.customer_email, license_key, expires.isoformat(), request.duration_days)
            email_sent = True
        except Exception as e:
            email_error = str(e)
    
    return {"license_key": license_key, "expires": expires.isoformat(), "message": "License created", "email_sent": email_sent, "email_error": email_error}


@app.post("/api/admin/import-license")
async def import_license(request: ImportLicenseRequest):
    """Import an existing license (e.g. from old server)"""
    if request.admin_token != ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    LICENSE_DATABASE[request.license_key] = {
        'key': request.license_key,
        'created_at': datetime.now().isoformat(),
        'expires': request.expires,
        'active': True,
        'customer_email': request.customer_email,
        'hardware_id': request.hardware_id,
        'duration_days': request.duration_days,
        'is_demo': request.is_demo,
        'max_users': -1 if request.is_demo else 1
    }
    if request.hardware_id:
        ACTIVATION_DATABASE[request.license_key] = {
            'hardware_id': request.hardware_id,
            'activated_at': datetime.now().isoformat()
        }
    save_database()
    return {"success": True, "message": f"License {request.license_key} imported", "expires": request.expires}


@app.get("/api/admin/list-licenses")
async def list_licenses(admin_token: str):
    if admin_token != ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="Unauthorized")
    return {"licenses": list(LICENSE_DATABASE.values()), "total": len(LICENSE_DATABASE)}


@app.get("/api/admin/stats")
async def get_stats(admin_token: str):
    if admin_token != ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="Unauthorized")
    total = len(LICENSE_DATABASE)
    active = sum(1 for l in LICENSE_DATABASE.values() if l.get('active'))
    bound = sum(1 for l in LICENSE_DATABASE.values() if l.get('hardware_id'))
    expired = sum(1 for l in LICENSE_DATABASE.values() if datetime.fromisoformat(l['expires']) < datetime.now())
    return {"total_licenses": total, "active_licenses": active, "bound_licenses": bound, "expired_licenses": expired}


@app.post("/api/admin/delete-license")
async def delete_license(request: DeleteLicenseRequest):
    if request.admin_token != ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="Unauthorized")
    if request.license_key not in LICENSE_DATABASE:
        raise HTTPException(status_code=404, detail="License not found")
    if LICENSE_DATABASE[request.license_key].get('is_demo'):
        raise HTTPException(status_code=403, detail="Cannot delete demo license")
    del LICENSE_DATABASE[request.license_key]
    save_database()
    return {"success": True, "message": f"License {request.license_key} deleted"}


@app.post("/api/admin/resend-email")
async def resend_email(request: ResendEmailRequest):
    if request.admin_token != ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="Unauthorized")
    if request.license_key not in LICENSE_DATABASE:
        raise HTTPException(status_code=404, detail="License not found")
    
    lic = LICENSE_DATABASE[request.license_key]
    email = request.customer_email or lic.get('customer_email', '')
    if not email:
        raise HTTPException(status_code=400, detail="No email address")
    
    expires_date = lic.get('expires', '')
    duration_days = max(1, (datetime.fromisoformat(expires_date) - datetime.now()).days) if expires_date else 365
    
    try:
        send_license_email(email, request.license_key, expires_date, duration_days)
        return {"success": True, "message": f"Email sent to {email}"}
    except Exception as e:
        return {"success": False, "message": str(e)}


# ── Admin file upload ──

@app.post("/api/admin/upload-installer")
async def upload_installer(admin_token: str = Form(...), file: UploadFile = File(...)):
    """Upload installer files (DEB/EXE) via admin API"""
    if admin_token != ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    allowed_ext = ('.deb', '.exe', '.AppImage', '.dmg', '.zip', '.png', '.jpg', '.jpeg', '.svg', '.ico', '.gif', '.webp')
    if not any(file.filename.endswith(ext) for ext in allowed_ext):
        raise HTTPException(status_code=400, detail=f"Only installer/image files allowed: {allowed_ext}")
    
    filepath = os.path.join(STATIC_DIR, file.filename)
    contents = await file.read()
    with open(filepath, "wb") as f:
        f.write(contents)
    
    size_mb = len(contents) / (1024 * 1024)
    return {"success": True, "filename": file.filename, "size_mb": round(size_mb, 2)}


@app.get("/api/admin/list-files")
async def list_files(admin_token: str = ""):
    """List uploaded installer files"""
    if admin_token != ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    files = []
    if os.path.exists(STATIC_DIR):
        for f in os.listdir(STATIC_DIR):
            fpath = os.path.join(STATIC_DIR, f)
            if os.path.isfile(fpath):
                files.append({"name": f, "size_mb": round(os.path.getsize(fpath) / (1024*1024), 2)})
    return {"files": files}


# ── Edit license endpoint ──

class EditLicenseRequest(BaseModel):
    admin_token: str
    license_key: str
    customer_email: Optional[str] = None
    expires: Optional[str] = None
    active: Optional[bool] = None
    hardware_id: Optional[str] = None  # set to "" to unbind


@app.post("/api/admin/edit-license")
async def edit_license(request: EditLicenseRequest):
    if request.admin_token != ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="Unauthorized")
    if request.license_key not in LICENSE_DATABASE:
        raise HTTPException(status_code=404, detail="License not found")
    
    lic = LICENSE_DATABASE[request.license_key]
    changes = []
    if request.customer_email is not None:
        lic['customer_email'] = request.customer_email
        changes.append("email")
    if request.expires is not None:
        lic['expires'] = request.expires
        changes.append("expires")
    if request.active is not None:
        lic['active'] = request.active
        changes.append("active")
    if request.hardware_id is not None:
        lic['hardware_id'] = request.hardware_id if request.hardware_id != "" else None
        changes.append("hardware_id")
    
    lic['updated_at'] = datetime.now().isoformat()
    save_database()
    return {"success": True, "message": f"License updated ({', '.join(changes)})", "license": lic}


# ══════════════════════════════════════════════════════════════════
#   ADMIN DASHBOARD (Web UI)
# ══════════════════════════════════════════════════════════════════

ADMIN_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Connexa License Admin</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        * { font-family: 'Inter', sans-serif; }
        body { background: #0f172a; color: #e2e8f0; }
        .glass { background: rgba(30,41,59,0.7); backdrop-filter: blur(12px); border: 1px solid rgba(71,85,105,0.3); }
        .status-active { background: #059669; }
        .status-expired { background: #dc2626; }
        .status-inactive { background: #d97706; }
        .modal-bg { background: rgba(0,0,0,0.6); backdrop-filter: blur(4px); }
        input, select { background: #1e293b; border: 1px solid #334155; color: #e2e8f0; }
        input:focus, select:focus { outline: none; border-color: #3b82f6; box-shadow: 0 0 0 2px rgba(59,130,246,0.2); }
    </style>
</head>
<body class="min-h-screen">
    <!-- Header -->
    <header class="border-b border-slate-700/50 bg-slate-900/80 backdrop-blur sticky top-0 z-40">
        <div class="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
            <div class="flex items-center gap-3">
                <div class="w-9 h-9 rounded-lg bg-gradient-to-br from-blue-500 to-cyan-500 flex items-center justify-center font-bold text-white">C</div>
                <div>
                    <h1 class="text-lg font-bold text-white">Connexa License Admin</h1>
                    <p class="text-xs text-slate-500">Connexify (Pty) Ltd</p>
                </div>
            </div>
            <div class="flex items-center gap-3">
                <div id="stats-bar" class="hidden md:flex items-center gap-4 text-xs text-slate-400 mr-4"></div>
                <a href="/" class="text-xs text-slate-400 hover:text-white transition">&larr; Back to Website</a>
            </div>
        </div>
    </header>

    <div class="max-w-7xl mx-auto px-6 py-8">
        <!-- Login -->
        <div id="login-section">
            <div class="max-w-md mx-auto mt-20">
                <div class="glass rounded-2xl p-8">
                    <h2 class="text-xl font-bold text-white mb-6 text-center">Admin Login</h2>
                    <div class="space-y-4">
                        <input id="token-input" type="password" placeholder="Admin Token" class="w-full px-4 py-3 rounded-lg text-sm">
                        <button onclick="login()" class="w-full bg-blue-600 hover:bg-blue-500 text-white py-3 rounded-lg font-medium transition">Sign In</button>
                        <p id="login-error" class="text-red-400 text-sm text-center hidden"></p>
                    </div>
                </div>
            </div>
        </div>

        <!-- Dashboard (hidden until login) -->
        <div id="dashboard-section" class="hidden">
            <!-- Stats Cards -->
            <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
                <div class="glass rounded-xl p-5">
                    <p class="text-sm text-slate-400 mb-1">Total Licenses</p>
                    <p id="stat-total" class="text-3xl font-bold text-white">-</p>
                </div>
                <div class="glass rounded-xl p-5">
                    <p class="text-sm text-slate-400 mb-1">Active</p>
                    <p id="stat-active" class="text-3xl font-bold text-green-400">-</p>
                </div>
                <div class="glass rounded-xl p-5">
                    <p class="text-sm text-slate-400 mb-1">Bound to HW</p>
                    <p id="stat-bound" class="text-3xl font-bold text-cyan-400">-</p>
                </div>
                <div class="glass rounded-xl p-5">
                    <p class="text-sm text-slate-400 mb-1">Expired</p>
                    <p id="stat-expired" class="text-3xl font-bold text-red-400">-</p>
                </div>
            </div>

            <!-- Actions Bar -->
            <div class="flex flex-wrap items-center justify-between gap-4 mb-6">
                <h2 class="text-xl font-bold text-white">Licenses</h2>
                <div class="flex gap-3">
                    <button onclick="showCreateModal()" class="bg-blue-600 hover:bg-blue-500 text-white px-5 py-2.5 rounded-lg text-sm font-medium transition flex items-center gap-2">
                        <span class="text-lg">+</span> Create License
                    </button>
                    <button onclick="loadLicenses()" class="bg-slate-700 hover:bg-slate-600 text-white px-4 py-2.5 rounded-lg text-sm font-medium transition">
                        &#8635; Refresh
                    </button>
                </div>
            </div>

            <!-- License Table -->
            <div class="glass rounded-xl overflow-hidden">
                <div class="overflow-x-auto">
                    <table class="w-full text-sm">
                        <thead>
                            <tr class="border-b border-slate-700/50 text-left text-slate-400">
                                <th class="px-5 py-3 font-medium">License Key</th>
                                <th class="px-5 py-3 font-medium">Customer</th>
                                <th class="px-5 py-3 font-medium">Status</th>
                                <th class="px-5 py-3 font-medium">Expires</th>
                                <th class="px-5 py-3 font-medium">Hardware</th>
                                <th class="px-5 py-3 font-medium text-right">Actions</th>
                            </tr>
                        </thead>
                        <tbody id="license-table-body">
                            <tr><td colspan="6" class="px-5 py-10 text-center text-slate-500">Loading...</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>

    <!-- Create License Modal -->
    <div id="create-modal" class="fixed inset-0 z-50 hidden items-center justify-center modal-bg">
        <div class="glass rounded-2xl p-8 w-full max-w-md mx-4">
            <h3 class="text-lg font-bold text-white mb-6">Create New License</h3>
            <div class="space-y-4">
                <div>
                    <label class="text-xs text-slate-400 block mb-1">Customer Email</label>
                    <input id="create-email" type="email" placeholder="customer@example.com" class="w-full px-4 py-2.5 rounded-lg text-sm">
                </div>
                <div>
                    <label class="text-xs text-slate-400 block mb-1">Duration (days)</label>
                    <input id="create-days" type="number" value="365" class="w-full px-4 py-2.5 rounded-lg text-sm">
                </div>
                <div class="flex items-center gap-2">
                    <input id="create-demo" type="checkbox" class="w-4 h-4 rounded">
                    <label class="text-sm text-slate-400">Demo / Trial license</label>
                </div>
                <div class="flex gap-3 mt-6">
                    <button onclick="createLicense()" class="flex-1 bg-blue-600 hover:bg-blue-500 text-white py-2.5 rounded-lg text-sm font-medium transition">Create</button>
                    <button onclick="closeModal('create-modal')" class="flex-1 bg-slate-700 hover:bg-slate-600 text-white py-2.5 rounded-lg text-sm font-medium transition">Cancel</button>
                </div>
                <p id="create-result" class="text-sm text-center hidden"></p>
            </div>
        </div>
    </div>

    <!-- Edit License Modal -->
    <div id="edit-modal" class="fixed inset-0 z-50 hidden items-center justify-center modal-bg">
        <div class="glass rounded-2xl p-8 w-full max-w-md mx-4">
            <h3 class="text-lg font-bold text-white mb-2">Edit License</h3>
            <p id="edit-key-display" class="text-xs text-cyan-400 font-mono mb-6"></p>
            <div class="space-y-4">
                <div>
                    <label class="text-xs text-slate-400 block mb-1">Customer Email</label>
                    <input id="edit-email" type="email" class="w-full px-4 py-2.5 rounded-lg text-sm">
                </div>
                <div>
                    <label class="text-xs text-slate-400 block mb-1">Expires (YYYY-MM-DD)</label>
                    <input id="edit-expires" type="date" class="w-full px-4 py-2.5 rounded-lg text-sm">
                </div>
                <div>
                    <label class="text-xs text-slate-400 block mb-1">Status</label>
                    <select id="edit-active" class="w-full px-4 py-2.5 rounded-lg text-sm">
                        <option value="true">Active</option>
                        <option value="false">Inactive</option>
                    </select>
                </div>
                <div class="flex items-center gap-2">
                    <input id="edit-unbind" type="checkbox" class="w-4 h-4 rounded">
                    <label class="text-sm text-slate-400">Unbind from hardware (allow re-activation)</label>
                </div>
                <div class="flex gap-3 mt-6">
                    <button onclick="saveEdit()" class="flex-1 bg-blue-600 hover:bg-blue-500 text-white py-2.5 rounded-lg text-sm font-medium transition">Save</button>
                    <button onclick="closeModal('edit-modal')" class="flex-1 bg-slate-700 hover:bg-slate-600 text-white py-2.5 rounded-lg text-sm font-medium transition">Cancel</button>
                </div>
                <p id="edit-result" class="text-sm text-center hidden"></p>
            </div>
        </div>
    </div>

    <!-- Toast -->
    <div id="toast" class="fixed bottom-6 right-6 bg-green-600 text-white px-6 py-3 rounded-xl shadow-lg text-sm font-medium transform translate-y-20 opacity-0 transition-all duration-300 z-50"></div>

    <script>
        let TOKEN = '';
        const BASE = window.location.origin;

        // ── Auth ──
        document.getElementById('token-input').addEventListener('keydown', e => { if (e.key === 'Enter') login(); });

        async function login() {
            TOKEN = document.getElementById('token-input').value.trim();
            if (!TOKEN) return;
            try {
                const r = await fetch(`${BASE}/api/admin/stats?admin_token=${encodeURIComponent(TOKEN)}`);
                if (!r.ok) throw new Error('Invalid token');
                document.getElementById('login-section').classList.add('hidden');
                document.getElementById('dashboard-section').classList.remove('hidden');
                loadLicenses();
                loadStats();
            } catch (e) {
                const el = document.getElementById('login-error');
                el.textContent = 'Invalid admin token';
                el.classList.remove('hidden');
            }
        }

        // ── Load Data ──
        async function loadStats() {
            const r = await fetch(`${BASE}/api/admin/stats?admin_token=${encodeURIComponent(TOKEN)}`);
            const d = await r.json();
            document.getElementById('stat-total').textContent = d.total_licenses;
            document.getElementById('stat-active').textContent = d.active_licenses;
            document.getElementById('stat-bound').textContent = d.bound_licenses;
            document.getElementById('stat-expired').textContent = d.expired_licenses;
        }

        async function loadLicenses() {
            const r = await fetch(`${BASE}/api/admin/list-licenses?admin_token=${encodeURIComponent(TOKEN)}`);
            const d = await r.json();
            const tbody = document.getElementById('license-table-body');
            
            if (!d.licenses || d.licenses.length === 0) {
                tbody.innerHTML = '<tr><td colspan="6" class="px-5 py-10 text-center text-slate-500">No licenses found</td></tr>';
                return;
            }

            tbody.innerHTML = d.licenses.map(lic => {
                const isExpired = new Date(lic.expires) < new Date();
                const isActive = lic.active && !isExpired;
                const statusClass = isExpired ? 'status-expired' : (lic.active ? 'status-active' : 'status-inactive');
                const statusText = isExpired ? 'Expired' : (lic.active ? 'Active' : 'Inactive');
                const expDate = lic.expires ? lic.expires.substring(0, 10) : 'N/A';
                const hwBound = lic.hardware_id ? '&#128274; Bound' : '&#128275; Unbound';
                const hwClass = lic.hardware_id ? 'text-cyan-400' : 'text-slate-500';
                const email = lic.customer_email || '<span class="text-slate-600 italic">none</span>';
                const demoTag = lic.is_demo ? '<span class="ml-2 text-[10px] bg-yellow-600/20 text-yellow-400 px-1.5 py-0.5 rounded">DEMO</span>' : '';

                return `<tr class="border-b border-slate-700/30 hover:bg-slate-800/30 transition">
                    <td class="px-5 py-3">
                        <span class="font-mono text-xs text-cyan-300">${lic.key}</span>${demoTag}
                    </td>
                    <td class="px-5 py-3 text-xs">${email}</td>
                    <td class="px-5 py-3">
                        <span class="inline-flex items-center gap-1.5 text-xs">
                            <span class="w-2 h-2 rounded-full ${statusClass}"></span>
                            ${statusText}
                        </span>
                    </td>
                    <td class="px-5 py-3 text-xs ${isExpired ? 'text-red-400' : 'text-slate-300'}">${expDate}</td>
                    <td class="px-5 py-3 text-xs ${hwClass}">${hwBound}</td>
                    <td class="px-5 py-3 text-right">
                        <div class="flex items-center justify-end gap-1">
                            <button onclick="showEditModal('${lic.key}')" class="px-2.5 py-1.5 rounded-md bg-slate-700 hover:bg-slate-600 text-xs text-white transition" title="Edit">&#9998;</button>
                            ${lic.hardware_id ? `<button onclick="unbindLicense('${lic.key}')" class="px-2.5 py-1.5 rounded-md bg-orange-700/50 hover:bg-orange-600/50 text-xs text-orange-300 transition" title="Unbind HW">&#128275;</button>` : ''}
                            ${!lic.is_demo ? `<button onclick="deleteLicense('${lic.key}')" class="px-2.5 py-1.5 rounded-md bg-red-700/50 hover:bg-red-600/50 text-xs text-red-300 transition" title="Delete">&#128465;</button>` : ''}
                        </div>
                    </td>
                </tr>`;
            }).join('');

            loadStats();
        }

        // ── Create License ──
        function showCreateModal() {
            document.getElementById('create-email').value = '';
            document.getElementById('create-days').value = '365';
            document.getElementById('create-demo').checked = false;
            document.getElementById('create-result').classList.add('hidden');
            document.getElementById('create-modal').classList.remove('hidden');
            document.getElementById('create-modal').classList.add('flex');
        }

        async function createLicense() {
            const email = document.getElementById('create-email').value.trim();
            const days = parseInt(document.getElementById('create-days').value) || 365;
            const isDemo = document.getElementById('create-demo').checked;

            const r = await fetch(`${BASE}/api/admin/create-license`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ admin_token: TOKEN, customer_email: email, duration_days: days, is_demo: isDemo })
            });
            const d = await r.json();
            
            if (d.license_key) {
                closeModal('create-modal');
                showToast(`License created: ${d.license_key}`);
                loadLicenses();
            } else {
                const el = document.getElementById('create-result');
                el.textContent = d.detail || 'Error creating license';
                el.className = 'text-sm text-center text-red-400';
                el.classList.remove('hidden');
            }
        }

        // ── Edit License ──
        let editingKey = '';

        function showEditModal(key) {
            editingKey = key;
            // Find license data from the table (re-fetch to be safe)
            fetch(`${BASE}/api/admin/list-licenses?admin_token=${encodeURIComponent(TOKEN)}`)
                .then(r => r.json())
                .then(d => {
                    const lic = d.licenses.find(l => l.key === key);
                    if (!lic) return;
                    document.getElementById('edit-key-display').textContent = key;
                    document.getElementById('edit-email').value = lic.customer_email || '';
                    document.getElementById('edit-expires').value = lic.expires ? lic.expires.substring(0, 10) : '';
                    document.getElementById('edit-active').value = lic.active ? 'true' : 'false';
                    document.getElementById('edit-unbind').checked = false;
                    document.getElementById('edit-result').classList.add('hidden');
                    document.getElementById('edit-modal').classList.remove('hidden');
                    document.getElementById('edit-modal').classList.add('flex');
                });
        }

        async function saveEdit() {
            const body = {
                admin_token: TOKEN,
                license_key: editingKey,
                customer_email: document.getElementById('edit-email').value.trim(),
                expires: document.getElementById('edit-expires').value + 'T23:59:59',
                active: document.getElementById('edit-active').value === 'true'
            };
            if (document.getElementById('edit-unbind').checked) {
                body.hardware_id = '';
            }

            const r = await fetch(`${BASE}/api/admin/edit-license`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(body)
            });
            const d = await r.json();
            
            if (d.success) {
                closeModal('edit-modal');
                showToast('License updated');
                loadLicenses();
            } else {
                const el = document.getElementById('edit-result');
                el.textContent = d.detail || 'Error updating license';
                el.className = 'text-sm text-center text-red-400';
                el.classList.remove('hidden');
            }
        }

        // ── Unbind ──
        async function unbindLicense(key) {
            if (!confirm(`Unbind hardware from license ${key}?\\nThis will allow re-activation on a new machine.`)) return;
            const r = await fetch(`${BASE}/api/admin/edit-license`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ admin_token: TOKEN, license_key: key, hardware_id: '' })
            });
            const d = await r.json();
            if (d.success) { showToast('Hardware unbound'); loadLicenses(); }
        }

        // ── Delete ──
        async function deleteLicense(key) {
            if (!confirm(`DELETE license ${key}?\\n\\nThis cannot be undone!`)) return;
            const r = await fetch(`${BASE}/api/admin/delete-license`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ admin_token: TOKEN, license_key: key })
            });
            const d = await r.json();
            if (d.success) { showToast('License deleted'); loadLicenses(); }
        }

        // ── Helpers ──
        function closeModal(id) {
            document.getElementById(id).classList.add('hidden');
            document.getElementById(id).classList.remove('flex');
        }

        function showToast(msg) {
            const t = document.getElementById('toast');
            t.textContent = msg;
            t.classList.remove('translate-y-20', 'opacity-0');
            setTimeout(() => t.classList.add('translate-y-20', 'opacity-0'), 3000);
        }

        // Close modals on bg click
        document.querySelectorAll('.modal-bg').forEach(el => {
            el.addEventListener('click', e => { if (e.target === el) closeModal(el.id); });
        });
    </script>
</body>
</html>"""


@app.get("/admin", response_class=HTMLResponse)
async def admin_dashboard():
    """License management admin dashboard"""
    return HTMLResponse(content=ADMIN_HTML)


# ── Downloads page (legacy URL compat) ──

@app.get("/downloads", response_class=HTMLResponse)
async def downloads_page():
    """Redirect to homepage downloads section"""
    return RedirectResponse(url="/#downloads")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8002")))
