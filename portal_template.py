"""
Connexify Customer Portal Template
Self-contained dashboard — no external auth dependency.
Uses session tokens + FastAPI backend for data.
"""

PORTAL_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>My Account - __COMPANY__</title>
<script src="https://cdn.tailwindcss.com"></script>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<style>
body{background:#0a0a0f;font-family:'Inter',system-ui,sans-serif}
.glass{background:rgba(15,23,42,0.6);border:1px solid rgba(71,85,105,0.3);backdrop-filter:blur(12px)}
.glow-btn{background:linear-gradient(135deg,#2563eb,#7c3aed)}.glow-btn:hover{background:linear-gradient(135deg,#1d4ed8,#6d28d9)}
.sidebar-link{transition:all 0.2s;display:flex;align-items:center;gap:0.75rem;padding:0.6rem 1rem;border-radius:0.5rem;color:#94a3b8;font-size:0.875rem;cursor:pointer}
.sidebar-link:hover,.sidebar-link.active{background:rgba(59,130,246,0.1);color:#3b82f6}
.grad-text{background:linear-gradient(135deg,#60a5fa,#a78bfa);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.status-active{color:#22c55e;background:rgba(34,197,94,0.1)}.status-expired{color:#ef4444;background:rgba(239,68,68,0.1)}
.status-trial{color:#f59e0b;background:rgba(245,158,11,0.1)}
.tab-content{display:none}.tab-content.active{display:block}
.license-key{filter:blur(4px);transition:filter 0.3s;cursor:pointer;user-select:all}
.license-key.revealed{filter:blur(0)}
input:focus{border-color:#3b82f6!important}
</style>
</head>
<body class="min-h-screen text-gray-300">

<!-- Loading -->
<div id="loading" class="min-h-screen flex items-center justify-center">
<div class="text-center">
<div class="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
<p class="text-gray-500 text-sm">Loading portal...</p>
</div></div>

<!-- ═══════════════════════════════════════════════════════════ -->
<!--   AUTH VIEW                                                -->
<!-- ═══════════════════════════════════════════════════════════ -->
<div id="auth-view" class="hidden min-h-screen flex items-center justify-center p-4">
<div class="w-full max-w-md">
<!-- Logo -->
<div class="text-center mb-8">
<a href="/" class="inline-block no-underline"><h1 class="text-2xl font-bold grad-text">__COMPANY__</h1></a>
<p class="text-gray-500 text-sm mt-1">Customer Portal</p>
</div>

<!-- Login Form -->
<div id="login-form" class="glass rounded-2xl p-8">
<h2 class="text-xl font-bold text-white mb-6 text-center">Sign In</h2>
<div id="login-error" class="hidden mb-4 p-3 rounded-lg bg-red-500/10 border border-red-500/30 text-red-400 text-sm text-center"></div>
<div class="space-y-4">
<div><label class="text-xs text-gray-400 block mb-1.5">Email</label>
<input id="login-email" type="email" class="w-full bg-gray-900/80 border border-gray-700 text-white px-4 py-2.5 rounded-lg text-sm outline-none transition" placeholder="you@company.com"></div>
<div><label class="text-xs text-gray-400 block mb-1.5">Password</label>
<input id="login-password" type="password" class="w-full bg-gray-900/80 border border-gray-700 text-white px-4 py-2.5 rounded-lg text-sm outline-none transition" placeholder="Your password" onkeydown="if(event.key==='Enter')doLogin()"></div>
<button id="btn-login" onclick="doLogin()" class="w-full glow-btn py-2.5 rounded-lg text-white text-sm font-medium">Sign In</button>
</div>
<div class="mt-4 text-center text-sm">
<a onclick="showAuthView('forgot')" class="text-blue-400 cursor-pointer hover:underline">Forgot password?</a>
</div>
<div class="mt-4 text-center text-sm text-gray-500">
Don't have an account? <a onclick="showAuthView('register')" class="text-blue-400 cursor-pointer hover:underline">Create one</a>
</div>
</div>

<!-- Register Form -->
<div id="register-form" class="glass rounded-2xl p-8 hidden">
<h2 class="text-xl font-bold text-white mb-6 text-center">Create Account</h2>
<div id="register-error" class="hidden mb-4 p-3 rounded-lg bg-red-500/10 border border-red-500/30 text-red-400 text-sm text-center"></div>
<div class="space-y-4">
<div><label class="text-xs text-gray-400 block mb-1.5">Full Name *</label>
<input id="reg-name" type="text" class="w-full bg-gray-900/80 border border-gray-700 text-white px-4 py-2.5 rounded-lg text-sm outline-none transition" placeholder="John Smith"></div>
<div><label class="text-xs text-gray-400 block mb-1.5">Email *</label>
<input id="reg-email" type="email" class="w-full bg-gray-900/80 border border-gray-700 text-white px-4 py-2.5 rounded-lg text-sm outline-none transition" placeholder="you@company.com"></div>
<div><label class="text-xs text-gray-400 block mb-1.5">Company</label>
<input id="reg-company" type="text" class="w-full bg-gray-900/80 border border-gray-700 text-white px-4 py-2.5 rounded-lg text-sm outline-none transition" placeholder="Your ISP / Company"></div>
<div><label class="text-xs text-gray-400 block mb-1.5">Password * <span class="text-gray-600">(min 6 characters)</span></label>
<input id="reg-password" type="password" class="w-full bg-gray-900/80 border border-gray-700 text-white px-4 py-2.5 rounded-lg text-sm outline-none transition"></div>
<div><label class="text-xs text-gray-400 block mb-1.5">Confirm Password *</label>
<input id="reg-confirm" type="password" class="w-full bg-gray-900/80 border border-gray-700 text-white px-4 py-2.5 rounded-lg text-sm outline-none transition" onkeydown="if(event.key==='Enter')doRegister()"></div>
<button id="btn-register" onclick="doRegister()" class="w-full glow-btn py-2.5 rounded-lg text-white text-sm font-medium">Create Account</button>
</div>
<div class="mt-4 text-center text-sm text-gray-500">
Already have an account? <a onclick="showAuthView('login')" class="text-blue-400 cursor-pointer hover:underline">Sign in</a>
</div>
</div>

<!-- Forgot Password -->
<div id="forgot-form" class="glass rounded-2xl p-8 hidden">
<h2 class="text-xl font-bold text-white mb-6 text-center">Reset Password</h2>
<p class="text-gray-400 text-sm mb-4 text-center">Enter your email and we'll send a password reset link.</p>
<div id="forgot-msg" class="hidden mb-4 p-3 rounded-lg text-sm text-center"></div>
<div class="space-y-4">
<div><label class="text-xs text-gray-400 block mb-1.5">Email</label>
<input id="forgot-email" type="email" class="w-full bg-gray-900/80 border border-gray-700 text-white px-4 py-2.5 rounded-lg text-sm outline-none transition" placeholder="you@company.com" onkeydown="if(event.key==='Enter')doForgotPassword()"></div>
<button id="btn-forgot" onclick="doForgotPassword()" class="w-full glow-btn py-2.5 rounded-lg text-white text-sm font-medium">Send Reset Link</button>
</div>
<div class="mt-4 text-center text-sm text-gray-500">
<a onclick="showAuthView('login')" class="text-blue-400 cursor-pointer hover:underline">&larr; Back to Sign In</a>
</div>
</div>

<!-- Reset Password (after email link click) -->
<div id="reset-form" class="glass rounded-2xl p-8 hidden">
<h2 class="text-xl font-bold text-white mb-6 text-center">Set New Password</h2>
<div id="reset-error" class="hidden mb-4 p-3 rounded-lg bg-red-500/10 border border-red-500/30 text-red-400 text-sm text-center"></div>
<div class="space-y-4">
<div><label class="text-xs text-gray-400 block mb-1.5">New Password</label>
<input id="reset-password" type="password" class="w-full bg-gray-900/80 border border-gray-700 text-white px-4 py-2.5 rounded-lg text-sm outline-none transition" placeholder="Min 6 characters"></div>
<div><label class="text-xs text-gray-400 block mb-1.5">Confirm Password</label>
<input id="reset-confirm" type="password" class="w-full bg-gray-900/80 border border-gray-700 text-white px-4 py-2.5 rounded-lg text-sm outline-none transition" onkeydown="if(event.key==='Enter')doResetPassword()"></div>
<button onclick="doResetPassword()" class="w-full glow-btn py-2.5 rounded-lg text-white text-sm font-medium">Update Password</button>
</div>
</div>
</div></div>

<!-- ═══════════════════════════════════════════════════════════ -->
<!--   DASHBOARD VIEW                                           -->
<!-- ═══════════════════════════════════════════════════════════ -->
<div id="dashboard-view" class="hidden min-h-screen">

<!-- Top Nav -->
<nav class="border-b border-gray-800/50 bg-gray-950/80 backdrop-blur sticky top-0 z-50">
<div class="max-w-7xl mx-auto px-4 sm:px-6 flex items-center justify-between h-14">
<a href="/" class="font-bold grad-text text-lg no-underline">__COMPANY__</a>
<div class="flex items-center gap-4">
<span id="nav-user-name" class="text-gray-400 text-sm hidden sm:block"></span>
<button onclick="doLogout()" class="text-gray-500 hover:text-red-400 text-sm transition">Sign Out</button>
</div></div></nav>

<div class="max-w-7xl mx-auto flex flex-col md:flex-row px-4 sm:px-6">
<!-- Sidebar (desktop) -->
<aside class="hidden md:block w-56 flex-shrink-0 pr-6 pt-8 sticky top-14 self-start">
<nav class="space-y-1">
<a class="sidebar-link active" data-tab="overview" onclick="switchTab('overview')">&#128202; Overview</a>
<a class="sidebar-link" data-tab="licenses" onclick="switchTab('licenses')">&#128273; My Licenses</a>
<a class="sidebar-link" data-tab="subscription" onclick="switchTab('subscription')">&#128179; Subscription</a>
<a class="sidebar-link" data-tab="profile" onclick="switchTab('profile')">&#128100; Profile</a>
</nav>
<div class="mt-8 pt-4 border-t border-gray-800/50">
<a href="/#downloads" class="sidebar-link text-gray-500 no-underline">&#11015; Download App</a>
<a href="mailto:__EMAIL__" class="sidebar-link text-gray-500 no-underline">&#128172; Support</a>
</div></aside>

<!-- Mobile Tabs -->
<div class="md:hidden flex gap-1 pt-4 pb-2 overflow-x-auto w-full">
<button class="mob-tab px-3 py-2 rounded-lg text-xs font-medium whitespace-nowrap bg-blue-500/10 text-blue-400" data-tab="overview" onclick="switchTab('overview')">Overview</button>
<button class="mob-tab px-3 py-2 rounded-lg text-xs font-medium whitespace-nowrap text-gray-400" data-tab="licenses" onclick="switchTab('licenses')">Licenses</button>
<button class="mob-tab px-3 py-2 rounded-lg text-xs font-medium whitespace-nowrap text-gray-400" data-tab="subscription" onclick="switchTab('subscription')">Plans</button>
<button class="mob-tab px-3 py-2 rounded-lg text-xs font-medium whitespace-nowrap text-gray-400" data-tab="profile" onclick="switchTab('profile')">Profile</button>
</div>

<!-- ══════════ Main Content ══════════ -->
<main class="flex-1 py-8 min-w-0">

<!-- ── Overview Tab ── -->
<div id="tab-overview" class="tab-content active">
<h1 class="text-2xl font-bold text-white mb-1">Welcome back, <span id="ov-name" class="grad-text"></span></h1>
<p class="text-gray-500 text-sm mb-6">Here's your account overview.</p>
<div class="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
<div class="glass rounded-xl p-5"><p class="text-gray-500 text-xs mb-1">Total Licenses</p>
<p id="ov-licenses" class="text-3xl font-bold text-white">0</p></div>
<div class="glass rounded-xl p-5"><p class="text-gray-500 text-xs mb-1">Current Plan</p>
<p id="ov-plan" class="text-xl font-bold text-white">&mdash;</p></div>
<div class="glass rounded-xl p-5"><p class="text-gray-500 text-xs mb-1">Account Status</p>
<p id="ov-status" class="text-xl font-bold text-green-400">Active</p></div>
</div>
<h2 class="text-white font-semibold mb-3">Quick Actions</h2>
<div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
<button onclick="switchTab('subscription')" class="glass rounded-xl p-5 text-left hover:border-blue-500/50 transition">
<div class="text-2xl mb-2">&#128179;</div>
<p class="text-white font-medium text-sm">Subscribe / Upgrade</p>
<p class="text-gray-500 text-xs">Get a professional license</p></button>
<button onclick="switchTab('licenses')" class="glass rounded-xl p-5 text-left hover:border-blue-500/50 transition">
<div class="text-2xl mb-2">&#128273;</div>
<p class="text-white font-medium text-sm">View Licenses</p>
<p class="text-gray-500 text-xs">See keys &amp; hardware bindings</p></button>
<a href="/#downloads" class="glass rounded-xl p-5 text-left hover:border-blue-500/50 transition no-underline block">
<div class="text-2xl mb-2">&#11015;</div>
<p class="text-white font-medium text-sm">Download Connexa</p>
<p class="text-gray-500 text-xs">Get the latest installer</p></a>
</div>
<!-- No-license CTA -->
<div id="ov-no-licenses" class="hidden mt-8 glass rounded-xl p-6 text-center border-dashed border-blue-500/30">
<div class="text-4xl mb-3">&#127881;</div>
<h3 class="text-white font-semibold mb-2">Get Started with a Free Trial</h3>
<p class="text-gray-400 text-sm mb-4">Try Connexa free for 7 days. No credit card required.</p>
<button onclick="activateTrialFromPortal()" id="btn-portal-trial" class="glow-btn px-6 py-2.5 rounded-lg text-white text-sm font-medium">Start 7-Day Trial</button>
</div>
</div>

<!-- ── Licenses Tab ── -->
<div id="tab-licenses" class="tab-content">
<div class="flex justify-between items-center mb-6">
<h1 class="text-2xl font-bold text-white">My Licenses</h1>
<span id="lic-count" class="text-gray-400 text-sm"></span></div>
<div id="lic-list" class="space-y-4"></div>
<div id="lic-empty" class="hidden glass rounded-xl p-8 text-center">
<div class="text-4xl mb-3">&#128274;</div>
<p class="text-gray-400 mb-4">You don't have any licenses yet.</p>
<button onclick="switchTab('subscription')" class="glow-btn px-6 py-2 rounded-lg text-white text-sm font-medium">Get a License</button>
</div>
<!-- Link existing license -->
<div class="mt-6 glass rounded-xl p-5">
<h3 class="text-white font-medium text-sm mb-3">Link an Existing License</h3>
<div class="flex gap-2">
<input id="link-key" type="text" class="flex-1 bg-gray-900/80 border border-gray-700 text-white px-4 py-2 rounded-lg text-sm outline-none transition uppercase" placeholder="XXXXX-XXXXX-XXXXX-XXXXX-XXXXX">
<button onclick="linkLicense()" class="glow-btn px-4 py-2 rounded-lg text-white text-sm font-medium">Link</button>
</div></div>
</div>

<!-- ── Subscription Tab ── -->
<div id="tab-subscription" class="tab-content">
<h1 class="text-2xl font-bold text-white mb-6">Subscription</h1>
<!-- Current plan -->
<div class="glass rounded-xl p-6 mb-6">
<div class="flex items-center justify-between mb-3">
<h3 class="text-white font-semibold">Current Plan</h3>
<span id="sub-badge" class="px-3 py-1 rounded-full text-xs font-medium status-trial">No Plan</span>
</div>
<div class="grid grid-cols-2 gap-4 text-sm">
<div><p class="text-gray-500 text-xs">Plan</p><p id="sub-plan" class="text-white font-medium">None</p></div>
<div><p class="text-gray-500 text-xs">Billing</p><p id="sub-cycle" class="text-white font-medium">&mdash;</p></div>
</div>
<p id="sub-expiry" class="text-gray-500 text-xs mt-3"></p>
</div>
<!-- New subscription -->
<div class="glass rounded-xl p-6 mb-6">
<h3 class="text-white font-semibold mb-4">Subscribe to Professional</h3>
<div class="flex gap-3 mb-4">
<button id="sub-monthly-btn" onclick="setSubBilling('monthly')" class="flex-1 py-3 rounded-lg border border-blue-500 text-blue-400 bg-blue-500/10 text-sm font-medium transition">
Monthly<br><span class="text-lg font-bold">R600</span><span class="text-gray-400 text-xs">/mo</span>
</button>
<button id="sub-annual-btn" onclick="setSubBilling('annual')" class="flex-1 py-3 rounded-lg border border-gray-700 text-gray-400 text-sm font-medium transition">
Annual<br><span class="text-lg font-bold">R6,800</span><span class="text-gray-400 text-xs">/yr</span>
</button>
</div>
<div class="flex items-center justify-between mb-4">
<span class="text-gray-400 text-sm">Licenses:</span>
<div class="flex items-center gap-3">
<button onclick="changeSubQty(-1)" class="w-8 h-8 rounded-lg bg-gray-800 text-white flex items-center justify-center hover:bg-gray-700">-</button>
<span id="sub-qty" class="text-white font-bold text-lg w-8 text-center">1</span>
<button onclick="changeSubQty(1)" class="w-8 h-8 rounded-lg bg-gray-800 text-white flex items-center justify-center hover:bg-gray-700">+</button>
</div></div>
<div class="bg-gray-900/50 rounded-lg p-4 mb-4">
<div class="flex justify-between items-center">
<span class="text-gray-400 text-sm">Total</span>
<span id="sub-total" class="text-white text-2xl font-bold">R600</span>
</div>
<p id="sub-breakdown" class="text-gray-500 text-xs mt-1">R600 &times; 1 license(s) &times; 1 month</p>
</div>
<button onclick="subscribePay()" class="w-full glow-btn py-3 rounded-lg text-white font-medium">Pay with PayFast</button>
</div>
<!-- Payment History -->
<div class="glass rounded-xl p-6">
<h3 class="text-white font-semibold mb-3">Payment History</h3>
<div id="pay-history"><p class="text-gray-500 text-sm">No payments yet.</p></div>
</div>
</div>

<!-- ── Profile Tab ── -->
<div id="tab-profile" class="tab-content">
<h1 class="text-2xl font-bold text-white mb-6">Profile</h1>
<div class="glass rounded-xl p-6 mb-6">
<h3 class="text-white font-semibold mb-4">Account Info</h3>
<div class="grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm mb-4">
<div><p class="text-gray-500 text-xs mb-1">Email</p><p id="prof-email" class="text-white">&mdash;</p></div>
<div><p class="text-gray-500 text-xs mb-1">Member since</p><p id="prof-created" class="text-white">&mdash;</p></div>
</div>
<div class="space-y-3">
<div><label class="text-xs text-gray-400 block mb-1">Full Name</label>
<input id="prof-name" type="text" class="w-full bg-gray-900/80 border border-gray-700 text-white px-4 py-2.5 rounded-lg text-sm outline-none transition"></div>
<div><label class="text-xs text-gray-400 block mb-1">Company</label>
<input id="prof-company" type="text" class="w-full bg-gray-900/80 border border-gray-700 text-white px-4 py-2.5 rounded-lg text-sm outline-none transition"></div>
<div><label class="text-xs text-gray-400 block mb-1">Phone</label>
<input id="prof-phone" type="text" class="w-full bg-gray-900/80 border border-gray-700 text-white px-4 py-2.5 rounded-lg text-sm outline-none transition"></div>
<button onclick="saveProfile()" class="glow-btn px-6 py-2.5 rounded-lg text-white text-sm font-medium">Save Changes</button>
</div></div>
<div class="glass rounded-xl p-6">
<h3 class="text-white font-semibold mb-4">Change Password</h3>
<div class="space-y-3">
<div><label class="text-xs text-gray-400 block mb-1">New Password</label>
<input id="prof-newpw" type="password" class="w-full bg-gray-900/80 border border-gray-700 text-white px-4 py-2.5 rounded-lg text-sm outline-none transition" placeholder="Min 6 characters"></div>
<div><label class="text-xs text-gray-400 block mb-1">Confirm Password</label>
<input id="prof-confirmpw" type="password" class="w-full bg-gray-900/80 border border-gray-700 text-white px-4 py-2.5 rounded-lg text-sm outline-none transition" onkeydown="if(event.key==='Enter')changePassword()"></div>
<button onclick="changePassword()" class="px-6 py-2.5 rounded-lg border border-gray-700 text-gray-300 hover:text-white text-sm font-medium transition">Update Password</button>
</div></div>
</div>

</main>
</div></div>

<!-- Toast -->
<div id="toast" class="hidden fixed bottom-6 right-6 px-6 py-3 rounded-lg text-sm font-medium z-50 transition-all"></div>

<!-- ═══════════════════════════════════════════════════════════ -->
<!--   JAVASCRIPT                                               -->
<!-- ═══════════════════════════════════════════════════════════ -->
<script>
const PRICE_MONTHLY=600;
const PRICE_ANNUAL=6800;

let authToken=localStorage.getItem('portal_token')||null;
let currentUser=null;
let portalData=null;
let activeTab='overview';
let subBilling='monthly';
let subQty=1;

// ═══ Helpers ═══

async function api(method,path,body){
  if(!authToken){showAuthView('login');return null}
  const opts={method,headers:{'Content-Type':'application/json','Authorization':'Bearer '+authToken}};
  if(body)opts.body=JSON.stringify(body);
  try{
    const res=await fetch(path,opts);
    if(res.status===401){doLogout();return null}
    const data=await res.json();
    if(!res.ok){showToast(data.detail||'Error','error');return null}
    return data;
  }catch(e){showToast('Connection error','error');return null}
}

function showToast(msg,type){
  const t=document.getElementById('toast');t.textContent=msg;
  t.className='fixed bottom-6 right-6 px-6 py-3 rounded-lg text-sm font-medium z-50 '+(type==='success'?'bg-green-600 text-white':type==='error'?'bg-red-600 text-white':'bg-blue-600 text-white');
  setTimeout(()=>{t.className='hidden fixed bottom-6 right-6'},4000);
}

// ═══ Auth UI ═══

function showAuthView(form){
  document.getElementById('loading').classList.add('hidden');
  document.getElementById('dashboard-view').classList.add('hidden');
  document.getElementById('auth-view').classList.remove('hidden');
  ['login-form','register-form','forgot-form','reset-form'].forEach(f=>
    document.getElementById(f).classList[f===form+'-form'?'remove':'add']('hidden'));
}
function showDashboard(){
  document.getElementById('loading').classList.add('hidden');
  document.getElementById('auth-view').classList.add('hidden');
  document.getElementById('dashboard-view').classList.remove('hidden');
}

// ═══ Auth Actions ═══

async function doLogin(){
  const email=document.getElementById('login-email').value.trim();
  const password=document.getElementById('login-password').value;
  const errEl=document.getElementById('login-error');
  errEl.classList.add('hidden');
  if(!email||!password){errEl.textContent='Please fill in all fields';errEl.classList.remove('hidden');return}
  const btn=document.getElementById('btn-login');
  btn.disabled=true;btn.textContent='Signing in...';
  try{
    const res=await fetch('/api/portal/auth/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email,password})});
    const data=await res.json();
    if(!res.ok){errEl.textContent=data.detail||'Login failed';errEl.classList.remove('hidden');btn.disabled=false;btn.textContent='Sign In';return}
    authToken=data.token;localStorage.setItem('portal_token',authToken);
    currentUser=data.user;
    await loadDashboard();
  }catch(e){errEl.textContent='Connection error';errEl.classList.remove('hidden');btn.disabled=false;btn.textContent='Sign In'}
}

async function doRegister(){
  const full_name=document.getElementById('reg-name').value.trim();
  const email=document.getElementById('reg-email').value.trim();
  const company=document.getElementById('reg-company').value.trim();
  const password=document.getElementById('reg-password').value;
  const confirm=document.getElementById('reg-confirm').value;
  const errEl=document.getElementById('register-error');
  errEl.classList.add('hidden');
  if(!full_name||!email||!password){errEl.textContent='Please fill in required fields';errEl.classList.remove('hidden');return}
  if(password.length<6){errEl.textContent='Password must be at least 6 characters';errEl.classList.remove('hidden');return}
  if(password!==confirm){errEl.textContent='Passwords do not match';errEl.classList.remove('hidden');return}
  const btn=document.getElementById('btn-register');
  btn.disabled=true;btn.textContent='Creating account...';
  try{
    const res=await fetch('/api/portal/auth/register',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email,password,full_name,company})});
    const data=await res.json();
    if(!res.ok){errEl.textContent=data.detail||'Registration failed';errEl.classList.remove('hidden');btn.disabled=false;btn.textContent='Create Account';return}
    authToken=data.token;localStorage.setItem('portal_token',authToken);
    currentUser=data.user;
    await loadDashboard();
  }catch(e){errEl.textContent='Connection error';errEl.classList.remove('hidden');btn.disabled=false;btn.textContent='Create Account'}
}

async function doForgotPassword(){
  const email=document.getElementById('forgot-email').value.trim();
  const msgEl=document.getElementById('forgot-msg');
  if(!email){msgEl.textContent='Please enter your email';msgEl.className='mb-4 p-3 rounded-lg bg-red-500/10 border border-red-500/30 text-red-400 text-sm text-center';return}
  const btn=document.getElementById('btn-forgot');
  btn.disabled=true;btn.textContent='Sending...';
  try{
    const res=await fetch('/api/portal/auth/forgot-password',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email})});
    const data=await res.json();
    msgEl.textContent=data.message||'If that email has an account, a reset link has been sent.';
    msgEl.className='mb-4 p-3 rounded-lg bg-green-500/10 border border-green-500/30 text-green-400 text-sm text-center';
  }catch(e){msgEl.textContent='Connection error';msgEl.className='mb-4 p-3 rounded-lg bg-red-500/10 border border-red-500/30 text-red-400 text-sm text-center'}
  btn.disabled=false;btn.textContent='Send Reset Link';
}

async function doResetPassword(){
  const pw=document.getElementById('reset-password').value;
  const confirm=document.getElementById('reset-confirm').value;
  const errEl=document.getElementById('reset-error');
  errEl.classList.add('hidden');
  if(pw.length<6){errEl.textContent='Password must be at least 6 characters';errEl.classList.remove('hidden');return}
  if(pw!==confirm){errEl.textContent='Passwords do not match';errEl.classList.remove('hidden');return}
  const params=new URLSearchParams(window.location.search);
  const resetToken=params.get('reset_token');
  if(!resetToken){errEl.textContent='Invalid reset link';errEl.classList.remove('hidden');return}
  try{
    const res=await fetch('/api/portal/auth/reset-password',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({reset_token:resetToken,password:pw})});
    const data=await res.json();
    if(!res.ok){errEl.textContent=data.detail||'Reset failed';errEl.classList.remove('hidden');return}
    authToken=data.token;localStorage.setItem('portal_token',authToken);
    window.history.replaceState({},document.title,'/portal');
    showToast('Password updated successfully!','success');
    await loadDashboard();
  }catch(e){errEl.textContent='Connection error';errEl.classList.remove('hidden')}
}

function doLogout(){
  authToken=null;currentUser=null;portalData=null;
  localStorage.removeItem('portal_token');
  showAuthView('login');
}

// ═══ Dashboard Loading ═══

async function loadDashboard(){
  showDashboard();
  const data=await api('GET','/api/portal/me');
  if(!data||!data.customer)return;
  portalData=data;
  const c=data.customer;
  document.getElementById('ov-name').textContent=c.full_name||'there';
  document.getElementById('ov-licenses').textContent=data.stats.total_licenses;
  document.getElementById('ov-plan').textContent=data.stats.current_plan||'No Plan';
  const st=document.getElementById('ov-status');
  st.textContent=c.is_suspended?'Suspended':'Active';
  st.className='text-xl font-bold '+(c.is_suspended?'text-red-400':'text-green-400');
  document.getElementById('ov-no-licenses').classList.toggle('hidden',data.stats.total_licenses>0);
  document.getElementById('prof-email').textContent=c.email;
  document.getElementById('prof-created').textContent=c.created_at?new Date(c.created_at).toLocaleDateString():'—';
  document.getElementById('prof-name').value=c.full_name||'';
  document.getElementById('prof-company').value=c.company||'';
  document.getElementById('prof-phone').value=c.phone||'';
  document.getElementById('nav-user-name').textContent=c.full_name||c.email;
  await loadLicenses();
  await loadSubscription();
}

async function loadLicenses(){
  const data=await api('GET','/api/portal/licenses');
  if(!data)return;
  const list=document.getElementById('lic-list');
  const empty=document.getElementById('lic-empty');
  const count=document.getElementById('lic-count');
  if(!data.licenses||data.licenses.length===0){list.innerHTML='';empty.classList.remove('hidden');count.textContent='0 licenses';return}
  empty.classList.add('hidden');count.textContent=data.licenses.length+' license(s)';
  list.innerHTML=data.licenses.map(l=>{
    const typeCls=l.license_type==='trial'?'status-trial':l.license_type==='annual'?'bg-purple-500/10 text-purple-400':'bg-blue-500/10 text-blue-400';
    const statusCls=l.status==='active'?'status-active':'status-expired';
    const hw=l.hardware_id?'&#128274; '+l.hardware_id.substring(0,16)+'...':'&#9898; Unbound';
    const expDate=l.expires_at?new Date(l.expires_at).toLocaleDateString():'—';
    const creDate=l.created_at?new Date(l.created_at).toLocaleDateString():'—';
    return '<div class="glass rounded-xl p-5"><div class="flex justify-between items-start mb-3"><div>'
      +'<span class="px-2 py-0.5 rounded text-xs font-medium '+typeCls+'">'+l.license_type+'</span>'
      +'<span class="ml-2 px-2 py-0.5 rounded text-xs font-medium '+statusCls+'">'+l.status+'</span>'
      +'</div><p class="text-gray-500 text-xs">'+creDate+'</p></div>'
      +'<p class="license-key font-mono text-cyan-400 text-sm mb-3" onclick="this.classList.toggle(\'revealed\')" title="Click to reveal">'+l.license_key+'</p>'
      +'<div class="grid grid-cols-2 gap-2 text-xs"><div><p class="text-gray-500">Hardware</p><p class="text-white">'+hw+'</p></div>'
      +'<div><p class="text-gray-500">Expires</p><p class="text-white">'+expDate+'</p></div></div></div>';
  }).join('');
}

async function loadSubscription(){
  const data=await api('GET','/api/portal/subscription');if(!data)return;
  if(data.subscription){
    const s=data.subscription;
    document.getElementById('sub-plan').textContent=s.plan.charAt(0).toUpperCase()+s.plan.slice(1);
    document.getElementById('sub-cycle').textContent=s.billing_cycle==='annual'?'Annual billing':s.billing_cycle==='monthly'?'Monthly billing':'7-day trial';
    const b=document.getElementById('sub-badge');b.textContent=s.status;
    b.className='px-3 py-1 rounded-full text-xs font-medium '+(s.status==='active'?'status-active':'status-expired');
    if(s.current_period_end)document.getElementById('sub-expiry').textContent='Period ends: '+new Date(s.current_period_end).toLocaleDateString();
  }
}

// ═══ Actions ═══

async function saveProfile(){
  const name=document.getElementById('prof-name').value.trim();
  const company=document.getElementById('prof-company').value.trim();
  const phone=document.getElementById('prof-phone').value.trim();
  const data=await api('PUT','/api/portal/profile',{full_name:name,company,phone});
  if(data&&data.success){
    showToast('Profile updated!','success');
    document.getElementById('ov-name').textContent=name||'there';
    document.getElementById('nav-user-name').textContent=name||(portalData&&portalData.customer?portalData.customer.email:'');
  }
}

async function changePassword(){
  const pw=document.getElementById('prof-newpw').value;
  const confirm=document.getElementById('prof-confirmpw').value;
  if(pw.length<6){showToast('Password must be at least 6 characters','error');return}
  if(pw!==confirm){showToast('Passwords do not match','error');return}
  try{
    const res=await fetch('/api/portal/auth/change-password',{method:'POST',headers:{'Content-Type':'application/json','Authorization':'Bearer '+authToken},body:JSON.stringify({password:pw})});
    const data=await res.json();
    if(res.ok){showToast('Password updated!','success');document.getElementById('prof-newpw').value='';document.getElementById('prof-confirmpw').value=''}
    else showToast(data.detail||'Error','error');
  }catch(e){showToast('Connection error','error')}
}

async function linkLicense(){
  const key=document.getElementById('link-key').value.trim().toUpperCase();
  if(!key||key.length<10){showToast('Enter a valid license key','error');return}
  const data=await api('POST','/api/portal/link-license',{license_key:key});
  if(data&&data.success){showToast('License linked!','success');document.getElementById('link-key').value='';await loadLicenses();await loadDashboard()}
}

async function activateTrialFromPortal(){
  const btn=document.getElementById('btn-portal-trial');
  btn.disabled=true;btn.textContent='Activating...';
  const data=await api('POST','/api/portal/activate-trial');
  if(data&&data.success){
    showToast('7-day trial activated! Check your email for the license key.','success');
    btn.textContent='Trial Activated!';btn.style.background='#22c55e';
    await loadDashboard();
  }else{btn.disabled=false;btn.textContent='Start 7-Day Trial'}
}

// ═══ Subscription ═══

function setSubBilling(c){
  subBilling=c;
  document.getElementById('sub-monthly-btn').className='flex-1 py-3 rounded-lg border text-sm font-medium transition '+(c==='monthly'?'border-blue-500 text-blue-400 bg-blue-500/10':'border-gray-700 text-gray-400');
  document.getElementById('sub-annual-btn').className='flex-1 py-3 rounded-lg border text-sm font-medium transition '+(c==='annual'?'border-blue-500 text-blue-400 bg-blue-500/10':'border-gray-700 text-gray-400');
  updateSubTotal();
}
function changeSubQty(d){subQty=Math.max(1,Math.min(100,subQty+d));document.getElementById('sub-qty').textContent=subQty;updateSubTotal()}
function updateSubTotal(){
  const p=subBilling==='annual'?PRICE_ANNUAL:PRICE_MONTHLY;const t=p*subQty;
  const period=subBilling==='annual'?'year':'month';
  document.getElementById('sub-total').textContent='R'+t.toLocaleString();
  document.getElementById('sub-breakdown').textContent='R'+p.toLocaleString()+' \\u00d7 '+subQty+' license(s) \\u00d7 1 '+period;
}
async function subscribePay(){
  const data=await api('POST','/api/portal/subscribe',{billing_cycle:subBilling,quantity:subQty});
  if(!data||!data.form_fields){return}
  const form=document.createElement('form');form.method='POST';form.action=data.payfast_url;
  for(const[k,v]of Object.entries(data.form_fields)){
    const inp=document.createElement('input');inp.type='hidden';inp.name=k;inp.value=v;form.appendChild(inp);
  }document.body.appendChild(form);form.submit();
}

// ═══ Tab Navigation ═══

function switchTab(tab){
  activeTab=tab;
  document.querySelectorAll('.tab-content').forEach(t=>t.classList.remove('active'));
  document.getElementById('tab-'+tab).classList.add('active');
  document.querySelectorAll('.sidebar-link').forEach(l=>l.classList.toggle('active',l.dataset&&l.dataset.tab===tab));
  document.querySelectorAll('.mob-tab').forEach(b=>{
    b.className='mob-tab px-3 py-2 rounded-lg text-xs font-medium whitespace-nowrap '+(b.dataset.tab===tab?'bg-blue-500/10 text-blue-400':'text-gray-400');
  });
}

// ═══ Init ═══

(async function init(){
  // Check for password reset token in URL
  const params=new URLSearchParams(window.location.search);
  if(params.get('reset_token')){
    showAuthView('reset');
    return;
  }
  // Check for payment return
  if(params.get('payment')==='success'){
    if(authToken){await loadDashboard();setTimeout(()=>showToast('Payment successful! Your license will appear shortly.','success'),500)}
    else showAuthView('login');
    window.history.replaceState({},document.title,'/portal');
    return;
  }
  if(params.get('payment')==='cancelled'){
    if(authToken){await loadDashboard();setTimeout(()=>showToast('Payment was cancelled.','error'),500)}
    else showAuthView('login');
    window.history.replaceState({},document.title,'/portal');
    return;
  }
  // Check existing session
  if(authToken){
    const data=await api('GET','/api/portal/me');
    if(data&&data.customer){await loadDashboard()}
    else{authToken=null;localStorage.removeItem('portal_token');showAuthView('login')}
  }else{
    showAuthView('login');
  }
})();

setSubBilling('monthly');
</script>
</body>
</html>"""
