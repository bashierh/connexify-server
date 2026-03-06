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
import asyncio
import random
import logging
from pathlib import Path
from typing import Optional

# ── Email service (inline, no external dependency) ──
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ── Website templates ──
from templates import WEBSITE_TEMPLATE, GET_STARTED_TEMPLATE
from portal_template import PORTAL_TEMPLATE
from admin_template import ADMIN_HTML

# ── Persistent storage abstraction (GCS or local) ──
import storage as store

app = FastAPI(title="Connexa License Server", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Configuration ──
# On Cloud Run containers use /tmp for local caching. On Render use the
# persistent disk.  For local dev, fall back to the current directory.
_RENDER_DATA = Path("/opt/render/project/data")
_CLOUD_RUN_TMP = Path("/tmp/connexify-data")
if _RENDER_DATA.exists():
    DATA_DIR = str(_RENDER_DATA)
elif os.getenv("K_SERVICE"):      # Cloud Run sets K_SERVICE automatically
    _CLOUD_RUN_TMP.mkdir(parents=True, exist_ok=True)
    DATA_DIR = str(_CLOUD_RUN_TMP)
else:
    DATA_DIR = "."

LICENSE_DB_FILE = Path(os.path.join(DATA_DIR, "license_database.json"))

ADMIN_TOKEN = os.getenv("ADMIN_TOKEN") or os.getenv("ADMIN_SECRET_TOKEN", "your-admin-secret-token-change-this")
CURRENT_VERSION = os.getenv("CONNEXA_VERSION", "5.2.8")
SMTP_HOST = os.getenv("SMTP_HOST", "mail.connexify.co.za")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "admin@connexify.co.za")
SMTP_PASS = os.getenv("SMTP_PASSWORD", "159951B@sh!")
FROM_EMAIL = os.getenv("FROM_EMAIL", SMTP_USER)
FROM_NAME = os.getenv("FROM_NAME", "Connexify")
COMPANY_NAME = os.getenv("COMPANY_NAME", "Connexify")
SUPPORT_EMAIL = os.getenv("SUPPORT_EMAIL", "admin@connexify.co.za")

# ── PayFast configuration ──
PAYFAST_MERCHANT_ID = os.getenv("PAYFAST_MERCHANT_ID", "27484481")
PAYFAST_MERCHANT_KEY = os.getenv("PAYFAST_MERCHANT_KEY", "4xkai7s4ataw7")
PAYFAST_PASSPHRASE = os.getenv("PAYFAST_PASSPHRASE", "159951Bashier")
PAYFAST_URL = os.getenv("PAYFAST_URL", "https://www.payfast.co.za/eng/process")
SITE_URL = os.getenv("SITE_URL", "https://www.connexify.co.za")

# ══════════════════════════════════════════════════════════════════
#   PORTAL USER DATABASE (self-contained, no Supabase needed)
# ══════════════════════════════════════════════════════════════════
PORTAL_USERS_FILE = os.path.join(DATA_DIR, "portal_users.json")
PORTAL_USERS = {}  # email -> {email, full_name, company, phone, password_hash, salt, created_at, is_suspended}
PORTAL_SESSIONS = {}  # token -> email
PORTAL_RESET_TOKENS = {}  # reset_token -> {email, expires}

def _hash_password(password: str, salt: str = None) -> tuple:
    """Hash password with salt. Returns (hash, salt)."""
    if not salt:
        salt = secrets.token_hex(16)
    pw_hash = hashlib.sha256((password + salt).encode()).hexdigest()
    return pw_hash, salt

def load_portal_users():
    global PORTAL_USERS
    try:
        data = store.load_json(PORTAL_USERS_FILE)
        if data:
            PORTAL_USERS = data
            print(f"[Portal] Loaded {len(PORTAL_USERS)} portal users")
    except Exception as e:
        print(f"[Portal] Error loading users: {e}")

def save_portal_users():
    try:
        store.save_json(PORTAL_USERS_FILE, PORTAL_USERS)
    except Exception as e:
        print(f"[Portal] Error saving users: {e}")

def create_portal_user(email: str, password: str, full_name: str = "", company: str = "") -> dict:
    """Create a new portal user. Returns user dict."""
    email = email.lower().strip()
    pw_hash, salt = _hash_password(password)
    user = {
        "email": email,
        "full_name": full_name,
        "company": company,
        "phone": "",
        "password_hash": pw_hash,
        "salt": salt,
        "created_at": datetime.now().isoformat(),
        "is_suspended": False,
    }
    PORTAL_USERS[email] = user
    save_portal_users()
    print(f"[Portal] User created: {email}")
    return user

def verify_portal_login(email: str, password: str) -> dict | None:
    """Verify credentials. Returns user dict or None."""
    email = email.lower().strip()
    user = PORTAL_USERS.get(email)
    if not user:
        return None
    pw_hash, _ = _hash_password(password, user["salt"])
    if pw_hash != user["password_hash"]:
        return None
    return user

def create_session(email: str) -> str:
    """Create a session token for a user."""
    token = secrets.token_hex(32)
    PORTAL_SESSIONS[token] = email.lower().strip()
    return token

def get_session_user(token: str) -> dict | None:
    """Get user from session token."""
    email = PORTAL_SESSIONS.get(token)
    if not email:
        return None
    user = PORTAL_USERS.get(email)
    if not user:
        return None
    if user.get("is_suspended"):
        return None
    return user

load_portal_users()

# In-memory database
LICENSE_DATABASE = {}
ACTIVATION_DATABASE = {}


def load_database():
    global LICENSE_DATABASE, ACTIVATION_DATABASE
    try:
        data = store.load_json(str(LICENSE_DB_FILE))
        if data:
            LICENSE_DATABASE = data.get('licenses', {})
            ACTIVATION_DATABASE = data.get('activations', {})
            print(f"Loaded {len(LICENSE_DATABASE)} licenses")
    except Exception as e:
        print(f"Error loading database: {e}")


def save_database():
    try:
        store.save_json(str(LICENSE_DB_FILE), {
            'licenses': LICENSE_DATABASE,
            'activations': ACTIVATION_DATABASE
        })
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


def send_multi_license_email(customer_email: str, license_keys: list, duration_days: int, is_annual: int = 0):
    """Send welcome email with one or more license keys."""
    if not SMTP_USER or not SMTP_PASS:
        print("Email not configured, skipping")
        return False

    expires_date = (datetime.now() + timedelta(days=duration_days)).strftime('%Y-%m-%d')
    qty = len(license_keys)

    # Build license keys HTML block
    keys_html = ""
    for i, key in enumerate(license_keys, 1):
        label = f"License Key {i} of {qty}" if qty > 1 else "Your License Key"
        keys_html += f"""
        <div style="background: #1e293b; border: 1px solid #334155; border-radius: 8px; padding: 24px; margin: 16px 0; text-align: center;">
            <p style="color: #94a3b8; margin: 0 0 8px; font-size: 13px;">{label}</p>
            <p style="font-size: 22px; font-weight: bold; color: #22d3ee; letter-spacing: 2px; font-family: monospace; margin: 0;">{key}</p>
        </div>"""

    summary = f"{qty} license(s)" if qty > 1 else "1 license"
    duration_label = "1 Year" if is_annual else "1 Month"

    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; background: #0f172a; color: #e2e8f0; padding: 40px; border-radius: 12px;">
        <h1 style="color: #3b82f6; text-align: center;">Welcome to Connexa</h1>
        <p style="text-align: center; color: #94a3b8;">Professional Network Management Platform</p>
        <div style="background: #1e293b; border-radius: 8px; padding: 16px; margin: 20px 0; text-align: center;">
            <p style="color: #94a3b8; margin: 0;">Order Summary: <strong style="color: #fff;">{summary}</strong> &bull; <strong style="color: #fff;">{duration_label}</strong> &bull; Expires <strong style="color: #fff;">{expires_date}</strong></p>
        </div>
        {keys_html}
        <p style="margin-top: 24px;"><strong>How to activate:</strong></p>
        <ol style="color: #94a3b8; font-size: 14px;">
            <li>Download Connexa from <a href="https://www.connexify.co.za/downloads" style="color: #3b82f6;">connexify.co.za/downloads</a></li>
            <li>Install and launch the application</li>
            <li>Enter your license key when prompted</li>
            <li>Each license activates one installation</li>
        </ol>
        <hr style="border: none; border-top: 1px solid #334155; margin: 24px 0;">
        <p style="font-size: 12px; color: #64748b; text-align: center;">Need help? Contact {SUPPORT_EMAIL}</p>
        <p style="font-size: 12px; color: #64748b; text-align: center;">&copy; {datetime.now().year} {COMPANY_NAME} (Pty) Ltd</p>
    </div>
    """

    subject = f"Welcome to Connexa - Your {summary}" if qty > 1 else "Welcome to Connexa - Your License Key"
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
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
    print(f"[Startup] DATA_DIR={DATA_DIR}  GCS_BUCKET={store.GCS_BUCKET or '(none)'}  STATIC_DIR={STATIC_DIR}")
    load_database()
    load_portal_users()
    load_social_posts()
    load_social_accounts()

    # Start social media automation background loop
    global _automation_task
    _automation_task = asyncio.create_task(_automation_loop())
    print("[Startup] Social media automation scheduler started")

    # Sync small static files from GCS → local STATIC_DIR (logos, etc.)
    # Large installer files (.deb/.exe) are served via GCS signed URL redirect
    if store.using_gcs():
        try:
            gcs_files = store.list_files(str(STATIC_DIR))
            for finfo in gcs_files:
                fname = finfo["name"]
                local_path = STATIC_DIR / fname
                # Skip large files — they'll be served via signed URL redirect
                if fname.endswith(('.deb', '.exe', '.AppImage', '.dmg', '.zip')) and finfo.get('size_mb', 0) > 10:
                    print(f"[Startup] Skipping large file {fname} ({finfo['size_mb']} MB) — served via GCS redirect")
                    continue
                if not local_path.exists():
                    data = store.load_file(str(STATIC_DIR), fname)
                    if data:
                        local_path.write_bytes(data)
                        print(f"[Startup] Synced {fname} from GCS ({finfo['size_mb']} MB)")
        except Exception as e:
            print(f"[Startup] Error syncing static files from GCS: {e}")

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
PORTAL_HTML = _render_template(PORTAL_TEMPLATE)


# ══════════════════════════════════════════════════════════════════
#   ROUTES - Website
# ══════════════════════════════════════════════════════════════════

@app.get("/", response_class=HTMLResponse)
async def homepage(request: Request):
    """Connexify company website.

    - Redirect the license subdomain to the admin portal.
    - All other requests for the main domains should land on the
      step-by-step wizard so that visitors immediately see the
      download/installation instructions.
    """
    # log every header for debugging
    headers = dict(request.headers)
    print("[homepage] headers:", headers)
    host = headers.get("host", "").lower()

    # license subdomain -> admin portal
    if host.startswith("license."):
        print("[homepage] redirecting license host to /admin")
        return RedirectResponse(url="/admin")

    # Serve the full marketing site so that anchor links like
    # /#downloads, /#pricing, etc. work correctly.
    return HTMLResponse(content=WEBSITE_HTML)


@app.get("/get-started", response_class=HTMLResponse)
async def get_started_page():
    """Step-by-step get started wizard"""
    return HTMLResponse(content=GET_STARTED_HTML)


@app.get("/portal", response_class=HTMLResponse)
async def portal_page():
    """Customer portal dashboard"""
    return HTMLResponse(content=PORTAL_HTML)


@app.get("/docs", response_class=HTMLResponse)
async def docs_page():
    """Redirect to about section on homepage"""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/#about")


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
#   ROUTES - Free Trial (with email verification)
# ══════════════════════════════════════════════════════════════════

# In-memory store for email verification codes: {email: {code, expires, name, company, password}}
EMAIL_VERIFICATION_CODES: dict = {}

class TrialRequest(BaseModel):
    name: str
    email: str
    company: str = ""
    password: str = ""
    verification_code: str = ""   # Required on second call


class VerificationRequest(BaseModel):
    email: str
    name: str = ""
    company: str = ""
    password: str = ""


def send_verification_email(customer_email: str, code: str):
    """Send a 6-digit verification code to the customer's email."""
    if not SMTP_USER or not SMTP_PASS:
        print("Email not configured, skipping verification email")
        return False

    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; background: #0f172a; color: #e2e8f0; padding: 40px; border-radius: 12px;">
        <h1 style="color: #3b82f6; text-align: center;">Verify Your Email</h1>
        <p style="text-align: center; color: #94a3b8;">Enter this code to activate your Connexa trial</p>
        <div style="background: #1e293b; border: 1px solid #334155; border-radius: 8px; padding: 24px; margin: 20px 0; text-align: center;">
            <p style="color: #94a3b8; margin: 0 0 8px; font-size: 13px;">Your Verification Code</p>
            <p style="font-size: 36px; font-weight: bold; color: #22d3ee; letter-spacing: 8px; font-family: monospace; margin: 0;">{code}</p>
        </div>
        <p style="color: #64748b; font-size: 13px; text-align: center;">This code expires in 10 minutes.</p>
        <p style="color: #64748b; font-size: 12px; text-align: center; margin-top: 20px;">If you didn't request this, you can safely ignore this email.</p>
    </div>"""

    msg = MIMEMultipart('alternative')
    msg['Subject'] = 'Connexa - Email Verification Code'
    msg['From'] = f'{FROM_NAME} <{FROM_EMAIL}>'
    msg['To'] = customer_email
    msg.attach(MIMEText(html, 'html'))

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.sendmail(FROM_EMAIL, customer_email, msg.as_string())
    return True


@app.post("/api/trial/send-verification")
async def send_trial_verification(request: VerificationRequest):
    """Send a 6-digit verification code to the email before trial activation."""
    email = request.email.strip().lower()
    if not email or "@" not in email:
        raise HTTPException(status_code=400, detail="Valid email is required")

    # Check if this email already has an expired trial
    for key, lic in LICENSE_DATABASE.items():
        if lic.get('customer_email', '').lower() == email and lic.get('is_demo'):
            expires_str = lic.get('expires', '')
            try:
                expires_dt = datetime.fromisoformat(expires_str)
                if expires_dt < datetime.now():
                    raise HTTPException(
                        status_code=400,
                        detail="Your 7-day trial has expired. Please subscribe to a professional license to continue using Connexa."
                    )
            except (ValueError, TypeError):
                pass

    # Generate 6-digit code
    import random
    code = f"{random.randint(100000, 999999)}"
    EMAIL_VERIFICATION_CODES[email] = {
        "code": code,
        "expires": (datetime.now() + timedelta(minutes=10)).isoformat(),
        "name": request.name,
        "company": request.company,
        "password": request.password,
    }
    print(f"[Trial Verification] Code generated for {email}: {code}")

    # Send the code
    if SMTP_USER:
        try:
            send_verification_email(email, code)
            print(f"[Trial Verification] Code sent to {email}")
        except Exception as e:
            print(f"[Trial Verification] Email error: {e}")
            raise HTTPException(status_code=500, detail="Failed to send verification email. Please try again.")

    return {"success": True, "message": "Verification code sent to your email. Check your inbox (and spam folder)."}


def send_trial_email(customer_email: str, license_key: str, expires_date: str):
    """Send welcome email with 7-day trial license key."""
    if not SMTP_USER or not SMTP_PASS:
        print("Email not configured, skipping trial email")
        return False

    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; background: #0f172a; color: #e2e8f0; padding: 40px; border-radius: 12px;">
        <h1 style="color: #3b82f6; text-align: center;">Welcome to Connexa!</h1>
        <p style="text-align: center; color: #94a3b8;">Your 7-Day Free Trial is Ready</p>
        <div style="background: #1e293b; border: 1px solid #334155; border-radius: 8px; padding: 24px; margin: 20px 0; text-align: center;">
            <p style="color: #94a3b8; margin: 0 0 8px; font-size: 13px;">Your Trial License Key</p>
            <p style="font-size: 22px; font-weight: bold; color: #22d3ee; letter-spacing: 2px; font-family: monospace; margin: 0;">{license_key}</p>
        </div>
        <div style="background: #1e293b; border-radius: 8px; padding: 16px; margin: 16px 0; text-align: center;">
            <p style="color: #94a3b8; margin: 0;">Trial Period: <strong style="color: #fff;">7 days</strong> &bull; Expires: <strong style="color: #fff;">{expires_date}</strong></p>
        </div>
        <p style="margin-top: 24px;"><strong>How to get started:</strong></p>
        <ol style="color: #94a3b8; font-size: 14px;">
            <li>Download Connexa from <a href="https://www.connexify.co.za/#downloads" style="color: #3b82f6;">connexify.co.za</a></li>
            <li>Install and launch the application</li>
            <li>Enter your trial license key when prompted</li>
            <li>Enjoy full access for 7 days!</li>
        </ol>
        <div style="background: #1e3a5f; border: 1px solid #2563eb; border-radius: 8px; padding: 16px; margin: 20px 0;">
            <p style="color: #93c5fd; margin: 0; font-size: 14px;"><strong>&#128187; Manage your license online</strong> — Log in to your customer portal at <a href="https://www.connexify.co.za/portal" style="color: #60a5fa;">connexify.co.za/portal</a> using the email and password you chose during signup.</p>
        </div>
        <div style="background: #1e3a5f; border: 1px solid #2563eb; border-radius: 8px; padding: 16px; margin: 10px 0;">
            <p style="color: #93c5fd; margin: 0; font-size: 14px;"><strong>&#128161; Ready to upgrade?</strong> When your trial ends, visit <a href="https://www.connexify.co.za/get-started?plan=professional" style="color: #60a5fa;">connexify.co.za/get-started</a> to purchase a full license. Plans start at R600/month.</p>
        </div>
        <hr style="border: none; border-top: 1px solid #334155; margin: 24px 0;">
        <p style="font-size: 12px; color: #64748b; text-align: center;">Need help? Contact {SUPPORT_EMAIL}</p>
        <p style="font-size: 12px; color: #64748b; text-align: center;">&copy; {datetime.now().year} {COMPANY_NAME} (Pty) Ltd</p>
    </div>
    """

    msg = MIMEMultipart('alternative')
    msg['Subject'] = 'Welcome to Connexa - Your 7-Day Trial License'
    msg['From'] = f'{FROM_NAME} <{FROM_EMAIL}>'
    msg['To'] = customer_email
    msg.attach(MIMEText(html, 'html'))

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.sendmail(FROM_EMAIL, customer_email, msg.as_string())
    return True


@app.post("/api/trial/activate")
async def activate_trial(request: TrialRequest):
    """Generate a 7-day trial license and email it. Requires email verification."""
    email = request.email.strip().lower()
    if not email:
        raise HTTPException(status_code=400, detail="Email is required")

    # ── Verify the email verification code ──
    verification = EMAIL_VERIFICATION_CODES.get(email)
    if not verification:
        raise HTTPException(status_code=400, detail="Please verify your email first. Click 'Send Verification Code'.")
    # Check code expiry
    try:
        code_expires = datetime.fromisoformat(verification["expires"])
        if code_expires < datetime.now():
            EMAIL_VERIFICATION_CODES.pop(email, None)
            raise HTTPException(status_code=400, detail="Verification code expired. Please request a new one.")
    except (ValueError, TypeError):
        pass
    # Check code match
    if request.verification_code.strip() != verification["code"]:
        raise HTTPException(status_code=400, detail="Invalid verification code. Please check your email and try again.")
    # Code valid — remove it so it can't be reused
    EMAIL_VERIFICATION_CODES.pop(email, None)

    # Check if this email already has a trial license
    for key, lic in LICENSE_DATABASE.items():
        if lic.get('customer_email', '').lower() == email and lic.get('is_demo'):
            # Check if trial has expired
            expires_str = lic.get('expires', '')
            try:
                expires_dt = datetime.fromisoformat(expires_str)
                if expires_dt < datetime.now():
                    raise HTTPException(
                        status_code=400,
                        detail="Your 7-day trial has expired. Please subscribe to a professional license to continue using Connexa."
                    )
            except (ValueError, TypeError):
                pass  # If we can't parse the date, allow re-send

            # Trial still active — re-send the key
            existing_key = lic['key']
            expires_date = lic.get('expires', 'N/A')
            if SMTP_USER:
                try:
                    send_trial_email(email, existing_key, expires_date[:10] if len(expires_date) > 10 else expires_date)
                except Exception as e:
                    print(f"[Trial] Email re-send error: {e}")
            # Create portal account if password provided and account doesn't exist yet
            if request.password and len(request.password) >= 6 and email not in PORTAL_USERS:
                try:
                    create_portal_user(email, request.password, request.name, request.company)
                    print(f"[Trial] Portal account created on re-send for {email}")
                except Exception as e:
                    print(f"[Trial] Portal account create error: {e}")
            return {"success": True, "message": "Trial license re-sent to your email.", "existing": True}

    # Generate new 7-day trial license
    license_key = generate_license_key()
    expires = datetime.now() + timedelta(days=7)
    expires_date = expires.strftime('%Y-%m-%d')

    LICENSE_DATABASE[license_key] = {
        'key': license_key,
        'created_at': datetime.now().isoformat(),
        'expires': expires.isoformat(),
        'active': True,
        'customer_email': email,
        'hardware_id': None,
        'duration_days': 7,
        'is_demo': True,
        'max_users': 1,
        'payment': {
            'method': 'trial',
            'customer_name': request.name,
            'company': request.company,
            'completed_at': datetime.now().isoformat()
        }
    }
    save_database()
    print(f"[Trial] 7-day trial license created for {email}: {license_key}")

    # Create portal account if password provided
    if request.password and len(request.password) >= 6 and email not in PORTAL_USERS:
        try:
            create_portal_user(email, request.password, request.name, request.company)
            print(f"[Trial] Portal account created for {email}")
        except Exception as e:
            print(f"[Trial] Portal account error: {e}")

    # Send trial welcome email
    if SMTP_USER:
        try:
            send_trial_email(email, license_key, expires_date)
            print(f"[Trial] Welcome email sent to {email}")
        except Exception as e:
            print(f"[Trial] Email error: {e}")

    portal_msg = " Your portal account is ready — log in at /portal" if (request.password and len(request.password) >= 6) else ""
    return {"success": True, "message": f"Trial license created and emailed!{portal_msg}", "existing": False}


# ══════════════════════════════════════════════════════════════════
#   ROUTES - PayFast Payment Integration
# ══════════════════════════════════════════════════════════════════

def generate_payfast_signature(data: dict) -> str:
    """Generate PayFast MD5 signature from payment data.

    PayFast requires the parameters in the SAME ORDER as the form fields
    (i.e. dict insertion order).  Empty / None values are excluded.
    The passphrase (if set) is appended as the final parameter.
    Values are URL-encoded with quote_plus (with '+' → ' ' pre-replace
    per PayFast's own Python example).
    """
    pairs = []
    for k, v in data.items():
        if v is None or str(v).strip() == "":
            continue
        val = str(v).strip().replace("+", " ")
        pairs.append(f"{k}={urllib.parse.quote_plus(val)}")
    if PAYFAST_PASSPHRASE:
        pp = PAYFAST_PASSPHRASE.strip().replace("+", " ")
        pairs.append(f"passphrase={urllib.parse.quote_plus(pp)}")
    pf_string = "&".join(pairs)
    print(f"[PayFast] signing string: {pf_string}")
    return hashlib.md5(pf_string.encode()).hexdigest()


class PayFastCheckoutRequest(BaseModel):
    name: str
    email: str
    company: str = ""
    plan: str = "professional"
    quantity: int = 1
    billing_cycle: str = "monthly"  # "monthly" or "annual"


@app.post("/api/payfast/checkout")
async def payfast_checkout(request: PayFastCheckoutRequest):
    """Generate PayFast payment URL and redirect data."""
    if request.plan != "professional":
        raise HTTPException(status_code=400, detail="Only professional plan supports online payment")

    qty = max(1, min(100, request.quantity))
    cycle = request.billing_cycle if request.billing_cycle in ("monthly", "annual") else "monthly"
    price_per_license = 6800 if cycle == "annual" else 600  # R600/mo or R6,800/yr
    total = price_per_license * qty
    duration_days = 365 if cycle == "annual" else 30

    # Unique payment ID for tracking
    payment_id = secrets.token_hex(8)

    cycle_label = "1 Year" if cycle == "annual" else "1 Month"
    item_name = f"Connexa Professional License x{qty} ({cycle_label})"
    item_desc = f"{qty} license(s), {cycle_label}, unlimited devices, all features"

    # Build PayFast data dict — ORDER MUST match PayFast's parameter spec:
    # merchant_id, merchant_key, return_url, cancel_url, notify_url,
    # name_first, name_last, email_address, [cell_number],
    # m_payment_id, amount, item_name, item_description,
    # custom_int1..5, custom_str1..5, ...
    name_parts = request.name.split() if request.name else []
    data = {
        "merchant_id": PAYFAST_MERCHANT_ID,
        "merchant_key": PAYFAST_MERCHANT_KEY,
        "return_url": f"{SITE_URL}/api/payfast/return?payment_id={payment_id}",
        "cancel_url": f"{SITE_URL}/api/payfast/cancel",
        "notify_url": f"{SITE_URL}/api/payfast/notify",
        "name_first": name_parts[0] if name_parts else "",
        "name_last": " ".join(name_parts[1:]) if len(name_parts) > 1 else "",
        "email_address": request.email,
        "m_payment_id": payment_id,
        "amount": f"{total:.2f}",
        "item_name": item_name[:100],
        "item_description": item_desc[:255],
        "custom_int1": str(qty),
        "custom_int2": str(1 if cycle == "annual" else 0),  # 1=annual 0=monthly
        "custom_str1": request.email,
        "custom_str2": request.company,
        "custom_str3": request.plan,
    }

    # Generate signature
    signature = generate_payfast_signature(data)
    # debug logging for signature issues
    print(f"[PayFast] signing data string: {data}")
    print(f"[PayFast] computed signature: {signature}")
    data["signature"] = signature

    # Strip empty-valued fields so the browser form never sends them
    clean = {k: v for k, v in data.items() if v is not None and str(v).strip() != ""}
    clean["signature"] = signature

    return {"form_fields": clean, "payfast_url": PAYFAST_URL, "payment_id": payment_id}


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
    qty = int(data.get("custom_int1", "1") or "1")
    is_annual = int(data.get("custom_int2", "0") or "0")
    duration_days = 365 if is_annual else 30
    cycle_label = "1 Year" if is_annual else "1 Month"

    if payment_status == "COMPLETE":
        # Payment successful — generate N licenses
        license_keys = []
        for _ in range(qty):
            license_key = generate_license_key()
            expires = datetime.now() + timedelta(days=duration_days)

            LICENSE_DATABASE[license_key] = {
                'key': license_key,
                'created_at': datetime.now().isoformat(),
                'expires': expires.isoformat(),
                'active': True,
                'customer_email': customer_email,
                'hardware_id': None,
                'duration_days': duration_days,
                'is_demo': False,
                'max_users': 1,
                'payment': {
                    'method': 'payfast',
                    'pf_payment_id': pf_payment_id,
                    'm_payment_id': m_payment_id,
                    'amount': amount_gross,
                    'quantity': qty,
                    'billing_cycle': 'annual' if is_annual else 'monthly',
                    'customer_name': f"{name_first} {name_last}".strip(),
                    'company': company,
                    'completed_at': datetime.now().isoformat()
                }
            }
            license_keys.append(license_key)

        save_database()
        print(f"[PayFast ITN] {qty} license(s) created for {customer_email}: {license_keys}")

        # Create portal user account if doesn't exist
        email_lower = customer_email.lower()
        if email_lower and email_lower not in PORTAL_USERS:
            # Create account with a temporary random password (user can reset via portal)
            temp_pw = secrets.token_hex(8)
            create_portal_user(email_lower, temp_pw, f"{name_first} {name_last}".strip(), company)
            print(f"[PayFast ITN] Portal account auto-created for {email_lower} (temp password)")

        # Send license email with all keys
        if SMTP_USER and customer_email:
            try:
                send_multi_license_email(customer_email, license_keys, duration_days, is_annual)
                print(f"[PayFast ITN] License email sent to {customer_email}")
            except Exception as e:
                print(f"[PayFast ITN] Email error: {e}")

    elif payment_status == "CANCELLED":
        print(f"[PayFast ITN] Payment cancelled: {m_payment_id}")
    else:
        print(f"[PayFast ITN] Status: {payment_status} for {m_payment_id}")

    return {"status": "ok"}


# ══════════════════════════════════════════════════════════════════
#   ROUTES - Portal Auth API (self-contained, no Supabase)
# ══════════════════════════════════════════════════════════════════

@app.post("/api/portal/auth/login")
async def portal_auth_login(request: Request):
    """Login with email/password, return session token."""
    try:
        body = await request.json()
    except Exception as e:
        print(f"[Portal] login parse error: {e}")
        raise HTTPException(400, "Malformed JSON")
    email = (body.get("email") or "").strip().lower()
    password = body.get("password") or ""
    print(f"[Portal] login attempt for {email}")
    if not email or not password:
        print(f"[Portal] login missing credentials")
        raise HTTPException(400, "Email and password required")
    user = verify_portal_login(email, password)
    if not user:
        print(f"[Portal] login failed for {email}")
        raise HTTPException(401, "Invalid email or password")
    if user.get("is_suspended"):
        print(f"[Portal] login suspended account {email}")
        raise HTTPException(403, "Account suspended. Contact support.")
    token = create_session(email)
    print(f"[Portal] login succeeded for {email}")
    return {"token": token, "user": {"email": user["email"], "full_name": user["full_name"], "company": user.get("company", "")}}


@app.post("/api/portal/auth/register")
async def portal_auth_register(request: Request):
    """Register a new portal account."""
    body = await request.json()
    email = (body.get("email") or "").strip().lower()
    password = body.get("password") or ""
    full_name = (body.get("full_name") or "").strip()
    company = (body.get("company") or "").strip()
    if not email or not password:
        raise HTTPException(400, "Email and password required")
    if len(password) < 6:
        raise HTTPException(400, "Password must be at least 6 characters")
    if email in PORTAL_USERS:
        raise HTTPException(409, "An account with this email already exists. Please sign in.")
    user = create_portal_user(email, password, full_name, company)
    token = create_session(email)
    return {"token": token, "user": {"email": user["email"], "full_name": user["full_name"], "company": user.get("company", "")}}


@app.post("/api/portal/auth/forgot-password")
async def portal_auth_forgot(request: Request):
    """Send a password reset email."""
    body = await request.json()
    email = (body.get("email") or "").strip().lower()
    if not email:
        raise HTTPException(400, "Email required")
    # Always return success (don't reveal if email exists)
    if email in PORTAL_USERS and SMTP_USER and SMTP_PASS:
        reset_token = secrets.token_urlsafe(32)
        PORTAL_RESET_TOKENS[reset_token] = {"email": email, "expires": (datetime.now() + timedelta(hours=1)).isoformat()}
        reset_url = f"{SITE_URL}/portal?reset_token={reset_token}"
        try:
            html = f"""
            <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;background:#0f172a;color:#e2e8f0;padding:40px;border-radius:12px;">
                <h1 style="color:#3b82f6;text-align:center;">Password Reset</h1>
                <p style="text-align:center;color:#94a3b8;">Click the link below to reset your password.</p>
                <div style="text-align:center;margin:30px 0;">
                    <a href="{reset_url}" style="background:linear-gradient(135deg,#2563eb,#7c3aed);color:#fff;padding:12px 32px;border-radius:8px;text-decoration:none;font-weight:bold;">Reset Password</a>
                </div>
                <p style="font-size:12px;color:#64748b;text-align:center;">This link expires in 1 hour. If you didn't request this, ignore this email.</p>
                <hr style="border:none;border-top:1px solid #334155;margin:24px 0;">
                <p style="font-size:12px;color:#64748b;text-align:center;">&copy; {datetime.now().year} {COMPANY_NAME}</p>
            </div>"""
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f'{COMPANY_NAME} - Password Reset'
            msg['From'] = f'{FROM_NAME} <{FROM_EMAIL}>'
            msg['To'] = email
            msg.attach(MIMEText(html, 'html'))
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
                server.starttls()
                server.login(SMTP_USER, SMTP_PASS)
                server.sendmail(FROM_EMAIL, email, msg.as_string())
            print(f"[Portal] Password reset email sent to {email}")
        except Exception as e:
            print(f"[Portal] Reset email error: {e}")
    return {"success": True, "message": "If that email has an account, a reset link has been sent."}


@app.post("/api/portal/auth/reset-password")
async def portal_auth_reset(request: Request):
    """Reset password using a reset token."""
    body = await request.json()
    token = body.get("reset_token") or ""
    new_password = body.get("password") or ""
    if not token or not new_password:
        raise HTTPException(400, "Reset token and new password required")
    if len(new_password) < 6:
        raise HTTPException(400, "Password must be at least 6 characters")
    reset_info = PORTAL_RESET_TOKENS.get(token)
    if not reset_info:
        raise HTTPException(400, "Invalid or expired reset link")
    if datetime.fromisoformat(reset_info["expires"]) < datetime.now():
        del PORTAL_RESET_TOKENS[token]
        raise HTTPException(400, "Reset link has expired. Please request a new one.")
    email = reset_info["email"]
    user = PORTAL_USERS.get(email)
    if not user:
        raise HTTPException(400, "Account not found")
    pw_hash, salt = _hash_password(new_password)
    user["password_hash"] = pw_hash
    user["salt"] = salt
    PORTAL_USERS[email] = user
    save_portal_users()
    del PORTAL_RESET_TOKENS[token]
    session_token = create_session(email)
    return {"success": True, "token": session_token, "message": "Password updated successfully!"}


@app.post("/api/portal/auth/change-password")
async def portal_auth_change_password(request: Request):
    """Change password for authenticated user."""
    user = await _get_portal_user(request)
    body = await request.json()
    new_password = body.get("password") or ""
    if len(new_password) < 6:
        raise HTTPException(400, "Password must be at least 6 characters")
    email = user["email"]
    portal_user = PORTAL_USERS.get(email)
    if not portal_user:
        raise HTTPException(400, "Account not found")
    pw_hash, salt = _hash_password(new_password)
    portal_user["password_hash"] = pw_hash
    portal_user["salt"] = salt
    PORTAL_USERS[email] = portal_user
    save_portal_users()
    return {"success": True, "message": "Password updated successfully!"}


async def _get_portal_user(request: Request) -> dict:
    """Get authenticated portal user from session token."""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(401, "Not authenticated")
    token = auth_header.split(" ")[1]
    user = get_session_user(token)
    if not user:
        raise HTTPException(401, "Session expired. Please sign in again.")
    return user


# ══════════════════════════════════════════════════════════════════
#   ROUTES - Customer Portal API
# ══════════════════════════════════════════════════════════════════

@app.get("/api/portal/me")
async def portal_me(request: Request):
    """Get current user profile and stats."""
    user = await _get_portal_user(request)
    email = user["email"]
    # Count licenses from JSON DB
    my_licenses = [lic for lic in LICENSE_DATABASE.values() if lic.get('customer_email', '').lower() == email]
    active_licenses = [lic for lic in my_licenses if lic.get('active')]
    has_trial = any(lic.get('is_demo') for lic in my_licenses)
    has_paid = any(not lic.get('is_demo') for lic in my_licenses)
    current_plan = "Trial" if has_trial and not has_paid else "Professional" if has_paid else None
    return {
        "customer": {
            "email": user["email"],
            "full_name": user.get("full_name", ""),
            "company": user.get("company", ""),
            "phone": user.get("phone", ""),
            "created_at": user.get("created_at", ""),
            "is_suspended": user.get("is_suspended", False),
        },
        "stats": {
            "total_licenses": len(my_licenses),
            "active_licenses": len(active_licenses),
            "current_plan": current_plan,
        }
    }


@app.put("/api/portal/profile")
async def portal_update_profile(request: Request):
    """Update customer profile (name, company, phone)."""
    user = await _get_portal_user(request)
    body = await request.json()
    if "full_name" in body: user["full_name"] = body["full_name"]
    if "company" in body: user["company"] = body["company"]
    if "phone" in body: user["phone"] = body["phone"]
    PORTAL_USERS[user["email"]] = user
    save_portal_users()
    return {"success": True}


@app.get("/api/portal/licenses")
async def portal_licenses(request: Request):
    """List customer's licenses from JSON database."""
    user = await _get_portal_user(request)
    email = user["email"]
    licenses = []
    for key, lic in LICENSE_DATABASE.items():
        if lic.get('customer_email', '').lower() == email:
            expires = lic.get('expires', '')
            is_expired = False
            try:
                is_expired = datetime.fromisoformat(expires) < datetime.now()
            except Exception:
                pass
            licenses.append({
                "license_key": key,
                "license_type": "trial" if lic.get('is_demo') else ("annual" if lic.get('duration_days', 0) >= 365 else "monthly"),
                "status": "expired" if is_expired else ("active" if lic.get('active') else "inactive"),
                "hardware_id": lic.get('hardware_id'),
                "duration_days": lic.get('duration_days', 0),
                "expires_at": expires,
                "created_at": lic.get('created_at', ''),
            })
    licenses.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    return {"licenses": licenses}


@app.post("/api/portal/link-license")
async def portal_link_license(request: Request):
    """Link an existing license key to this customer's portal account."""
    user = await _get_portal_user(request)
    body = await request.json()
    key = (body.get("license_key") or "").strip().upper()
    if key not in LICENSE_DATABASE:
        raise HTTPException(404, "License key not found")
    lic = LICENSE_DATABASE[key]
    if lic.get("customer_email", "").lower() != user["email"]:
        raise HTTPException(403, "This license belongs to a different email address")
    return {"success": True, "message": "License is already linked to your account"}


@app.get("/api/portal/subscription")
async def portal_subscription(request: Request):
    """Get current subscription info from license database."""
    user = await _get_portal_user(request)
    email = user["email"]
    my_licenses = [lic for lic in LICENSE_DATABASE.values() if lic.get('customer_email', '').lower() == email]
    # Get the latest license as the "subscription"
    subscription = None
    if my_licenses:
        latest = sorted(my_licenses, key=lambda x: x.get('created_at', ''), reverse=True)[0]
        is_trial = latest.get('is_demo', False)
        is_annual = latest.get('duration_days', 0) >= 365
        subscription = {
            "plan": "trial" if is_trial else "professional",
            "billing_cycle": "trial" if is_trial else ("annual" if is_annual else "monthly"),
            "status": "active" if latest.get('active') else "expired",
            "current_period_end": latest.get('expires', ''),
        }
    return {"subscription": subscription, "payments": []}


@app.post("/api/portal/subscribe")
async def portal_subscribe(request: Request):
    """Create PayFast checkout for subscription from the customer portal."""
    user = await _get_portal_user(request)
    body = await request.json()
    cycle = body.get("billing_cycle", "monthly")
    if cycle not in ("monthly", "annual"): cycle = "monthly"
    qty = max(1, min(100, body.get("quantity", 1)))
    price = 6800 if cycle == "annual" else 600
    total = price * qty
    payment_id = secrets.token_hex(8)
    cycle_label = "1 Year" if cycle == "annual" else "1 Month"
    item_name = f"Connexa Professional License x{qty} ({cycle_label})"
    item_desc = f"{qty} license(s), {cycle_label}, via Customer Portal"
    name_parts = (user.get("full_name") or "").split()
    # Order must match PayFast parameter spec: custom_int before custom_str
    data = {
        "merchant_id": PAYFAST_MERCHANT_ID,
        "merchant_key": PAYFAST_MERCHANT_KEY,
        "return_url": f"{SITE_URL}/portal?payment=success&id={payment_id}",
        "cancel_url": f"{SITE_URL}/portal?payment=cancelled",
        "notify_url": f"{SITE_URL}/api/payfast/notify",
        "name_first": name_parts[0] if name_parts else "",
        "name_last": " ".join(name_parts[1:]) if len(name_parts) > 1 else "",
        "email_address": user["email"],
        "m_payment_id": payment_id,
        "amount": f"{total:.2f}",
        "item_name": item_name[:100],
        "item_description": item_desc[:255],
        "custom_int1": str(qty),
        "custom_int2": str(1 if cycle == "annual" else 0),
        "custom_str1": user["email"],
        "custom_str2": user.get("company", ""),
        "custom_str3": "professional",
    }
    signature = generate_payfast_signature(data)
    # Strip empty-valued fields so browser form never sends them
    clean = {k: v for k, v in data.items() if v is not None and str(v).strip() != ""}
    clean["signature"] = signature
    return {"form_fields": clean, "payfast_url": PAYFAST_URL, "payment_id": payment_id}
async def portal_activate_trial(request: Request):
    """Activate a 7-day trial from the portal."""
    user = await _get_portal_user(request)
    email = user["email"]

    # Check for existing trial
    for key, lic in LICENSE_DATABASE.items():
        if lic.get('customer_email', '').lower() == email and lic.get('is_demo'):
            # Check if trial has expired
            expires_str = lic.get('expires', '')
            try:
                expires_dt = datetime.fromisoformat(expires_str)
                if expires_dt < datetime.now():
                    raise HTTPException(
                        status_code=400,
                        detail="Your 7-day trial has expired. Please subscribe to a professional license to continue using Connexa."
                    )
            except (ValueError, TypeError):
                pass
            # Trial still active — re-send the key
            if SMTP_USER:
                try:
                    send_trial_email(email, key, lic.get('expires', '')[:10])
                except Exception:
                    pass
            return {"success": True, "message": "You already have a trial license. Check your email.", "existing": True}

    # Generate new trial
    license_key = generate_license_key()
    expires = datetime.now() + timedelta(days=7)
    expires_date = expires.strftime('%Y-%m-%d')
    LICENSE_DATABASE[license_key] = {
        'key': license_key, 'created_at': datetime.now().isoformat(),
        'expires': expires.isoformat(), 'active': True,
        'customer_email': email, 'hardware_id': None, 'duration_days': 7,
        'is_demo': True, 'max_users': 1,
        'payment': {'method': 'trial', 'customer_name': user.get('full_name', ''), 'company': user.get('company', ''), 'completed_at': datetime.now().isoformat()}
    }
    save_database()
    if SMTP_USER:
        try:
            send_trial_email(email, license_key, expires_date)
        except Exception as e:
            print(f"[Portal Trial] Email error: {e}")
    return {"success": True, "message": "Trial license created and emailed!"}


@app.get("/api/admin/portal-users")
async def admin_portal_users(request: Request):
    """List all portal customers (admin only)."""
    token = request.query_params.get("token", "")
    if token != ADMIN_TOKEN:
        raise HTTPException(401, "Unauthorized")
    users = []
    for email, u in PORTAL_USERS.items():
        my_lics = [lic for lic in LICENSE_DATABASE.values() if lic.get('customer_email', '').lower() == email]
        users.append({
            "email": u["email"],
            "full_name": u.get("full_name", ""),
            "company": u.get("company", ""),
            "phone": u.get("phone", ""),
            "created_at": u.get("created_at", ""),
            "is_suspended": u.get("is_suspended", False),
            "license_count": len(my_lics),
        })
    users.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    return {"users": users}


@app.post("/api/admin/portal-user/toggle")
async def admin_toggle_portal_user(request: Request):
    """Suspend or unsuspend a portal customer (admin only)."""
    body = await request.json()
    if body.get("admin_token") != ADMIN_TOKEN:
        raise HTTPException(401, "Unauthorized")
    email = (body.get("email") or "").lower()
    action = body.get("action", "suspend")
    user = PORTAL_USERS.get(email)
    if not user:
        raise HTTPException(404, "User not found")
    user["is_suspended"] = (action == "suspend")
    PORTAL_USERS[email] = user
    save_portal_users()
    return {"success": True, "suspended": user["is_suspended"]}


@app.get("/api/admin/portal-user/licenses")
async def admin_portal_user_licenses(request: Request):
    """Get all licenses for a specific portal customer (admin only)."""
    token = request.query_params.get("token", "")
    if token != ADMIN_TOKEN:
        raise HTTPException(401, "Unauthorized")
    email = (request.query_params.get("email") or "").lower()
    if not email:
        raise HTTPException(400, "email required")
    licenses = []
    for key, lic in LICENSE_DATABASE.items():
        if lic.get('customer_email', '').lower() == email:
            licenses.append({
                "license_key": key,
                "license_type": "trial" if lic.get('is_demo') else ("annual" if lic.get('duration_days', 0) >= 365 else "monthly"),
                "status": "active" if lic.get('active') else "expired",
                "hardware_id": lic.get('hardware_id'),
                "expires_at": lic.get('expires', ''),
                "created_at": lic.get('created_at', ''),
            })
    return {"licenses": licenses}


# ── SMTP Settings Admin API ──

SMTP_SETTINGS_FILE = os.path.join(DATA_DIR, "smtp_settings.json")


def load_smtp_settings():
    """Load SMTP settings from file or return current defaults."""
    if os.path.exists(SMTP_SETTINGS_FILE):
        try:
            with open(SMTP_SETTINGS_FILE, 'r') as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "host": SMTP_HOST,
        "port": SMTP_PORT,
        "user": SMTP_USER,
        "password": SMTP_PASS,
        "from_email": FROM_EMAIL,
        "from_name": FROM_NAME,
    }


def save_smtp_settings(settings: dict):
    """Save SMTP settings to file and update runtime globals."""
    global SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, FROM_EMAIL, FROM_NAME
    with open(SMTP_SETTINGS_FILE, 'w') as f:
        json.dump(settings, f, indent=2)
    SMTP_HOST = settings.get("host", SMTP_HOST)
    SMTP_PORT = int(settings.get("port", SMTP_PORT))
    SMTP_USER = settings.get("user", SMTP_USER)
    SMTP_PASS = settings.get("password", SMTP_PASS)
    FROM_EMAIL = settings.get("from_email", FROM_EMAIL)
    FROM_NAME = settings.get("from_name", FROM_NAME)


# Apply saved SMTP settings on startup
if os.path.exists(SMTP_SETTINGS_FILE):
    _saved_smtp = load_smtp_settings()
    save_smtp_settings(_saved_smtp)
else:
    # First-time: create smtp_settings.json with correct defaults
    # This overrides any stale env vars (e.g. old render.yaml shipped smtp.gmail.com)
    save_smtp_settings({
        "host": "mail.connexify.co.za",
        "port": 587,
        "user": "admin@connexify.co.za",
        "password": "159951B@sh!",
        "from_email": "admin@connexify.co.za",
        "from_name": "Connexify",
    })
    print("[SMTP] Created smtp_settings.json with correct Connexify defaults")


@app.get("/api/admin/smtp-settings")
async def admin_get_smtp(request: Request):
    """Get current SMTP settings (admin only)."""
    token = request.query_params.get("token", "")
    if token != ADMIN_TOKEN:
        raise HTTPException(401, "Unauthorized")
    settings = load_smtp_settings()
    # Mask password for display
    masked = {**settings, "password": "••••••••" if settings.get("password") else ""}
    return {"settings": masked}


@app.post("/api/admin/smtp-settings")
async def admin_update_smtp(request: Request):
    """Update SMTP settings (admin only)."""
    body = await request.json()
    if body.get("admin_token") != ADMIN_TOKEN:
        raise HTTPException(401, "Unauthorized")
    current = load_smtp_settings()
    new_settings = {
        "host": body.get("host", current["host"]),
        "port": int(body.get("port", current["port"])),
        "user": body.get("user", current["user"]),
        "password": body.get("password", current["password"]) if body.get("password") and body["password"] != "••••••••" else current["password"],
        "from_email": body.get("from_email", current["from_email"]),
        "from_name": body.get("from_name", current["from_name"]),
    }
    save_smtp_settings(new_settings)
    return {"success": True, "message": "SMTP settings updated"}


@app.post("/api/admin/smtp-test")
async def admin_test_smtp(request: Request):
    """Send a test email using current SMTP settings (admin only)."""
    body = await request.json()
    if body.get("admin_token") != ADMIN_TOKEN:
        raise HTTPException(401, "Unauthorized")
    test_email = body.get("email", SUPPORT_EMAIL)
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f'SMTP Test - {COMPANY_NAME} License Server'
        msg['From'] = f'{FROM_NAME} <{FROM_EMAIL}>'
        msg['To'] = test_email
        msg.attach(MIMEText(f'<div style="font-family:Arial;padding:20px;"><h2>SMTP Test Successful!</h2><p>This email confirms your SMTP settings are working correctly.</p><p>Server: {SMTP_HOST}:{SMTP_PORT}</p><p>From: {FROM_EMAIL}</p></div>', 'html'))
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(FROM_EMAIL, test_email, msg.as_string())
        return {"success": True, "message": f"Test email sent to {test_email}"}
    except Exception as e:
        return {"success": False, "message": f"SMTP error: {str(e)}"}


# ── Admin User Management API ──

ADMINS_FILE = os.path.join(DATA_DIR, "admin_users.json")


def load_admin_users():
    """Load admin users from file."""
    if os.path.exists(ADMINS_FILE):
        try:
            with open(ADMINS_FILE, 'r') as f:
                return json.load(f)
        except Exception:
            pass
    return [{"id": "1", "email": SUPPORT_EMAIL, "name": "Primary Admin", "role": "super", "created_at": datetime.now().isoformat()}]


def save_admin_users(users: list):
    """Save admin users to file."""
    with open(ADMINS_FILE, 'w') as f:
        json.dump(users, f, indent=2)


@app.get("/api/admin/admins")
async def admin_list_admins(request: Request):
    """List all admin users."""
    token = request.query_params.get("token", "")
    if token != ADMIN_TOKEN:
        raise HTTPException(401, "Unauthorized")
    return {"admins": load_admin_users()}


@app.post("/api/admin/admins/add")
async def admin_add_admin(request: Request):
    """Add a new admin user."""
    body = await request.json()
    if body.get("admin_token") != ADMIN_TOKEN:
        raise HTTPException(401, "Unauthorized")
    admins = load_admin_users()
    new_admin = {
        "id": str(len(admins) + 1),
        "email": body.get("email", ""),
        "name": body.get("name", ""),
        "role": body.get("role", "admin"),
        "created_at": datetime.now().isoformat()
    }
    if not new_admin["email"]:
        raise HTTPException(400, "Email is required")
    # Check for duplicate
    if any(a["email"].lower() == new_admin["email"].lower() for a in admins):
        raise HTTPException(400, "Admin with this email already exists")
    admins.append(new_admin)
    save_admin_users(admins)
    return {"success": True, "admin": new_admin}


@app.post("/api/admin/admins/remove")
async def admin_remove_admin(request: Request):
    """Remove an admin user (cannot remove super admin)."""
    body = await request.json()
    if body.get("admin_token") != ADMIN_TOKEN:
        raise HTTPException(401, "Unauthorized")
    admin_id = body.get("admin_id", "")
    admins = load_admin_users()
    admin_to_remove = next((a for a in admins if a["id"] == admin_id), None)
    if not admin_to_remove:
        raise HTTPException(404, "Admin not found")
    if admin_to_remove.get("role") == "super":
        raise HTTPException(400, "Cannot remove the primary super admin")
    admins = [a for a in admins if a["id"] != admin_id]
    save_admin_users(admins)
    return {"success": True}


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


# Serve static files for downloads (DEB / EXE / logos)
# Use persistent disk on Render, /tmp on Cloud Run, or ./static locally
STATIC_DIR = Path(os.path.join(DATA_DIR, "static"))
STATIC_DIR.mkdir(parents=True, exist_ok=True)

# copy any files bundled in the repo's static/ directory into the storage folder
import shutil
BUILTIN_STATIC = Path(__file__).parent / "static"
if BUILTIN_STATIC.exists():
    for child in BUILTIN_STATIC.iterdir():
        target = STATIC_DIR / child.name
        if not target.exists():
            try:
                shutil.copy(child, target)
            except Exception:
                pass

# ── Download route for large installer files (GCS signed URL redirect) ──
# Must be registered BEFORE the StaticFiles catch-all mount.

@app.get("/static/{filename:path}")
@app.head("/static/{filename:path}")
async def serve_static_file(filename: str):
    """Serve static files.  Large installers redirect to a GCS signed URL
    so we avoid buffering 100+ MB through this Cloud Run instance."""
    large_extensions = ('.deb', '.exe', '.AppImage', '.dmg', '.zip')
    local_path = STATIC_DIR / filename

    # For large installer files, generate a GCS signed URL and redirect
    if store.using_gcs() and filename.endswith(large_extensions):
        try:
            import google.auth
            from google.auth.transport import requests as gauth_requests

            bucket = store._get_bucket()
            blob = bucket.blob(f"static/{filename}")
            if blob.exists():
                credentials, project = google.auth.default()
                if hasattr(credentials, 'refresh'):
                    credentials.refresh(gauth_requests.Request())

                sa_email = getattr(credentials, 'service_account_email', None)
                token = getattr(credentials, 'token', None)

                if sa_email and token:
                    # Cloud Run: sign via IAM Credentials API
                    url = blob.generate_signed_url(
                        version="v4",
                        expiration=timedelta(hours=1),
                        method="GET",
                        service_account_email=sa_email,
                        access_token=token,
                    )
                else:
                    # Local / key-based credentials
                    url = blob.generate_signed_url(
                        version="v4",
                        expiration=timedelta(hours=1),
                        method="GET",
                    )
                print(f"[Static] Redirecting {filename} to signed GCS URL")
                return RedirectResponse(url=url, status_code=302)
        except Exception as e:
            print(f"[Static] Signed URL error for {filename}: {e}")
            # Fall through to local file serving

    # Small files or non-GCS: serve from local filesystem
    if local_path.exists() and local_path.is_file():
        return FileResponse(str(local_path), filename=filename)

    raise HTTPException(status_code=404, detail="File not found")


from fastapi.staticfiles import StaticFiles
# Note: the explicit /static/{filename} route above takes priority for matched paths.
# This mount catches anything the route doesn't handle.
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


# ══════════════════════════════════════════════════════════════════
#   ROUTES - Health / Status
# ══════════════════════════════════════════════════════════════════

@app.get("/api/health")
async def health_check():
    """Health check for Cloud Run / load balancer probes."""
    return {
        "status": "healthy",
        "version": CURRENT_VERSION,
        "storage_backend": "gcs" if store.using_gcs() else "local",
        "gcs_bucket": store.GCS_BUCKET or None,
        "licenses_loaded": len(LICENSE_DATABASE),
        "portal_users": len(PORTAL_USERS),
    }


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
    """Upload installer files (DEB/EXE) via admin API – saves to GCS + local"""
    if admin_token != ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    allowed_ext = ('.deb', '.exe', '.AppImage', '.dmg', '.zip', '.png', '.jpg', '.jpeg', '.svg', '.ico', '.gif', '.webp')
    if not any(file.filename.endswith(ext) for ext in allowed_ext):
        raise HTTPException(status_code=400, detail=f"Only installer/image files allowed: {allowed_ext}")
    
    contents = await file.read()
    store.save_file(str(STATIC_DIR), file.filename, contents)
    
    size_mb = len(contents) / (1024 * 1024)
    return {"success": True, "filename": file.filename, "size_mb": round(size_mb, 2)}


@app.get("/api/admin/list-files")
async def list_files(admin_token: str = ""):
    """List uploaded installer files (from GCS + local)"""
    if admin_token != ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    files = store.list_files(str(STATIC_DIR))
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
#   SOCIAL MEDIA MANAGEMENT
# ══════════════════════════════════════════════════════════════════

SOCIAL_POSTS_FILE = os.path.join(DATA_DIR, "social_posts.json")
SOCIAL_ACCOUNTS_FILE = os.path.join(DATA_DIR, "social_accounts.json")
SOCIAL_POSTS: list = []
SOCIAL_ACCOUNTS: list = []


def load_social_posts():
    global SOCIAL_POSTS
    try:
        data = store.load_json(SOCIAL_POSTS_FILE)
        if isinstance(data, dict) and "posts" in data:
            SOCIAL_POSTS = data["posts"]
        elif isinstance(data, list):
            SOCIAL_POSTS = data
        else:
            SOCIAL_POSTS = []
        print(f"[Social] Loaded {len(SOCIAL_POSTS)} posts")
    except Exception as e:
        print(f"[Social] Error loading posts: {e}")
        SOCIAL_POSTS = []


def save_social_posts():
    store.save_json(SOCIAL_POSTS_FILE, {"posts": SOCIAL_POSTS})


def load_social_accounts():
    global SOCIAL_ACCOUNTS
    try:
        data = store.load_json(SOCIAL_ACCOUNTS_FILE)
        if isinstance(data, dict) and "accounts" in data:
            SOCIAL_ACCOUNTS = data["accounts"]
        elif isinstance(data, list):
            SOCIAL_ACCOUNTS = data
        else:
            SOCIAL_ACCOUNTS = []
        print(f"[Social] Loaded {len(SOCIAL_ACCOUNTS)} accounts")
    except Exception as e:
        print(f"[Social] Error loading accounts: {e}")
        SOCIAL_ACCOUNTS = []


def save_social_accounts():
    store.save_json(SOCIAL_ACCOUNTS_FILE, {"accounts": SOCIAL_ACCOUNTS})


# ── Social Posts CRUD ──

@app.get("/api/admin/social/posts")
async def list_social_posts(admin_token: str = "", token: str = ""):
    tok = admin_token or token
    if tok != ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="Unauthorized")
    return {"posts": SOCIAL_POSTS}


@app.post("/api/admin/social/posts")
async def create_social_post(request: Request):
    body = await request.json()
    if body.get("admin_token") != ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="Unauthorized")
    post = {
        "id": secrets.token_hex(8),
        "content": body.get("content", ""),
        "platforms": body.get("platforms", []),
        "scheduled_date": body.get("scheduled_date", ""),
        "scheduled_time": body.get("scheduled_time", "09:00"),
        "status": body.get("status", "draft"),
        "image_url": body.get("image_url", ""),
        "hashtags": body.get("hashtags", ""),
        "campaign": body.get("campaign", ""),
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
    }
    SOCIAL_POSTS.append(post)
    save_social_posts()
    return {"success": True, "post": post}


@app.post("/api/admin/social/posts/edit")
async def edit_social_post(request: Request):
    body = await request.json()
    if body.get("admin_token") != ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="Unauthorized")
    post_id = body.get("post_id")
    post = next((p for p in SOCIAL_POSTS if p["id"] == post_id), None)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    for field in ["content", "platforms", "scheduled_date", "scheduled_time",
                   "status", "image_url", "hashtags", "campaign"]:
        if field in body:
            post[field] = body[field]
    post["updated_at"] = datetime.now().isoformat()
    save_social_posts()
    return {"success": True, "post": post}


@app.post("/api/admin/social/posts/delete")
async def delete_social_post(request: Request):
    body = await request.json()
    if body.get("admin_token") != ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="Unauthorized")
    post_id = body.get("post_id")
    global SOCIAL_POSTS
    SOCIAL_POSTS = [p for p in SOCIAL_POSTS if p["id"] != post_id]
    save_social_posts()
    return {"success": True}


@app.post("/api/admin/social/posts/duplicate")
async def duplicate_social_post(request: Request):
    body = await request.json()
    if body.get("admin_token") != ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="Unauthorized")
    post_id = body.get("post_id")
    original = next((p for p in SOCIAL_POSTS if p["id"] == post_id), None)
    if not original:
        raise HTTPException(status_code=404, detail="Post not found")
    new_post = {**original}
    new_post["id"] = secrets.token_hex(8)
    new_post["status"] = "draft"
    new_post["created_at"] = datetime.now().isoformat()
    new_post["updated_at"] = datetime.now().isoformat()
    SOCIAL_POSTS.append(new_post)
    save_social_posts()
    return {"success": True, "post": new_post}


@app.post("/api/admin/social/posts/bulk-schedule")
async def bulk_schedule_posts(request: Request):
    """Schedule multiple posts with a recurring interval."""
    body = await request.json()
    if body.get("admin_token") != ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="Unauthorized")
    post_ids = body.get("post_ids", [])
    start_date = body.get("start_date", "")
    interval_days = int(body.get("interval_days", 3))
    time_of_day = body.get("time", "09:00")

    if not start_date or not post_ids:
        raise HTTPException(status_code=400, detail="start_date and post_ids required")

    from datetime import date as dt_date
    current = datetime.fromisoformat(start_date).date()
    scheduled = 0
    for pid in post_ids:
        post = next((p for p in SOCIAL_POSTS if p["id"] == pid), None)
        if post:
            post["scheduled_date"] = current.isoformat()
            post["scheduled_time"] = time_of_day
            post["status"] = "scheduled"
            post["updated_at"] = datetime.now().isoformat()
            current += timedelta(days=interval_days)
            scheduled += 1
    save_social_posts()
    return {"success": True, "scheduled": scheduled}


@app.post("/api/admin/social/posts/import-csv")
async def import_social_csv(request: Request):
    """Import posts from CSV data. Expects JSON body with csv_rows array."""
    body = await request.json()
    if body.get("admin_token") != ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="Unauthorized")
    rows = body.get("csv_rows", [])
    imported = 0
    for row in rows:
        post = {
            "id": secrets.token_hex(8),
            "content": row.get("content", row.get("text", "")),
            "platforms": [p.strip() for p in row.get("platforms", "").split(",") if p.strip()] if isinstance(row.get("platforms"), str) else row.get("platforms", []),
            "scheduled_date": row.get("scheduled_date", row.get("date", "")),
            "scheduled_time": row.get("scheduled_time", row.get("time", "09:00")),
            "status": row.get("status", "draft"),
            "image_url": row.get("image_url", ""),
            "hashtags": row.get("hashtags", ""),
            "campaign": row.get("campaign", ""),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }
        SOCIAL_POSTS.append(post)
        imported += 1
    save_social_posts()
    return {"success": True, "imported": imported}


@app.post("/api/admin/social/posts/mark-published")
async def mark_post_published(request: Request):
    body = await request.json()
    if body.get("admin_token") != ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="Unauthorized")
    post_id = body.get("post_id")
    post = next((p for p in SOCIAL_POSTS if p["id"] == post_id), None)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    post["status"] = "published"
    post["published_at"] = datetime.now().isoformat()
    post["updated_at"] = datetime.now().isoformat()
    save_social_posts()
    return {"success": True, "post": post}


# ── Social Accounts CRUD ──

@app.get("/api/admin/social/accounts")
async def list_social_accounts(admin_token: str = "", token: str = ""):
    tok = admin_token or token
    if tok != ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="Unauthorized")
    # Strip sensitive keys from response
    safe = []
    for acc in SOCIAL_ACCOUNTS:
        a = {**acc}
        if "api_secret" in a:
            a["api_secret"] = "••••" + a["api_secret"][-4:] if len(a.get("api_secret", "")) > 4 else "••••"
        if "access_token_secret" in a:
            a["access_token_secret"] = "••••"
        safe.append(a)
    return {"accounts": safe}


@app.post("/api/admin/social/accounts")
async def save_social_account(request: Request):
    body = await request.json()
    if body.get("admin_token") != ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="Unauthorized")
    account = {
        "id": body.get("id") or secrets.token_hex(8),
        "platform": body.get("platform", ""),
        "account_name": body.get("account_name", ""),
        "api_key": body.get("api_key", ""),
        "api_secret": body.get("api_secret", ""),
        "access_token": body.get("access_token", ""),
        "access_token_secret": body.get("access_token_secret", ""),
        "page_id": body.get("page_id", ""),
        "enabled": body.get("enabled", True),
        "updated_at": datetime.now().isoformat(),
    }
    # Update existing or add new
    global SOCIAL_ACCOUNTS
    existing = next((i for i, a in enumerate(SOCIAL_ACCOUNTS) if a["id"] == account["id"]), None)
    if existing is not None:
        # Preserve secrets if not changed
        old = SOCIAL_ACCOUNTS[existing]
        if account["api_secret"].startswith("••••"):
            account["api_secret"] = old.get("api_secret", "")
        if account["access_token_secret"] == "••••":
            account["access_token_secret"] = old.get("access_token_secret", "")
        SOCIAL_ACCOUNTS[existing] = account
    else:
        account["created_at"] = datetime.now().isoformat()
        SOCIAL_ACCOUNTS.append(account)
    save_social_accounts()
    return {"success": True, "account": {"id": account["id"], "platform": account["platform"]}}


@app.post("/api/admin/social/accounts/delete")
async def delete_social_account(request: Request):
    body = await request.json()
    if body.get("admin_token") != ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="Unauthorized")
    acc_id = body.get("account_id")
    global SOCIAL_ACCOUNTS
    SOCIAL_ACCOUNTS = [a for a in SOCIAL_ACCOUNTS if a["id"] != acc_id]
    save_social_accounts()
    return {"success": True}


# ── Social Stats ──

@app.get("/api/admin/social/stats")
async def social_stats(admin_token: str = "", token: str = ""):
    tok = admin_token or token
    if tok != ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="Unauthorized")
    total = len(SOCIAL_POSTS)
    draft = sum(1 for p in SOCIAL_POSTS if p.get("status") == "draft")
    scheduled = sum(1 for p in SOCIAL_POSTS if p.get("status") == "scheduled")
    published = sum(1 for p in SOCIAL_POSTS if p.get("status") == "published")
    accounts = len([a for a in SOCIAL_ACCOUNTS if a.get("enabled", True)])
    return {
        "total_posts": total,
        "draft": draft,
        "scheduled": scheduled,
        "published": published,
        "active_accounts": accounts,
    }


# ══════════════════════════════════════════════════════════════════
#   SOCIAL MEDIA AUTOMATION ENGINE
# ══════════════════════════════════════════════════════════════════

AUTOMATION_CONFIG_FILE = os.path.join(DATA_DIR, "social_automation.json")
AUTOMATION_LOG_FILE = os.path.join(DATA_DIR, "automation_log.json")

# SA ISP/FNO target audience content library
SA_ISP_CONTENT_LIBRARY = {
    "product_highlights": [
        "Network downtime costing your ISP revenue? Connexa gives you real-time alerts before your customers even notice. #NetworkMonitoring #SouthAfricaISP",
        "Managing hundreds of CPEs across your fibre network? Connexa auto-discovers and monitors every device. No manual setup needed. #FibreNetwork #FTTH",
        "Your NOC team deserves better tools. Connexa provides unified monitoring for Mikrotik, Ubiquiti, Cambium & more — all in one dashboard. #NOC #ISPTools",
        "Connexa monitors your entire network stack — from core routers to last-mile CPEs. Built for South African ISPs who demand uptime. #NetworkOps",
        "Stop fighting with multiple monitoring tools. Connexa unifies SNMP, API polling & syslog into one clean interface. #NetworkManagement",
        "Fibre rollouts growing faster than your monitoring can keep up? Connexa scales from 100 to 100,000 devices seamlessly. #FibreISP #Scalability",
        "Bandwidth monitoring, traffic analysis, and alerting — Connexa does it all without the enterprise price tag. #AffordableNMS",
        "Your customers expect 99.9% uptime. Connexa helps you deliver it with predictive monitoring and smart alerting. #ISPExcellence",
    ],
    "industry_insights": [
        "South Africa's fibre-to-the-home market is growing 30%+ year-on-year. Is your monitoring infrastructure ready to scale? #FTTH #SAFibre",
        "Load shedding affects network uptime across SA. Smart UPS monitoring integrated into Connexa helps you stay ahead. #LoadShedding #NetworkResilience",
        "FNOs rolling out to new suburbs need real-time visibility. Connexa's auto-discovery means your NOC sees new sites instantly. #FNO #NetworkExpansion",
        "The days of SSH-ing into routers one by one are over. Modern ISPs need centralised monitoring. That's Connexa. #ModernISP",
        "According to industry data, 60% of ISP customer churn is caused by repeated connectivity issues. Proactive monitoring reduces churn. #CustomerRetention",
        "South African ISPs serving rural areas face unique challenges — long backhaul links, power instability, remote sites. Connexa handles all of it. #RuralConnectivity",
        "Multi-vendor networks are the reality for SA ISPs. Connexa speaks Mikrotik, Ubiquiti, Cambium, Huawei, and Cisco natively. #MultiVendor",
    ],
    "case_studies": [
        "A Western Cape ISP reduced their mean-time-to-repair by 45% after deploying Connexa. Faster detection = faster resolution. #MTTR #CaseStudy",
        "One of our Gauteng ISP customers monitors 5,000+ CPEs with Connexa — and their NOC team is just 3 people. #Efficiency #ISP",
        "A KZN fibre operator cut their truck rolls by 30% using Connexa's remote diagnostics. Less windscreen time, more uptime. #FibreOps",
        "After deploying Connexa, a small-town ISP went from reactive firefighting to proactive monitoring. Customer complaints dropped 50%. #ProactiveMonitoring",
    ],
    "tips_and_education": [
        "ISP tip: Set up tiered alerting in Connexa — critical alerts go to SMS, warnings to email, info to Slack. Don't wake your team for non-issues. #ISPTips",
        "Best practice: Monitor your backhaul links separately from access networks. Connexa's network grouping makes this easy. #NetworkBestPractice",
        "Pro tip: Use Connexa's bandwidth trending to plan capacity upgrades before your links hit 80%. Prevention > firefighting. #CapacityPlanning",
        "Monitoring tip: Track packet loss and jitter on voice circuits separately. Connexa's SLA monitoring feature handles this automatically. #VoIP #QoS",
        "Don't just monitor uptime — monitor performance. A link that's 'up' but at 99% utilisation is about to become a problem. #PerformanceMonitoring",
    ],
    "announcements": [
        "Connexa v5.2.8 is live! New features include enhanced wireless monitoring, improved dashboard performance, and multi-vendor support. Download now at connexify.co.za #Connexa #Update",
        "We're proudly South African, building network monitoring tools designed for African ISPs and FNOs. 🇿🇦 #ProudlySA #MadeInSA",
        "Free trial available — experience Connexa's full network monitoring suite with no commitment. Visit connexify.co.za to get started. #FreeTrial",
        "Connexa now supports SNMP v3 with full encryption for security-conscious ISPs. Upgrade today. #Security #SNMPv3",
    ],
}

SA_ISP_HASHTAGS = [
    "#SouthAfricaISP", "#SAFibre", "#FTTH", "#NetworkMonitoring", "#ISP",
    "#FNO", "#Connexa", "#NetworkManagement", "#FibreNetwork", "#NOC",
    "#MadeInSA", "#AfricanTech", "#TechSA", "#ISPTools", "#NetworkOps",
    "#Mikrotik", "#Ubiquiti", "#Cambium", "#ProudlySA", "#DigitalSA",
]

SA_ISP_TARGET_HANDLES = {
    "twitter": [
        "@Vumatel", "@OpenserveZA", "@MetroFibre", "@DFA_Africa",
        "@Frogfoot_Net", "@OctotelFibre", "@LinkAfricaZA",
        "@ABORSSA", "@MwebSA", "@WebafrSA", "@CoolIdeasZA",
    ],
    "linkedin": [
        "Vumatel", "Openserve", "MetroFibre Networx", "DFA",
        "Frogfoot Networks", "Octotel", "Link Africa",
        "ISPA South Africa", "Internet Solutions", "Liquid Intelligent Technologies",
    ],
}

# Default automation settings
DEFAULT_AUTOMATION_CONFIG = {
    "enabled": False,
    "platforms": ["twitter", "linkedin"],
    "posting_schedule": {
        "min_hours_between_posts": 8,     # Minimum gap between posts (anti-spam)
        "max_posts_per_day": 2,           # Hard cap per platform per day
        "max_posts_per_week": 8,          # Weekly cap per platform
        "posting_windows": [              # Only post during business/engagement hours (SAST)
            {"start": "07:00", "end": "09:00"},   # Morning commute
            {"start": "12:00", "end": "13:00"},   # Lunch break
            {"start": "17:00", "end": "19:00"},   # After work
        ],
        "excluded_days": [6],             # 0=Mon, 6=Sun — skip Sundays
        "timezone_offset": 2,             # SAST = UTC+2
    },
    "content_mix": {
        "product_highlights": 30,
        "industry_insights": 25,
        "tips_and_education": 20,
        "case_studies": 15,
        "announcements": 10,
    },
    "anti_spam": {
        "min_content_variation": 0.6,     # Minimum difference ratio between consecutive posts
        "max_hashtags_per_post": 4,       # Don't overload hashtags
        "cooldown_after_burst": 24,       # Hours cooldown if 3+ posts in 12h window
        "no_duplicate_content_days": 30,  # Don't repeat exact content within N days
        "mention_frequency": 5,           # Only @mention targets every Nth post
        "max_mentions_per_post": 1,       # Max @mentions per post
    },
    "campaign_name": "Connexa SA ISP Outreach",
    "last_run": None,
    "total_generated": 0,
    "total_published": 0,
}


def load_automation_config():
    try:
        data = store.load_json(AUTOMATION_CONFIG_FILE)
        if data:
            # Merge with defaults so new fields are always present
            merged = {**DEFAULT_AUTOMATION_CONFIG}
            merged.update(data)
            merged["posting_schedule"] = {**DEFAULT_AUTOMATION_CONFIG["posting_schedule"], **data.get("posting_schedule", {})}
            merged["content_mix"] = {**DEFAULT_AUTOMATION_CONFIG["content_mix"], **data.get("content_mix", {})}
            merged["anti_spam"] = {**DEFAULT_AUTOMATION_CONFIG["anti_spam"], **data.get("anti_spam", {})}
            return merged
    except Exception as e:
        print(f"[Automation] Error loading config: {e}")
    return {**DEFAULT_AUTOMATION_CONFIG}


def save_automation_config(config):
    store.save_json(AUTOMATION_CONFIG_FILE, config)


def load_automation_log():
    try:
        data = store.load_json(AUTOMATION_LOG_FILE)
        if isinstance(data, dict) and "entries" in data:
            return data["entries"]
        if isinstance(data, list):
            return data
    except Exception:
        pass
    return []


def save_automation_log(entries):
    # Keep only last 500 entries
    store.save_json(AUTOMATION_LOG_FILE, {"entries": entries[-500:]})


def _get_recent_post_content(days=30):
    """Get content of posts from the last N days to avoid duplicates."""
    cutoff = (datetime.now() - timedelta(days=days)).isoformat()
    return [
        p.get("content", "").lower().strip()
        for p in SOCIAL_POSTS
        if p.get("created_at", "") >= cutoff and p.get("content")
    ]


def _content_similarity(a: str, b: str) -> float:
    """Simple word-overlap similarity ratio between two strings."""
    words_a = set(a.lower().split())
    words_b = set(b.lower().split())
    if not words_a or not words_b:
        return 0.0
    intersection = words_a & words_b
    union = words_a | words_b
    return len(intersection) / len(union) if union else 0.0


def _count_posts_in_window(hours=24, platform=None):
    """Count posts created/scheduled in the last N hours for rate limiting."""
    cutoff = (datetime.now() - timedelta(hours=hours)).isoformat()
    count = 0
    for p in SOCIAL_POSTS:
        created = p.get("created_at", "")
        if created >= cutoff:
            if platform is None or platform in p.get("platforms", []):
                count += 1
    return count


def _is_in_posting_window(config):
    """Check if current time is within allowed posting windows (SAST)."""
    tz_offset = config.get("posting_schedule", {}).get("timezone_offset", 2)
    now = datetime.utcnow() + timedelta(hours=tz_offset)
    current_time = now.strftime("%H:%M")
    current_day = now.weekday()  # 0=Mon

    excluded = config.get("posting_schedule", {}).get("excluded_days", [])
    if current_day in excluded:
        return False

    windows = config.get("posting_schedule", {}).get("posting_windows", [])
    for w in windows:
        if w["start"] <= current_time <= w["end"]:
            return True
    return False


def generate_automated_post(config, platform="twitter"):
    """Generate a single post with anti-spam protections."""
    anti_spam = config.get("anti_spam", {})
    content_mix = config.get("content_mix", {})

    # Check rate limits
    sched = config.get("posting_schedule", {})
    daily_count = _count_posts_in_window(24, platform)
    if daily_count >= sched.get("max_posts_per_day", 2):
        return None, "Daily post limit reached"

    weekly_count = _count_posts_in_window(168, platform)
    if weekly_count >= sched.get("max_posts_per_week", 8):
        return None, "Weekly post limit reached"

    # Cooldown check: if 3+ posts in last 12h, enforce cooldown
    recent_12h = _count_posts_in_window(12, platform)
    cooldown_hours = anti_spam.get("cooldown_after_burst", 24)
    if recent_12h >= 3:
        last_post_time = None
        for p in sorted(SOCIAL_POSTS, key=lambda x: x.get("created_at", ""), reverse=True):
            if platform in p.get("platforms", []):
                last_post_time = p.get("created_at", "")
                break
        if last_post_time:
            hours_since = (datetime.now() - datetime.fromisoformat(last_post_time)).total_seconds() / 3600
            if hours_since < cooldown_hours:
                return None, f"Cooldown active ({cooldown_hours - hours_since:.1f}h remaining)"

    # Minimum gap between posts
    min_gap = sched.get("min_hours_between_posts", 8)
    last_auto = None
    for p in sorted(SOCIAL_POSTS, key=lambda x: x.get("created_at", ""), reverse=True):
        if p.get("auto_generated") and platform in p.get("platforms", []):
            last_auto = p.get("created_at", "")
            break
    if last_auto:
        hours_since = (datetime.now() - datetime.fromisoformat(last_auto)).total_seconds() / 3600
        if hours_since < min_gap:
            return None, f"Min gap not met ({min_gap - hours_since:.1f}h remaining)"

    # Select content category based on weighted mix
    categories = list(content_mix.keys())
    weights = [content_mix.get(c, 10) for c in categories]
    total_w = sum(weights)
    weights = [w / total_w for w in weights]
    category = random.choices(categories, weights=weights, k=1)[0]

    # Get available content for that category
    pool = SA_ISP_CONTENT_LIBRARY.get(category, [])
    if not pool:
        return None, f"No content in category {category}"

    # Filter out recently used content
    recent_content = _get_recent_post_content(anti_spam.get("no_duplicate_content_days", 30))
    available = [c for c in pool if c.lower().strip() not in recent_content]
    if not available:
        # All content used recently — pick from full pool but ensure variation
        available = pool

    # Pick content and ensure it's different enough from last post
    random.shuffle(available)
    min_variation = anti_spam.get("min_content_variation", 0.6)
    chosen = None
    for candidate in available:
        if recent_content:
            similarity = max(_content_similarity(candidate, rc) for rc in recent_content[-5:])
            if similarity < (1.0 - min_variation):
                chosen = candidate
                break
        else:
            chosen = candidate
            break
    if not chosen:
        chosen = available[0]  # Fallback

    # Add hashtags (limited)
    max_tags = anti_spam.get("max_hashtags_per_post", 4)
    # Extract existing hashtags from content
    existing_tags = [w for w in chosen.split() if w.startswith("#")]
    if len(existing_tags) < max_tags:
        extra_needed = max_tags - len(existing_tags)
        extra_pool = [t for t in SA_ISP_HASHTAGS if t not in chosen]
        extra = random.sample(extra_pool, min(extra_needed, len(extra_pool)))
        if extra:
            chosen = chosen.rstrip() + " " + " ".join(extra)

    # Occasionally @mention a target (controlled frequency)
    mention_freq = anti_spam.get("mention_frequency", 5)
    total_auto = sum(1 for p in SOCIAL_POSTS if p.get("auto_generated"))
    if total_auto % mention_freq == 0 and total_auto > 0:
        handles = SA_ISP_TARGET_HANDLES.get(platform, [])
        if handles:
            max_mentions = anti_spam.get("max_mentions_per_post", 1)
            mentions = random.sample(handles, min(max_mentions, len(handles)))
            chosen = chosen.rstrip() + " " + " ".join(mentions)

    # Respect character limits
    if platform == "twitter" and len(chosen) > 280:
        # Trim hashtags to fit
        words = chosen.split()
        while len(" ".join(words)) > 280 and words:
            if words[-1].startswith("#") or words[-1].startswith("@"):
                words.pop()
            else:
                break
        chosen = " ".join(words)

    return {
        "content": chosen,
        "category": category,
        "platform": platform,
    }, None


async def run_automation_cycle():
    """Background task: check if automation should create posts."""
    config = load_automation_config()
    if not config.get("enabled"):
        return

    if not _is_in_posting_window(config):
        return

    log_entries = load_automation_log()
    platforms = config.get("platforms", ["twitter", "linkedin"])
    generated_count = 0

    for platform in platforms:
        # Check if we have an account for this platform
        has_account = any(
            a.get("platform") == platform and a.get("enabled", True)
            for a in SOCIAL_ACCOUNTS
        )

        result, reason = generate_automated_post(config, platform)
        if not result:
            log_entries.append({
                "timestamp": datetime.now().isoformat(),
                "platform": platform,
                "action": "skipped",
                "reason": reason,
            })
            continue

        # Determine schedule time — pick a random time within current posting window
        tz_offset = config.get("posting_schedule", {}).get("timezone_offset", 2)
        now_sast = datetime.utcnow() + timedelta(hours=tz_offset)
        # Schedule for today or next valid window
        sched_date = now_sast.strftime("%Y-%m-%d")
        windows = config.get("posting_schedule", {}).get("posting_windows", [])
        if windows:
            # Pick a random window and random time within it
            window = random.choice(windows)
            start_h, start_m = map(int, window["start"].split(":"))
            end_h, end_m = map(int, window["end"].split(":"))
            start_mins = start_h * 60 + start_m
            end_mins = end_h * 60 + end_m
            random_mins = random.randint(start_mins, max(start_mins, end_mins - 1))
            sched_time = f"{random_mins // 60:02d}:{random_mins % 60:02d}"
        else:
            sched_time = "09:00"

        post = {
            "id": secrets.token_hex(8),
            "content": result["content"],
            "platforms": [platform],
            "scheduled_date": sched_date,
            "scheduled_time": sched_time,
            "status": "scheduled",
            "image_url": "",
            "hashtags": "",
            "campaign": config.get("campaign_name", "Connexa SA ISP Outreach"),
            "category": result["category"],
            "auto_generated": True,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }

        SOCIAL_POSTS.append(post)
        generated_count += 1

        status_note = " (no account configured — draft only)" if not has_account else ""
        if not has_account:
            post["status"] = "draft"

        log_entries.append({
            "timestamp": datetime.now().isoformat(),
            "platform": platform,
            "action": "generated",
            "post_id": post["id"],
            "category": result["category"],
            "content_preview": result["content"][:80],
            "scheduled": f"{sched_date} {sched_time}",
            "note": status_note.strip(),
        })

    if generated_count > 0:
        save_social_posts()
        config["last_run"] = datetime.now().isoformat()
        config["total_generated"] = config.get("total_generated", 0) + generated_count
        save_automation_config(config)

    save_automation_log(log_entries)


# Background scheduler loop
_automation_task = None

async def _automation_loop():
    """Runs every 30 minutes to check if posts should be auto-generated."""
    while True:
        try:
            await run_automation_cycle()
        except Exception as e:
            print(f"[Automation] Error in cycle: {e}")
        await asyncio.sleep(1800)  # Check every 30 minutes


# ── Automation API endpoints ──

@app.get("/api/admin/social/automation/config")
async def get_automation_config(admin_token: str = "", token: str = ""):
    tok = admin_token or token
    if tok != ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="Unauthorized")
    return {"config": load_automation_config()}


@app.post("/api/admin/social/automation/config")
async def update_automation_config(request: Request):
    body = await request.json()
    if body.get("admin_token") != ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="Unauthorized")

    config = load_automation_config()
    # Update fields that were provided
    updatable = [
        "enabled", "platforms", "campaign_name",
    ]
    for field in updatable:
        if field in body:
            config[field] = body[field]

    # Nested updates
    if "posting_schedule" in body:
        config["posting_schedule"].update(body["posting_schedule"])
    if "content_mix" in body:
        config["content_mix"].update(body["content_mix"])
    if "anti_spam" in body:
        config["anti_spam"].update(body["anti_spam"])

    save_automation_config(config)
    return {"success": True, "config": config}


@app.post("/api/admin/social/automation/generate-now")
async def trigger_automation_now(request: Request):
    """Manually trigger one automation cycle regardless of posting window."""
    body = await request.json()
    if body.get("admin_token") != ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="Unauthorized")

    config = load_automation_config()
    platforms = body.get("platforms", config.get("platforms", ["twitter", "linkedin"]))
    log_entries = load_automation_log()
    generated = []

    for platform in platforms:
        result, reason = generate_automated_post(config, platform)
        if not result:
            generated.append({"platform": platform, "success": False, "reason": reason})
            continue

        tz_offset = config.get("posting_schedule", {}).get("timezone_offset", 2)
        now_sast = datetime.utcnow() + timedelta(hours=tz_offset)
        sched_date = now_sast.strftime("%Y-%m-%d")
        windows = config.get("posting_schedule", {}).get("posting_windows", [])
        if windows:
            window = random.choice(windows)
            start_h, start_m = map(int, window["start"].split(":"))
            end_h, end_m = map(int, window["end"].split(":"))
            random_mins = random.randint(start_h * 60 + start_m, max(start_h * 60 + start_m, end_h * 60 + end_m - 1))
            sched_time = f"{random_mins // 60:02d}:{random_mins % 60:02d}"
        else:
            sched_time = "09:00"

        post = {
            "id": secrets.token_hex(8),
            "content": result["content"],
            "platforms": [platform],
            "scheduled_date": sched_date,
            "scheduled_time": sched_time,
            "status": "scheduled",
            "image_url": "",
            "hashtags": "",
            "campaign": config.get("campaign_name", "Connexa SA ISP Outreach"),
            "category": result["category"],
            "auto_generated": True,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }
        SOCIAL_POSTS.append(post)
        generated.append({"platform": platform, "success": True, "post_id": post["id"], "content_preview": result["content"][:100]})
        log_entries.append({
            "timestamp": datetime.now().isoformat(),
            "platform": platform,
            "action": "manual_generate",
            "post_id": post["id"],
            "category": result["category"],
            "content_preview": result["content"][:80],
        })

    if any(g["success"] for g in generated):
        save_social_posts()
        config["total_generated"] = config.get("total_generated", 0) + sum(1 for g in generated if g["success"])
        config["last_run"] = datetime.now().isoformat()
        save_automation_config(config)
    save_automation_log(log_entries)

    return {"success": True, "generated": generated}


@app.get("/api/admin/social/automation/log")
async def get_automation_log(admin_token: str = "", token: str = "", limit: int = 50):
    tok = admin_token or token
    if tok != ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="Unauthorized")
    entries = load_automation_log()
    return {"entries": entries[-limit:]}


@app.get("/api/admin/social/automation/content-library")
async def get_content_library(admin_token: str = "", token: str = ""):
    tok = admin_token or token
    if tok != ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="Unauthorized")
    return {
        "categories": {k: len(v) for k, v in SA_ISP_CONTENT_LIBRARY.items()},
        "total_templates": sum(len(v) for v in SA_ISP_CONTENT_LIBRARY.values()),
        "hashtag_pool": len(SA_ISP_HASHTAGS),
        "target_handles": {k: len(v) for k, v in SA_ISP_TARGET_HANDLES.items()},
    }


@app.post("/api/admin/social/automation/preview")
async def preview_automation(request: Request):
    """Preview what the next auto-generated posts would look like."""
    body = await request.json()
    if body.get("admin_token") != ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="Unauthorized")

    config = load_automation_config()
    count = min(body.get("count", 5), 10)
    platform = body.get("platform", "twitter")
    previews = []
    for _ in range(count):
        result, reason = generate_automated_post(config, platform)
        if result:
            previews.append(result)

    return {"previews": previews, "platform": platform}


# ═══════════════════════════════════════════════════════
#   SOCIAL MEDIA PUBLISHING ENGINE
#   Publishes scheduled posts via platform APIs
# ═══════════════════════════════════════════════════════

import httpx
import base64
import hmac as _hmac
import time as _time
import urllib.parse as _urlparse

PUBLISH_LOG_FILE = "publish_log.json"

def _load_publish_log():
    try:
        data = store.load(PUBLISH_LOG_FILE)
        if isinstance(data, list):
            return data[-500:]
        return []
    except:
        return []

def _save_publish_log(entries):
    store.save(PUBLISH_LOG_FILE, entries[-500:])

def _get_account_for_platform(platform: str):
    """Find enabled account with credentials for a platform."""
    for a in SOCIAL_ACCOUNTS:
        if a.get("platform") == platform and a.get("enabled", True):
            # Check has minimum credentials
            if platform == "twitter" and a.get("api_key") and a.get("api_secret") and a.get("access_token") and a.get("access_token_secret"):
                return a
            elif platform == "linkedin" and a.get("access_token"):
                return a
            elif platform == "facebook" and a.get("access_token"):
                return a
    return None


# ── Twitter/X API v2 Publishing (OAuth 1.0a) ──

def _twitter_oauth_signature(method, url, params, consumer_secret, token_secret):
    """Create OAuth 1.0a signature for Twitter API."""
    sorted_params = "&".join(f"{_urlparse.quote(k, safe='')}={_urlparse.quote(v, safe='')}"
                             for k, v in sorted(params.items()))
    base_string = f"{method.upper()}&{_urlparse.quote(url, safe='')}&{_urlparse.quote(sorted_params, safe='')}"
    signing_key = f"{_urlparse.quote(consumer_secret, safe='')}&{_urlparse.quote(token_secret, safe='')}"
    sig = _hmac.new(signing_key.encode(), base_string.encode(), hashlib.sha1)
    return base64.b64encode(sig.digest()).decode()


async def publish_to_twitter(content: str, account: dict) -> dict:
    """Publish a tweet using Twitter API v2 with OAuth 1.0a."""
    url = "https://api.twitter.com/2/tweets"
    consumer_key = account["api_key"]
    consumer_secret = account["api_secret"]
    access_token = account["access_token"]
    access_token_secret = account["access_token_secret"]

    # Build OAuth params
    oauth_params = {
        "oauth_consumer_key": consumer_key,
        "oauth_nonce": secrets.token_hex(16),
        "oauth_signature_method": "HMAC-SHA1",
        "oauth_timestamp": str(int(_time.time())),
        "oauth_token": access_token,
        "oauth_version": "1.0",
    }
    sig = _twitter_oauth_signature("POST", url, oauth_params, consumer_secret, access_token_secret)
    oauth_params["oauth_signature"] = sig
    auth_header = "OAuth " + ", ".join(
        f'{_urlparse.quote(k, safe="")}="{_urlparse.quote(v, safe="")}"'
        for k, v in sorted(oauth_params.items())
    )

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(url, json={"text": content}, headers={
            "Authorization": auth_header,
            "Content-Type": "application/json",
        })
    if resp.status_code in (200, 201):
        data = resp.json()
        tweet_id = data.get("data", {}).get("id", "")
        return {"success": True, "post_url": f"https://x.com/i/status/{tweet_id}", "platform_id": tweet_id}
    else:
        return {"success": False, "error": f"Twitter API {resp.status_code}: {resp.text[:200]}"}


# ── LinkedIn API Publishing ──

async def publish_to_linkedin(content: str, account: dict) -> dict:
    """Publish to LinkedIn using v2 API (UGC Posts)."""
    access_token = account["access_token"]
    person_urn = account.get("page_id", "")  # Format: urn:li:person:XXXX or urn:li:organization:XXXX

    if not person_urn:
        # Try to get profile URN
        async with httpx.AsyncClient(timeout=30) as client:
            prof = await client.get("https://api.linkedin.com/v2/userinfo", headers={
                "Authorization": f"Bearer {access_token}",
            })
        if prof.status_code == 200:
            sub = prof.json().get("sub", "")
            person_urn = f"urn:li:person:{sub}"
        else:
            return {"success": False, "error": f"LinkedIn profile lookup failed: {prof.status_code}"}

    # Create UGC post
    post_body = {
        "author": person_urn,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": content},
                "shareMediaCategory": "NONE",
            }
        },
        "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
    }

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post("https://api.linkedin.com/v2/ugcPosts", json=post_body, headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0",
        })
    if resp.status_code in (200, 201):
        post_id = resp.headers.get("x-restli-id", resp.json().get("id", ""))
        return {"success": True, "post_url": f"https://www.linkedin.com/feed/update/{post_id}", "platform_id": post_id}
    else:
        return {"success": False, "error": f"LinkedIn API {resp.status_code}: {resp.text[:200]}"}


# ── Facebook Graph API Publishing ──

async def publish_to_facebook(content: str, account: dict) -> dict:
    """Publish to Facebook Page using Graph API."""
    access_token = account["access_token"]
    page_id = account.get("page_id", "me")

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            f"https://graph.facebook.com/v19.0/{page_id}/feed",
            data={"message": content, "access_token": access_token},
        )
    if resp.status_code == 200:
        post_id = resp.json().get("id", "")
        return {"success": True, "post_url": f"https://www.facebook.com/{post_id}", "platform_id": post_id}
    else:
        return {"success": False, "error": f"Facebook API {resp.status_code}: {resp.text[:200]}"}


# ── Unified Publisher ──

PLATFORM_PUBLISHERS = {
    "twitter": publish_to_twitter,
    "linkedin": publish_to_linkedin,
    "facebook": publish_to_facebook,
}

async def publish_post(post: dict) -> dict:
    """Attempt to publish a post to all its target platforms."""
    results = []
    platforms = post.get("platforms", [])
    pub_log = _load_publish_log()

    for platform in platforms:
        account = _get_account_for_platform(platform)
        if not account:
            results.append({"platform": platform, "success": False, "error": "No account configured"})
            continue

        publisher = PLATFORM_PUBLISHERS.get(platform)
        if not publisher:
            results.append({"platform": platform, "success": False, "error": "Unsupported platform"})
            continue

        try:
            result = await publisher(post["content"], account)
            results.append({"platform": platform, **result})
            pub_log.append({
                "timestamp": datetime.now().isoformat(),
                "post_id": post.get("id"),
                "platform": platform,
                "action": "published" if result["success"] else "publish_failed",
                "post_url": result.get("post_url", ""),
                "error": result.get("error", ""),
                "content_preview": post["content"][:80],
            })
        except Exception as e:
            results.append({"platform": platform, "success": False, "error": str(e)[:200]})
            pub_log.append({
                "timestamp": datetime.now().isoformat(),
                "post_id": post.get("id"),
                "platform": platform,
                "action": "publish_error",
                "error": str(e)[:200],
            })

    _save_publish_log(pub_log)
    return {"results": results}


# ── Auto-Publisher Background Loop ──

async def _auto_publish_cycle():
    """Check for scheduled posts that are due and publish them."""
    config = load_automation_config()
    if not config.get("enabled"):
        return

    tz_offset = config.get("posting_schedule", {}).get("timezone_offset", 2)
    now_sast = datetime.utcnow() + timedelta(hours=tz_offset)
    now_date = now_sast.strftime("%Y-%m-%d")
    now_time = now_sast.strftime("%H:%M")

    published_count = 0

    for post in SOCIAL_POSTS:
        if post.get("status") != "scheduled":
            continue
        sched_date = post.get("scheduled_date", "")
        sched_time = post.get("scheduled_time", "")

        # Only publish posts that are at or past their scheduled time
        if sched_date > now_date:
            continue
        if sched_date == now_date and sched_time > now_time:
            continue

        # Try to publish
        result = await publish_post(post)
        successes = [r for r in result["results"] if r.get("success")]
        failures = [r for r in result["results"] if not r.get("success")]

        if successes:
            post["status"] = "published"
            post["published_at"] = datetime.now().isoformat()
            post["publish_urls"] = {r["platform"]: r.get("post_url", "") for r in successes}
            published_count += 1

            # Log to automation log too
            auto_log = load_automation_log()
            for s in successes:
                auto_log.append({
                    "timestamp": datetime.now().isoformat(),
                    "platform": s["platform"],
                    "action": "published",
                    "post_id": post["id"],
                    "content_preview": post["content"][:80],
                    "post_url": s.get("post_url", ""),
                })
            save_automation_log(auto_log)

        if failures and not successes:
            # All platforms failed — mark as failed, will retry next cycle (up to 3 times)
            retries = post.get("publish_retries", 0)
            if retries >= 3:
                post["status"] = "failed"
                post["fail_reason"] = failures[0].get("error", "Unknown error")
            else:
                post["publish_retries"] = retries + 1

    if published_count > 0:
        save_social_posts()
        config["total_published"] = config.get("total_published", 0) + published_count
        save_automation_config(config)
        print(f"[AutoPublish] Published {published_count} post(s)")


# Extend the automation loop to also run auto-publishing
_original_automation_loop = _automation_loop

async def _automation_loop():
    """Enhanced automation loop — generates AND publishes posts."""
    while True:
        try:
            await run_automation_cycle()
        except Exception as e:
            print(f"[Automation] Generate error: {e}")
        try:
            await _auto_publish_cycle()
        except Exception as e:
            print(f"[AutoPublish] Error: {e}")
        await asyncio.sleep(1800)


# ── Publishing API Endpoints ──

@app.post("/api/admin/social/publish")
async def publish_post_now(request: Request):
    """Manually publish a specific post immediately."""
    body = await request.json()
    if body.get("admin_token") != ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="Unauthorized")

    post_id = body.get("post_id")
    post = next((p for p in SOCIAL_POSTS if p["id"] == post_id), None)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    result = await publish_post(post)
    successes = [r for r in result["results"] if r.get("success")]
    if successes:
        post["status"] = "published"
        post["published_at"] = datetime.now().isoformat()
        post["publish_urls"] = {r["platform"]: r.get("post_url", "") for r in successes}
        save_social_posts()

    return {"success": len(successes) > 0, "results": result["results"]}


@app.get("/api/admin/social/publish/log")
async def get_publish_log(admin_token: str = "", token: str = "", limit: int = 50):
    tok = admin_token or token
    if tok != ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="Unauthorized")
    return {"entries": _load_publish_log()[-limit:]}


@app.get("/api/admin/social/publish/status")
async def get_publish_status(admin_token: str = "", token: str = ""):
    """Get publishing pipeline status — connected accounts, queue depth, etc."""
    tok = admin_token or token
    if tok != ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="Unauthorized")

    config = load_automation_config()
    platforms = config.get("platforms", ["twitter", "linkedin"])

    accounts_status = {}
    for platform in ["twitter", "linkedin", "facebook"]:
        acc = _get_account_for_platform(platform)
        accounts_status[platform] = {
            "connected": acc is not None,
            "account_name": acc.get("account_name", "") if acc else "",
            "enabled": platform in platforms,
        }

    # Count posts by status
    scheduled_count = sum(1 for p in SOCIAL_POSTS if p.get("status") == "scheduled")
    published_count = sum(1 for p in SOCIAL_POSTS if p.get("status") == "published")
    failed_count = sum(1 for p in SOCIAL_POSTS if p.get("status") == "failed")
    draft_count = sum(1 for p in SOCIAL_POSTS if p.get("status") == "draft")

    return {
        "automation_enabled": config.get("enabled", False),
        "accounts": accounts_status,
        "queue": {
            "scheduled": scheduled_count,
            "published": published_count,
            "failed": failed_count,
            "drafts": draft_count,
        },
        "total_published": config.get("total_published", 0),
        "last_run": config.get("last_run"),
    }


@app.post("/api/admin/social/accounts/test")
async def test_social_account(request: Request):
    """Test if a social media account's API credentials are valid."""
    body = await request.json()
    if body.get("admin_token") != ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="Unauthorized")

    account_id = body.get("account_id")
    account = next((a for a in SOCIAL_ACCOUNTS if a["id"] == account_id), None)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    platform = account["platform"]
    try:
        if platform == "twitter":
            # Verify credentials via Twitter API v2
            url = "https://api.twitter.com/2/users/me"
            oauth_params = {
                "oauth_consumer_key": account["api_key"],
                "oauth_nonce": secrets.token_hex(16),
                "oauth_signature_method": "HMAC-SHA1",
                "oauth_timestamp": str(int(_time.time())),
                "oauth_token": account["access_token"],
                "oauth_version": "1.0",
            }
            sig = _twitter_oauth_signature("GET", url, oauth_params, account["api_secret"], account["access_token_secret"])
            oauth_params["oauth_signature"] = sig
            auth_header = "OAuth " + ", ".join(
                f'{_urlparse.quote(k, safe="")}="{_urlparse.quote(v, safe="")}"'
                for k, v in sorted(oauth_params.items())
            )
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(url, headers={"Authorization": auth_header})
            if resp.status_code == 200:
                user_data = resp.json().get("data", {})
                return {"success": True, "platform": "twitter", "username": user_data.get("username", ""), "name": user_data.get("name", "")}
            else:
                return {"success": False, "error": f"Twitter returned {resp.status_code}: {resp.text[:150]}"}

        elif platform == "linkedin":
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get("https://api.linkedin.com/v2/userinfo", headers={
                    "Authorization": f"Bearer {account['access_token']}",
                })
            if resp.status_code == 200:
                d = resp.json()
                return {"success": True, "platform": "linkedin", "username": d.get("name", ""), "name": d.get("name", "")}
            else:
                return {"success": False, "error": f"LinkedIn returned {resp.status_code}: {resp.text[:150]}"}

        elif platform == "facebook":
            async with httpx.AsyncClient(timeout=15) as client:
                page_id = account.get("page_id", "me")
                resp = await client.get(f"https://graph.facebook.com/v19.0/{page_id}",
                                        params={"access_token": account["access_token"], "fields": "name,id"})
            if resp.status_code == 200:
                d = resp.json()
                return {"success": True, "platform": "facebook", "username": d.get("name", ""), "name": d.get("name", "")}
            else:
                return {"success": False, "error": f"Facebook returned {resp.status_code}: {resp.text[:150]}"}

        else:
            return {"success": False, "error": f"Unsupported platform: {platform}"}

    except Exception as e:
        return {"success": False, "error": str(e)[:200]}


# ── Setup Wizard Endpoint ──

@app.get("/api/admin/social/setup-guide")
async def get_setup_guide(admin_token: str = "", token: str = ""):
    """Return setup instructions for each platform."""
    tok = admin_token or token
    if tok != ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="Unauthorized")

    return {
        "platforms": {
            "twitter": {
                "name": "Twitter / X",
                "signup_url": "https://x.com/i/flow/signup",
                "developer_url": "https://developer.x.com/en/portal/dashboard",
                "steps": [
                    "1. Create a Twitter/X account at x.com/i/flow/signup",
                    "2. Go to developer.x.com and sign up for a Developer account (Free tier)",
                    "3. Create a Project and App in the Developer Portal",
                    "4. In your App settings, set up 'User authentication settings' — enable OAuth 1.0a with Read+Write",
                    "5. Generate your API Key, API Secret, Access Token, and Access Token Secret",
                    "6. Enter all 4 credentials in the Add Account form below",
                ],
                "fields": ["api_key", "api_secret", "access_token", "access_token_secret"],
                "free_tier": "1,500 tweets/month (Free), 3,000 tweets/month (Basic $200/mo)",
            },
            "linkedin": {
                "name": "LinkedIn",
                "signup_url": "https://www.linkedin.com/signup",
                "developer_url": "https://www.linkedin.com/developers/apps",
                "steps": [
                    "1. Create a LinkedIn account at linkedin.com/signup",
                    "2. Create a LinkedIn Company Page for Connexify",
                    "3. Go to linkedin.com/developers/apps and create a new app",
                    "4. Request 'Share on LinkedIn' and 'Sign In with LinkedIn' products",
                    "5. Generate an Access Token (valid 60 days — auto-refresh will be added)",
                    "6. Enter the Access Token and your company page URN (urn:li:organization:XXXXX) below",
                ],
                "fields": ["access_token", "page_id"],
                "free_tier": "Unlimited posts (standard API — rate limited to 100 calls/day)",
            },
            "facebook": {
                "name": "Facebook",
                "signup_url": "https://www.facebook.com/r.php",
                "developer_url": "https://developers.facebook.com/apps/",
                "steps": [
                    "1. Create a Facebook account at facebook.com",
                    "2. Create a Facebook Page for Connexify",
                    "3. Go to developers.facebook.com and create a new app (Business type)",
                    "4. Add 'Pages API' product to your app",
                    "5. Generate a Page Access Token with 'pages_manage_posts' permission",
                    "6. Enter the Page Access Token and Page ID below",
                ],
                "fields": ["access_token", "page_id"],
                "free_tier": "Unlimited posts with Page Access Token",
            },
        }
    }


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
