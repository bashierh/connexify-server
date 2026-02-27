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
from templates import WEBSITE_TEMPLATE, GET_STARTED_TEMPLATE
from portal_template import PORTAL_TEMPLATE
from admin_template import ADMIN_HTML

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

DATA_DIR = str(LICENSE_DB_FILE.parent)

ADMIN_TOKEN = os.getenv("ADMIN_SECRET_TOKEN", "your-admin-secret-token-change-this")
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
    if os.path.exists(PORTAL_USERS_FILE):
        try:
            with open(PORTAL_USERS_FILE, 'r') as f:
                PORTAL_USERS = json.load(f)
            print(f"[Portal] Loaded {len(PORTAL_USERS)} portal users")
        except Exception as e:
            print(f"[Portal] Error loading users: {e}")

def save_portal_users():
    try:
        with open(PORTAL_USERS_FILE, 'w') as f:
            json.dump(PORTAL_USERS, f, indent=2)
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
PORTAL_HTML = _render_template(PORTAL_TEMPLATE)


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
#   ROUTES - Free Trial
# ══════════════════════════════════════════════════════════════════

class TrialRequest(BaseModel):
    name: str
    email: str
    company: str = ""
    password: str = ""


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
    """Generate a 7-day trial license and email it."""
    email = request.email.strip().lower()
    if not email:
        raise HTTPException(status_code=400, detail="Email is required")

    # Check if this email already has a trial license
    for key, lic in LICENSE_DATABASE.items():
        if lic.get('customer_email', '').lower() == email and lic.get('is_demo'):
            # Already has a trial — re-send the key
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
        "amount": f"{total:.2f}",
        "item_name": item_name[:100],
        "item_description": item_desc[:255],
        "custom_str1": request.email,
        "custom_str2": request.company,
        "custom_str3": request.plan,
        "custom_int1": str(qty),
        "custom_int2": str(1 if cycle == "annual" else 0),  # 1=annual 0=monthly
    }

    # Generate signature
    signature = generate_payfast_signature(data)
    data["signature"] = signature

    return {"form_fields": data, "payfast_url": PAYFAST_URL, "payment_id": payment_id}


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
    body = await request.json()
    email = (body.get("email") or "").strip().lower()
    password = body.get("password") or ""
    if not email or not password:
        raise HTTPException(400, "Email and password required")
    user = verify_portal_login(email, password)
    if not user:
        raise HTTPException(401, "Invalid email or password")
    if user.get("is_suspended"):
        raise HTTPException(403, "Account suspended. Contact support.")
    token = create_session(email)
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
        "custom_str1": user["email"],
        "custom_str2": user.get("company", ""),
        "custom_str3": "professional",
        "custom_int1": str(qty),
        "custom_int2": str(1 if cycle == "annual" else 0),
    }
    signature = generate_payfast_signature(data)
    data["signature"] = signature
    return {"form_fields": data, "payfast_url": PAYFAST_URL, "payment_id": payment_id}


@app.post("/api/portal/activate-trial")
async def portal_activate_trial(request: Request):
    """Activate a 7-day trial from the portal."""
    user = await _get_portal_user(request)
    email = user["email"]

    # Check for existing trial
    for key, lic in LICENSE_DATABASE.items():
        if lic.get('customer_email', '').lower() == email and lic.get('is_demo'):
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
# Use persistent disk on Render so files survive deploys
_PERSISTENT_STATIC = Path("/opt/render/project/data/static")
_LOCAL_STATIC = Path(__file__).parent / "static"
if _PERSISTENT_STATIC.parent.exists():
    STATIC_DIR = _PERSISTENT_STATIC
else:
    STATIC_DIR = _LOCAL_STATIC
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
