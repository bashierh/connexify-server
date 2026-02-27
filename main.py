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
from pathlib import Path
from typing import Optional

# ── Email service (inline, no external dependency) ──
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

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
#   CONNEXIFY WEBSITE (landing page)
# ══════════════════════════════════════════════════════════════════

WEBSITE_HTML = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Connexify (Pty) Ltd - Network Management Solutions</title>
    <meta name="description" content="Connexify provides Connexa, a professional network management platform for ISPs and WISPs. Monitor towers, manage devices, automate scripts, and track wireless clients.">
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet">
    <style>
        * {{ font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; }}
        body {{ background: #030712; color: #e2e8f0; }}
        .hero-gradient {{ background: radial-gradient(ellipse at top, #1e3a5f 0%, #030712 70%); }}
        .gradient-text {{ background: linear-gradient(135deg, #3b82f6 0%, #06b6d4 50%, #10b981 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
        .card {{ background: rgba(15,23,42,0.6); backdrop-filter: blur(12px); border: 1px solid rgba(71,85,105,0.3); transition: all 0.3s ease; }}
        .card:hover {{ border-color: rgba(59,130,246,0.4); transform: translateY(-4px); box-shadow: 0 20px 40px rgba(0,0,0,0.3); }}
        .glow-btn {{ background: linear-gradient(135deg, #3b82f6, #06b6d4); transition: all 0.3s ease; }}
        .glow-btn:hover {{ transform: scale(1.05); box-shadow: 0 10px 40px rgba(59,130,246,0.4); }}
        .download-card {{ background: rgba(15,23,42,0.8); border: 1px solid rgba(71,85,105,0.4); }}
        .download-card:hover {{ border-color: rgba(59,130,246,0.6); box-shadow: 0 15px 30px rgba(0,0,0,0.3); }}
        .section-divider {{ border-top: 1px solid rgba(71,85,105,0.2); }}
        @keyframes float {{ 0%,100% {{ transform: translateY(0px); }} 50% {{ transform: translateY(-10px); }} }}
        .float-animation {{ animation: float 6s ease-in-out infinite; }}
    </style>
</head>
<body>
    <!-- Navigation -->
    <nav class="fixed top-0 w-full z-50 bg-gray-950/80 backdrop-blur-lg border-b border-gray-800/50">
        <div class="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
            <div class="flex items-center gap-3">
                <div class="w-10 h-10 rounded-lg bg-gradient-to-br from-blue-500 to-cyan-500 flex items-center justify-center font-bold text-white text-lg">C</div>
                <div>
                    <span class="text-xl font-bold text-white">Connexify</span>
                    <span class="text-[10px] text-gray-500 block -mt-1">(Pty) Ltd</span>
                </div>
            </div>
            <div class="hidden md:flex items-center gap-8 text-sm text-gray-400">
                <a href="#features" class="hover:text-white transition">Features</a>
                <a href="#downloads" class="hover:text-white transition">Downloads</a>
                <a href="#pricing" class="hover:text-white transition">Pricing</a>
                <a href="#contact" class="hover:text-white transition">Contact</a>
            </div>
            <a href="#downloads" class="glow-btn px-5 py-2 rounded-lg text-white text-sm font-medium">Download</a>
        </div>
    </nav>

    <!-- Hero Section -->
    <section class="hero-gradient min-h-screen flex items-center pt-20">
        <div class="max-w-7xl mx-auto px-6 py-20 grid lg:grid-cols-2 gap-16 items-center">
            <div>
                <div class="inline-flex items-center gap-2 bg-blue-500/10 border border-blue-500/20 text-blue-400 px-4 py-1.5 rounded-full text-sm mb-6">
                    <span class="w-2 h-2 rounded-full bg-green-400 animate-pulse"></span>
                    Version {CURRENT_VERSION} Now Available
                </div>
                <h1 class="text-5xl lg:text-6xl font-extrabold leading-tight mb-6">
                    <span class="gradient-text">Professional</span><br>
                    Network Management
                </h1>
                <p class="text-lg text-gray-400 leading-relaxed mb-8 max-w-lg">
                    Monitor your towers, manage devices, automate configurations, and track wireless clients &mdash; all from one beautiful dashboard built for ISPs and WISPs.
                </p>
                <div class="flex flex-wrap gap-4">
                    <a href="#downloads" class="glow-btn px-8 py-3 rounded-xl text-white font-semibold text-lg inline-flex items-center gap-2">
                        &#11015; Download Free Trial
                    </a>
                    <a href="#features" class="px-8 py-3 rounded-xl border border-gray-700 text-gray-300 hover:border-gray-500 hover:text-white transition font-medium">
                        Learn More &rarr;
                    </a>
                </div>
            </div>
            <div class="hidden lg:flex justify-center">
                <div class="float-animation relative">
                    <div class="w-96 h-64 rounded-2xl bg-gradient-to-br from-gray-900 to-gray-800 border border-gray-700 shadow-2xl p-6 space-y-4">
                        <div class="flex items-center gap-2">
                            <div class="w-3 h-3 rounded-full bg-red-500"></div>
                            <div class="w-3 h-3 rounded-full bg-yellow-500"></div>
                            <div class="w-3 h-3 rounded-full bg-green-500"></div>
                            <span class="text-xs text-gray-500 ml-2">Connexa Dashboard</span>
                        </div>
                        <div class="grid grid-cols-3 gap-3">
                            <div class="bg-gray-800/80 rounded-lg p-3 text-center">
                                <div class="text-2xl font-bold text-blue-400">24</div>
                                <div class="text-[10px] text-gray-500">Towers</div>
                            </div>
                            <div class="bg-gray-800/80 rounded-lg p-3 text-center">
                                <div class="text-2xl font-bold text-green-400">847</div>
                                <div class="text-[10px] text-gray-500">Clients</div>
                            </div>
                            <div class="bg-gray-800/80 rounded-lg p-3 text-center">
                                <div class="text-2xl font-bold text-cyan-400">99.8%</div>
                                <div class="text-[10px] text-gray-500">Uptime</div>
                            </div>
                        </div>
                        <div class="space-y-2">
                            <div class="flex items-center gap-2"><div class="w-2 h-2 rounded-full bg-green-400"></div><span class="text-xs text-gray-400">Tower Alpha - 32 clients</span><span class="text-xs text-green-400 ml-auto">-62 dBm</span></div>
                            <div class="flex items-center gap-2"><div class="w-2 h-2 rounded-full bg-green-400"></div><span class="text-xs text-gray-400">Tower Bravo - 28 clients</span><span class="text-xs text-green-400 ml-auto">-58 dBm</span></div>
                            <div class="flex items-center gap-2"><div class="w-2 h-2 rounded-full bg-yellow-400"></div><span class="text-xs text-gray-400">Tower Charlie - 41 clients</span><span class="text-xs text-yellow-400 ml-auto">-74 dBm</span></div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </section>

    <!-- Features -->
    <section id="features" class="section-divider py-24">
        <div class="max-w-7xl mx-auto px-6">
            <div class="text-center mb-16">
                <h2 class="text-4xl font-bold mb-4"><span class="gradient-text">Built for ISPs & WISPs</span></h2>
                <p class="text-gray-400 text-lg max-w-2xl mx-auto">Everything you need to manage your wireless network infrastructure in one platform.</p>
            </div>
            <div class="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
                <div class="card rounded-2xl p-6">
                    <div class="text-3xl mb-4">&#128225;</div>
                    <h3 class="text-lg font-semibold mb-2 text-white">Tower Monitoring</h3>
                    <p class="text-gray-400 text-sm">Real-time monitoring of all your tower equipment. Signal levels, client counts, uptime, and performance metrics at a glance.</p>
                </div>
                <div class="card rounded-2xl p-6">
                    <div class="text-3xl mb-4">&#128187;</div>
                    <h3 class="text-lg font-semibold mb-2 text-white">Device Management</h3>
                    <p class="text-gray-400 text-sm">Manage MikroTik, Ubiquiti, Cambium, and Mimosa devices. Auto-discovery, firmware tracking, and configuration backups.</p>
                </div>
                <div class="card rounded-2xl p-6">
                    <div class="text-3xl mb-4">&#128246;</div>
                    <h3 class="text-lg font-semibold mb-2 text-white">Wireless Clients</h3>
                    <p class="text-gray-400 text-sm">Track every connected client across all towers. Signal strength, SNR, CCQ, and data rates with automatic classification.</p>
                </div>
                <div class="card rounded-2xl p-6">
                    <div class="text-3xl mb-4">&#128196;</div>
                    <h3 class="text-lg font-semibold mb-2 text-white">Script Automation</h3>
                    <p class="text-gray-400 text-sm">Push RouterOS scripts to devices individually or in bulk. Schedule recurring tasks for automated configuration management.</p>
                </div>
                <div class="card rounded-2xl p-6">
                    <div class="text-3xl mb-4">&#128202;</div>
                    <h3 class="text-lg font-semibold mb-2 text-white">Zabbix Integration</h3>
                    <p class="text-gray-400 text-sm">Seamless integration with Zabbix for advanced monitoring, alerting, and historical data analysis.</p>
                </div>
                <div class="card rounded-2xl p-6">
                    <div class="text-3xl mb-4">&#128274;</div>
                    <h3 class="text-lg font-semibold mb-2 text-white">Multi-Tenancy</h3>
                    <p class="text-gray-400 text-sm">Isolate data by company. Perfect for MSPs managing multiple client networks from a single Connexa instance.</p>
                </div>
            </div>
        </div>
    </section>

    <!-- Downloads -->
    <section id="downloads" class="section-divider py-24 bg-gray-950/50">
        <div class="max-w-5xl mx-auto px-6">
            <div class="text-center mb-12">
                <h2 class="text-4xl font-bold mb-4"><span class="gradient-text">Download Connexa</span></h2>
                <p class="text-gray-400 text-lg">Version {CURRENT_VERSION} &mdash; Desktop application for Linux</p>
            </div>
            <div class="grid md:grid-cols-2 gap-6 max-w-3xl mx-auto" id="download-cards">
                <!-- DEB Package -->
                <div class="download-card rounded-2xl p-8 text-center transition-all">
                    <div class="text-5xl mb-4">&#128039;</div>
                    <h3 class="text-xl font-semibold mb-2 text-white">Debian / Ubuntu</h3>
                    <p class="text-gray-400 text-sm mb-1">connexa_{CURRENT_VERSION}_amd64.deb</p>
                    <p class="text-gray-500 text-xs mb-6">Recommended for Ubuntu 22.04+</p>
                    <a id="deb-download" href="/static/connexa_{CURRENT_VERSION}_amd64.deb" class="glow-btn inline-block py-3 px-8 rounded-xl text-white font-medium">
                        &#11015; Download .deb
                    </a>
                    <p class="text-gray-600 text-xs mt-4">
                        Install: <code class="bg-gray-800 px-2 py-0.5 rounded text-gray-400">sudo dpkg -i connexa_*.deb</code>
                    </p>
                </div>
                <!-- Windows EXE -->
                <div class="download-card rounded-2xl p-8 text-center transition-all">
                    <div class="text-5xl mb-4">&#128187;</div>
                    <h3 class="text-xl font-semibold mb-2 text-white">Windows</h3>
                    <p class="text-gray-400 text-sm mb-1">Connexa-Setup-{CURRENT_VERSION}.exe</p>
                    <p class="text-gray-500 text-xs mb-6">Windows 10 / 11 (64-bit)</p>
                    <a id="exe-download" href="/static/Connexa-Setup-{CURRENT_VERSION}.exe" class="glow-btn inline-block py-3 px-8 rounded-xl text-white font-medium">
                        &#11015; Download .exe
                    </a>
                    <p class="text-gray-600 text-xs mt-4">
                        Run the installer and follow the setup wizard
                    </p>
                </div>
            </div>
            <div class="text-center mt-8 text-gray-500 text-sm">
                <p>Need a license key? <a href="#contact" class="text-blue-400 hover:underline">Contact us</a> or email <a href="mailto:{SUPPORT_EMAIL}" class="text-blue-400 hover:underline">{SUPPORT_EMAIL}</a></p>
            </div>
        </div>
    </section>

    <!-- Pricing -->
    <section id="pricing" class="section-divider py-24">
        <div class="max-w-5xl mx-auto px-6">
            <div class="text-center mb-12">
                <h2 class="text-4xl font-bold mb-4"><span class="gradient-text">Simple Pricing</span></h2>
                <p class="text-gray-400 text-lg">Choose the plan that fits your network</p>
            </div>
            <div class="grid md:grid-cols-3 gap-6">
                <div class="card rounded-2xl p-8">
                    <h3 class="text-lg font-semibold text-gray-400 mb-2">Trial</h3>
                    <div class="text-4xl font-bold text-white mb-1">Free</div>
                    <p class="text-gray-500 text-sm mb-6">7-day trial</p>
                    <ul class="space-y-3 text-sm text-gray-400 mb-8">
                        <li>&#10003; Up to 10 devices</li>
                        <li>&#10003; All features included</li>
                        <li>&#10003; Email support</li>
                    </ul>
                    <a href="#downloads" class="block text-center py-2.5 rounded-lg border border-gray-700 text-gray-300 hover:border-blue-500 transition text-sm font-medium">Start Free Trial</a>
                </div>
                <div class="card rounded-2xl p-8 border-blue-500/30 relative">
                    <div class="absolute -top-3 left-1/2 -translate-x-1/2 bg-blue-600 text-white text-xs font-semibold px-3 py-1 rounded-full">Popular</div>
                    <h3 class="text-lg font-semibold text-blue-400 mb-2">Professional</h3>
                    <div class="text-4xl font-bold text-white mb-1">R500<span class="text-lg text-gray-500">/mo</span></div>
                    <p class="text-gray-500 text-sm mb-6">Per installation</p>
                    <ul class="space-y-3 text-sm text-gray-400 mb-8">
                        <li>&#10003; Unlimited devices</li>
                        <li>&#10003; All features included</li>
                        <li>&#10003; Priority support</li>
                        <li>&#10003; Zabbix integration</li>
                    </ul>
                    <a href="mailto:{SUPPORT_EMAIL}?subject=Connexa%20Professional%20License" class="glow-btn block text-center py-2.5 rounded-lg text-white text-sm font-medium">Get Started</a>
                </div>
                <div class="card rounded-2xl p-8">
                    <h3 class="text-lg font-semibold text-gray-400 mb-2">Enterprise</h3>
                    <div class="text-4xl font-bold text-white mb-1">Custom</div>
                    <p class="text-gray-500 text-sm mb-6">Multi-tenant / MSP</p>
                    <ul class="space-y-3 text-sm text-gray-400 mb-8">
                        <li>&#10003; Multi-company support</li>
                        <li>&#10003; Custom branding</li>
                        <li>&#10003; Dedicated support</li>
                        <li>&#10003; On-premise deployment</li>
                    </ul>
                    <a href="mailto:{SUPPORT_EMAIL}?subject=Connexa%20Enterprise%20Inquiry" class="block text-center py-2.5 rounded-lg border border-gray-700 text-gray-300 hover:border-blue-500 transition text-sm font-medium">Contact Sales</a>
                </div>
            </div>
        </div>
    </section>

    <!-- Contact -->
    <section id="contact" class="section-divider py-24 bg-gray-950/50">
        <div class="max-w-3xl mx-auto px-6 text-center">
            <h2 class="text-4xl font-bold mb-4"><span class="gradient-text">Get in Touch</span></h2>
            <p class="text-gray-400 text-lg mb-8">Ready to streamline your network management? We're here to help.</p>
            <div class="grid sm:grid-cols-2 gap-6 mb-12">
                <div class="card rounded-2xl p-6">
                    <div class="text-2xl mb-2">&#9993;</div>
                    <h3 class="text-white font-medium mb-1">Email</h3>
                    <a href="mailto:{SUPPORT_EMAIL}" class="text-blue-400 hover:underline text-sm">{SUPPORT_EMAIL}</a>
                </div>
                <div class="card rounded-2xl p-6">
                    <div class="text-2xl mb-2">&#128222;</div>
                    <h3 class="text-white font-medium mb-1">Support</h3>
                    <p class="text-gray-400 text-sm">Response within 24 hours</p>
                </div>
            </div>
            <div class="text-gray-600 text-sm">
                <p>&copy; {datetime.now().year} Connexify (Pty) Ltd &mdash; South Africa</p>
                <p class="mt-1">All rights reserved.</p>
            </div>
        </div>
    </section>
</body>
</html>"""


# ══════════════════════════════════════════════════════════════════
#   ROUTES - Website
# ══════════════════════════════════════════════════════════════════

@app.get("/", response_class=HTMLResponse)
async def homepage():
    """Connexify company website"""
    return HTMLResponse(content=WEBSITE_HTML)


@app.get("/health")
async def health_check():
    return {"service": "Connexa License Server", "status": "running", "version": "1.0.0", "licenses": len(LICENSE_DATABASE)}


# Serve static files for downloads (DEB / EXE)
# Place installer files in render-license-server/static/
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
        ACTIVATIONS_DB[request.license_key] = {
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
    
    allowed_ext = ('.deb', '.exe', '.AppImage', '.dmg', '.zip')
    if not any(file.filename.endswith(ext) for ext in allowed_ext):
        raise HTTPException(status_code=400, detail=f"Only installer files allowed: {allowed_ext}")
    
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


# ── Downloads page (legacy URL compat) ──

@app.get("/downloads", response_class=HTMLResponse)
async def downloads_page():
    """Redirect to homepage downloads section"""
    return RedirectResponse(url="/#downloads")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8002")))
