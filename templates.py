"""
Connexify Website Templates
All HTML templates for the Connexify website, documentation, and get-started wizard.
Placeholders: __VERSION__, __EMAIL__, __YEAR__, __COMPANY__
"""

# ══════════════════════════════════════════════════════════════════
#   SHARED COMPONENTS
# ══════════════════════════════════════════════════════════════════

_HEAD = """<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<link rel="icon" href="/static/connexa-helmet-logo.png" type="image/png">
<script src="https://cdn.tailwindcss.com"></script>
<script>tailwind.config={theme:{extend:{fontFamily:{sans:['Inter','system-ui','sans-serif']}}}}</script>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet">
<style>
html{scroll-behavior:smooth}
body{background:#030712;color:#e2e8f0;font-family:'Inter',system-ui,sans-serif}
.hero-grad{background:radial-gradient(ellipse at top,#1e3a5f 0%,#030712 70%)}
.grad-text{background:linear-gradient(135deg,#3b82f6,#06b6d4 50%,#10b981);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text}
.card{background:rgba(15,23,42,0.6);backdrop-filter:blur(12px);border:1px solid rgba(71,85,105,0.3);transition:all .3s}
.card:hover{border-color:rgba(59,130,246,0.4);transform:translateY(-4px);box-shadow:0 20px 40px rgba(0,0,0,0.3)}
.glow-btn{background:linear-gradient(135deg,#3b82f6,#06b6d4);transition:all .3s;display:inline-block}
.glow-btn:hover{transform:scale(1.03);box-shadow:0 10px 40px rgba(59,130,246,0.4)}
.glass{background:rgba(30,41,59,0.7);backdrop-filter:blur(12px);border:1px solid rgba(71,85,105,0.3)}
@keyframes float{0%,100%{transform:translateY(0)}50%{transform:translateY(-10px)}}
.float-anim{animation:float 6s ease-in-out infinite}
.faq-body{max-height:0;overflow:hidden;transition:max-height .3s ease}
.faq-body.open{max-height:600px}
.faq-icon{transition:transform .3s}.faq-icon.open{transform:rotate(45deg)}
.step-dot{width:2.5rem;height:2.5rem;border-radius:9999px;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:.875rem;transition:all .3s}
.step-dot.active{background:linear-gradient(135deg,#3b82f6,#06b6d4);color:#fff}
.step-dot.done{background:#059669;color:#fff}
.step-dot.pending{background:#1e293b;color:#64748b;border:2px solid #334155}
.doc-link{display:block;padding:.5rem 1rem;border-radius:.5rem;font-size:.875rem;color:#94a3b8;transition:all .2s}
.doc-link:hover,.doc-link.active{background:rgba(59,130,246,0.1);color:#3b82f6}
</style>"""

_NAV = """<nav class="fixed top-0 w-full z-50 bg-gray-950/80 backdrop-blur-lg border-b border-gray-800/50">
<div class="max-w-7xl mx-auto px-4 sm:px-6 py-3 flex items-center justify-between">
<a href="/" class="flex items-center gap-2.5 no-underline">
<img src="/static/connexa-helmet-logo.png" alt="Connexify" class="w-10 h-10 rounded-lg object-contain">
<div><span class="text-lg font-bold text-white tracking-tight">Connexify</span><span class="text-[9px] text-gray-500 block -mt-1">(Pty) Ltd</span></div>
</a>
<div class="hidden lg:flex items-center gap-6 text-sm text-gray-400">
<a href="/#features" class="hover:text-white transition-colors no-underline">Features</a>
<a href="/#about" class="hover:text-white transition-colors no-underline">About</a>
<a href="/#downloads" class="hover:text-white transition-colors no-underline">Downloads</a>
<a href="/#pricing" class="hover:text-white transition-colors no-underline">Pricing</a>
<a href="/#faq" class="hover:text-white transition-colors no-underline">FAQ</a>
<a href="/#contact" class="hover:text-white transition-colors no-underline">Contact</a>
</div>
<div class="flex items-center gap-3">
<a href="/get-started" class="hidden sm:inline-block glow-btn px-5 py-2 rounded-lg text-white text-sm font-medium no-underline">Get Started</a>
<button id="mob-btn" class="lg:hidden text-gray-400 hover:text-white p-2" aria-label="Menu">
<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"/></svg>
</button>
</div>
</div>
<div id="mob-menu" class="hidden lg:hidden border-t border-gray-800/50 bg-gray-950/95 backdrop-blur-lg">
<div class="px-4 py-4 space-y-1">
<a href="/#features" class="block text-gray-400 hover:text-white py-2 no-underline">Features</a>
<a href="/#about" class="block text-gray-400 hover:text-white py-2 no-underline">About</a>
<a href="/#downloads" class="block text-gray-400 hover:text-white py-2 no-underline">Downloads</a>
<a href="/#pricing" class="block text-gray-400 hover:text-white py-2 no-underline">Pricing</a>
<a href="/#faq" class="block text-gray-400 hover:text-white py-2 no-underline">FAQ</a>
<a href="/#contact" class="block text-gray-400 hover:text-white py-2 no-underline">Contact</a>
<a href="/get-started" class="block glow-btn text-white text-center py-2.5 rounded-lg font-medium mt-2 no-underline">Get Started</a>
</div>
</div>
</nav>"""

_FOOTER = """<footer class="border-t border-gray-800/30 bg-gray-950 pt-16 pb-8">
<div class="max-w-7xl mx-auto px-6">
<div class="grid sm:grid-cols-2 lg:grid-cols-4 gap-10 mb-12">
<div>
<div class="flex items-center gap-2.5 mb-4">
<img src="/static/connexa-helmet-logo.png" alt="" class="w-10 h-10 rounded-lg object-contain">
<span class="text-lg font-bold text-white">Connexify</span>
</div>
<p class="text-sm text-gray-500 leading-relaxed mb-4">Professional network management solutions for ISPs, WISPs and MSPs across South Africa and beyond.</p>
<p class="text-xs text-gray-600">&copy; __YEAR__ __COMPANY__ (Pty) Ltd</p>
</div>
<div>
<h4 class="text-sm font-semibold text-white mb-4">Product</h4>
<ul class="space-y-2 text-sm text-gray-500">
<li><a href="/#features" class="hover:text-gray-300 transition no-underline">Features</a></li>
<li><a href="/#downloads" class="hover:text-gray-300 transition no-underline">Downloads</a></li>
<li><a href="/#pricing" class="hover:text-gray-300 transition no-underline">Pricing</a></li>
<li><a href="/get-started" class="hover:text-gray-300 transition no-underline">Get Started</a></li>
</ul>
</div>
<div>
<h4 class="text-sm font-semibold text-white mb-4">Resources</h4>
<ul class="space-y-2 text-sm text-gray-500">
<li><a href="/#about" class="hover:text-gray-300 transition no-underline">About Connexa</a></li>
<li><a href="/#features" class="hover:text-gray-300 transition no-underline">Features</a></li>
<li><a href="/#downloads" class="hover:text-gray-300 transition no-underline">Downloads</a></li>
<li><a href="/#faq" class="hover:text-gray-300 transition no-underline">FAQ</a></li>
</ul>
</div>
<div>
<h4 class="text-sm font-semibold text-white mb-4">Connect</h4>
<ul class="space-y-2 text-sm text-gray-500">
<li><a href="mailto:__EMAIL__" class="hover:text-gray-300 transition no-underline">__EMAIL__</a></li>
<li><a href="/#contact" class="hover:text-gray-300 transition no-underline">Contact Form</a></li>
<li><a href="/admin" class="hover:text-gray-300 transition no-underline">Admin Portal</a></li>
</ul>
</div>
</div>
<div class="border-t border-gray-800/30 pt-6 flex flex-col sm:flex-row items-center justify-between gap-4">
<p class="text-xs text-gray-600">Built with &#10084; in South Africa &mdash; __COMPANY__ (Pty) Ltd</p>
<div class="flex items-center gap-4 text-xs text-gray-600">
<span>Version __VERSION__</span>
<span>&bull;</span>
<a href="/#about" class="hover:text-gray-400 transition no-underline">About</a>
<span>&bull;</span>
<a href="/admin" class="hover:text-gray-400 transition no-underline">Admin</a>
</div>
</div>
</div>
</footer>
<button id="scroll-top-btn" onclick="window.scrollTo({top:0,behavior:'smooth'})" class="fixed bottom-6 right-6 w-12 h-12 bg-blue-600 hover:bg-blue-500 text-white rounded-full shadow-lg z-40 flex items-center justify-center opacity-0 pointer-events-none transition-all duration-300" aria-label="Scroll to top">
<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 15l7-7 7 7"/></svg>
</button>"""

_SHARED_JS = """<script>
// Mobile menu
document.getElementById('mob-btn')?.addEventListener('click',()=>document.getElementById('mob-menu').classList.toggle('hidden'));
document.querySelectorAll('#mob-menu a').forEach(a=>a.addEventListener('click',()=>document.getElementById('mob-menu').classList.add('hidden')));
// Scroll to top
window.addEventListener('scroll',()=>{const b=document.getElementById('scroll-top-btn');if(!b)return;if(window.scrollY>400){b.style.opacity='1';b.style.pointerEvents='auto'}else{b.style.opacity='0';b.style.pointerEvents='none'}});
</script>"""


# ══════════════════════════════════════════════════════════════════
#   HOMEPAGE
# ══════════════════════════════════════════════════════════════════

WEBSITE_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
""" + _HEAD + """
<title>Connexify (Pty) Ltd - Professional Network Management for ISPs &amp; WISPs</title>
<meta name="description" content="Connexify develops Connexa, a professional network management platform for ISPs, WISPs, and MSPs. Monitor towers, manage devices, automate scripts, track wireless clients.">
</head>
<body>
""" + _NAV + """

<!-- Hero -->
<section class="hero-grad min-h-screen flex items-center pt-20">
<div class="max-w-7xl mx-auto px-6 py-16 lg:py-24 grid lg:grid-cols-2 gap-12 items-center">
<div>
<div class="inline-flex items-center gap-2 bg-blue-500/10 border border-blue-500/20 text-blue-400 px-4 py-1.5 rounded-full text-sm mb-6">
<span class="w-2 h-2 rounded-full bg-green-400 animate-pulse"></span>
Version __VERSION__ Available
</div>
<h1 class="text-4xl sm:text-5xl lg:text-6xl font-extrabold leading-tight mb-6">
<span class="grad-text">Professional</span><br>Network Management
</h1>
<p class="text-lg text-gray-400 leading-relaxed mb-8 max-w-lg">
Monitor your towers, manage devices, automate configurations, and track wireless clients &mdash; all from one powerful dashboard built for ISPs and WISPs.
</p>
<div class="flex flex-wrap gap-4">
<a href="/get-started" class="glow-btn px-8 py-3 rounded-xl text-white font-semibold text-lg no-underline">Get Started Free</a>
<a href="#features" class="px-8 py-3 rounded-xl border border-gray-700 text-gray-300 hover:border-gray-500 hover:text-white transition font-medium no-underline">Learn More &rarr;</a>
</div>
<div class="mt-8 flex items-center gap-6 text-sm text-gray-500">
<span class="flex items-center gap-1.5">&#10003; Free 7-day trial</span>
<span class="flex items-center gap-1.5">&#10003; No credit card needed</span>
</div>
</div>
<div class="hidden lg:flex justify-center">
<div class="float-anim relative">
<div class="w-[420px] h-72 rounded-2xl bg-gradient-to-br from-gray-900 to-gray-800 border border-gray-700 shadow-2xl p-6 space-y-4">
<div class="flex items-center gap-2">
<div class="w-3 h-3 rounded-full bg-red-500"></div>
<div class="w-3 h-3 rounded-full bg-yellow-500"></div>
<div class="w-3 h-3 rounded-full bg-green-500"></div>
<span class="text-xs text-gray-500 ml-2">Connexa Dashboard</span>
</div>
<div class="grid grid-cols-3 gap-3">
<div class="bg-gray-800/80 rounded-lg p-3 text-center"><div class="text-2xl font-bold text-blue-400">24</div><div class="text-[10px] text-gray-500">Towers</div></div>
<div class="bg-gray-800/80 rounded-lg p-3 text-center"><div class="text-2xl font-bold text-green-400">847</div><div class="text-[10px] text-gray-500">Clients</div></div>
<div class="bg-gray-800/80 rounded-lg p-3 text-center"><div class="text-2xl font-bold text-cyan-400">99.8%</div><div class="text-[10px] text-gray-500">Uptime</div></div>
</div>
<div class="space-y-2">
<div class="flex items-center gap-2"><div class="w-2 h-2 rounded-full bg-green-400"></div><span class="text-xs text-gray-400">Tower Alpha &mdash; 32 clients</span><span class="text-xs text-green-400 ml-auto">-62 dBm</span></div>
<div class="flex items-center gap-2"><div class="w-2 h-2 rounded-full bg-green-400"></div><span class="text-xs text-gray-400">Tower Bravo &mdash; 28 clients</span><span class="text-xs text-green-400 ml-auto">-58 dBm</span></div>
<div class="flex items-center gap-2"><div class="w-2 h-2 rounded-full bg-yellow-400"></div><span class="text-xs text-gray-400">Tower Charlie &mdash; 41 clients</span><span class="text-xs text-yellow-400 ml-auto">-74 dBm</span></div>
</div>
</div>
</div>
</div>
</div>
</section>

<!-- Stats -->
<section class="border-t border-gray-800/20 bg-gray-950/60 py-12">
<div class="max-w-5xl mx-auto px-6 grid grid-cols-2 md:grid-cols-4 gap-8 text-center">
<div><div class="text-3xl font-bold text-white counter" data-target="150">0</div><p class="text-sm text-gray-500 mt-1">Towers Managed</p></div>
<div><div class="text-3xl font-bold text-white counter" data-target="3500">0</div><p class="text-sm text-gray-500 mt-1">Devices Monitored</p></div>
<div><div class="text-3xl font-bold text-white">99.9%</div><p class="text-sm text-gray-500 mt-1">Uptime SLA</p></div>
<div><div class="text-3xl font-bold text-white counter" data-target="25">0</div><p class="text-sm text-gray-500 mt-1">ISPs &amp; WISPs</p></div>
</div>
</section>

<!-- Features -->
<section id="features" class="py-20 lg:py-28">
<div class="max-w-7xl mx-auto px-6">
<div class="text-center mb-16">
<h2 class="text-3xl sm:text-4xl font-bold mb-4"><span class="grad-text">Built for ISPs &amp; WISPs</span></h2>
<p class="text-gray-400 text-lg max-w-2xl mx-auto">Everything you need to manage your wireless network infrastructure in one platform.</p>
</div>
<div class="grid sm:grid-cols-2 lg:grid-cols-4 gap-5">
<div class="card rounded-2xl p-6">
<div class="w-12 h-12 rounded-xl bg-blue-500/10 flex items-center justify-center text-2xl mb-4">&#128225;</div>
<h3 class="text-base font-semibold mb-2 text-white">Tower Monitoring</h3>
<p class="text-gray-400 text-sm leading-relaxed">Real-time monitoring of all tower equipment. Signal levels, client counts, uptime, and performance metrics at a glance.</p>
</div>
<div class="card rounded-2xl p-6">
<div class="w-12 h-12 rounded-xl bg-green-500/10 flex items-center justify-center text-2xl mb-4">&#128187;</div>
<h3 class="text-base font-semibold mb-2 text-white">Device Management</h3>
<p class="text-gray-400 text-sm leading-relaxed">Manage MikroTik, Ubiquiti, Cambium, and Mimosa devices. Auto-discovery, firmware tracking, and config backups.</p>
</div>
<div class="card rounded-2xl p-6">
<div class="w-12 h-12 rounded-xl bg-cyan-500/10 flex items-center justify-center text-2xl mb-4">&#128246;</div>
<h3 class="text-base font-semibold mb-2 text-white">Wireless Clients</h3>
<p class="text-gray-400 text-sm leading-relaxed">Track every connected client across all towers. Signal strength, SNR, CCQ, data rates with automatic classification.</p>
</div>
<div class="card rounded-2xl p-6">
<div class="w-12 h-12 rounded-xl bg-purple-500/10 flex items-center justify-center text-2xl mb-4">&#128196;</div>
<h3 class="text-base font-semibold mb-2 text-white">Script Automation</h3>
<p class="text-gray-400 text-sm leading-relaxed">Push RouterOS scripts to devices individually or in bulk. Schedule recurring tasks for automated config management.</p>
</div>
<div class="card rounded-2xl p-6">
<div class="w-12 h-12 rounded-xl bg-orange-500/10 flex items-center justify-center text-2xl mb-4">&#128202;</div>
<h3 class="text-base font-semibold mb-2 text-white">Zabbix Integration</h3>
<p class="text-gray-400 text-sm leading-relaxed">Seamless integration with Zabbix for advanced monitoring, alerting, and historical data analysis across your network.</p>
</div>
<div class="card rounded-2xl p-6">
<div class="w-12 h-12 rounded-xl bg-pink-500/10 flex items-center justify-center text-2xl mb-4">&#128274;</div>
<h3 class="text-base font-semibold mb-2 text-white">Multi-Tenancy</h3>
<p class="text-gray-400 text-sm leading-relaxed">Isolate data by company. Perfect for MSPs managing multiple client networks from a single Connexa instance.</p>
</div>
<div class="card rounded-2xl p-6">
<div class="w-12 h-12 rounded-xl bg-yellow-500/10 flex items-center justify-center text-2xl mb-4">&#128197;</div>
<h3 class="text-base font-semibold mb-2 text-white">Task Scheduler</h3>
<p class="text-gray-400 text-sm leading-relaxed">Schedule firmware upgrades, config changes, and maintenance tasks. Cron-like scheduling with full audit trails.</p>
</div>
<div class="card rounded-2xl p-6">
<div class="w-12 h-12 rounded-xl bg-red-500/10 flex items-center justify-center text-2xl mb-4">&#128232;</div>
<h3 class="text-base font-semibold mb-2 text-white">Email Alerts</h3>
<p class="text-gray-400 text-sm leading-relaxed">Configurable email notifications for device outages, threshold breaches, and scheduled task completions.</p>
</div>
</div>
</div>
</section>

<!-- About -->
<section id="about" class="border-t border-gray-800/20 py-20 bg-gray-950/40">
<div class="max-w-5xl mx-auto px-6">
<div class="text-center mb-12">
<h2 class="text-3xl sm:text-4xl font-bold mb-4"><span class="grad-text">What is Connexa?</span></h2>
<p class="text-gray-400 text-lg max-w-2xl mx-auto">A comprehensive network device management platform designed for ISPs, WISPs and MSPs.</p>
</div>
<div class="grid md:grid-cols-2 gap-8">
<div class="glass rounded-2xl p-8">
<h3 class="text-white font-semibold text-lg mb-4">&#128640; How It Works</h3>
<p class="text-gray-400 text-sm leading-relaxed mb-3">Connexa runs as a desktop application that connects directly to your network devices via SNMP and API. It discovers, monitors, and manages devices from a single dashboard.</p>
<ul class="text-sm text-gray-400 space-y-2">
<li class="flex items-start gap-2"><span class="text-blue-400">&#9679;</span> Install on any Ubuntu/Windows machine on your network</li>
<li class="flex items-start gap-2"><span class="text-blue-400">&#9679;</span> Add your device ranges and let Connexa auto-discover</li>
<li class="flex items-start gap-2"><span class="text-blue-400">&#9679;</span> Monitor wireless clients, signal quality, and bandwidth</li>
<li class="flex items-start gap-2"><span class="text-blue-400">&#9679;</span> Run bulk commands and scripts across multiple devices</li>
<li class="flex items-start gap-2"><span class="text-blue-400">&#9679;</span> Schedule automated backups and maintenance tasks</li>
</ul>
</div>
<div class="glass rounded-2xl p-8">
<h3 class="text-white font-semibold text-lg mb-4">&#127759; Supported Vendors</h3>
<div class="grid grid-cols-2 gap-4 mb-6">
<div class="bg-gray-900/40 rounded-xl p-4 text-center">
<div class="text-2xl mb-2">&#128225;</div>
<p class="text-white text-sm font-medium">MikroTik</p>
<p class="text-gray-500 text-xs">RouterOS API</p>
</div>
<div class="bg-gray-900/40 rounded-xl p-4 text-center">
<div class="text-2xl mb-2">&#128225;</div>
<p class="text-white text-sm font-medium">Ubiquiti</p>
<p class="text-gray-500 text-xs">SNMP / API</p>
</div>
<div class="bg-gray-900/40 rounded-xl p-4 text-center">
<div class="text-2xl mb-2">&#128225;</div>
<p class="text-white text-sm font-medium">Cambium</p>
<p class="text-gray-500 text-xs">SNMP</p>
</div>
<div class="bg-gray-900/40 rounded-xl p-4 text-center">
<div class="text-2xl mb-2">&#128225;</div>
<p class="text-white text-sm font-medium">Mimosa</p>
<p class="text-gray-500 text-xs">SNMP</p>
</div>
</div>
<p class="text-gray-500 text-xs text-center">Plus any SNMP-enabled device via custom templates</p>
</div>
</div>
<div class="mt-10 glass rounded-2xl p-8">
<h3 class="text-white font-semibold text-lg mb-4">&#128218; Quick Start Guide</h3>
<div class="grid sm:grid-cols-4 gap-4">
<div class="text-center">
<div class="w-10 h-10 rounded-full bg-blue-600/20 text-blue-400 font-bold flex items-center justify-center mx-auto mb-2">1</div>
<p class="text-white text-sm font-medium">Download</p>
<p class="text-gray-500 text-xs">Get the DEB or EXE installer</p>
</div>
<div class="text-center">
<div class="w-10 h-10 rounded-full bg-blue-600/20 text-blue-400 font-bold flex items-center justify-center mx-auto mb-2">2</div>
<p class="text-white text-sm font-medium">Install</p>
<p class="text-gray-500 text-xs">Run installer, enter license key</p>
</div>
<div class="text-center">
<div class="w-10 h-10 rounded-full bg-blue-600/20 text-blue-400 font-bold flex items-center justify-center mx-auto mb-2">3</div>
<p class="text-white text-sm font-medium">Configure</p>
<p class="text-gray-500 text-xs">Add device ranges and credentials</p>
</div>
<div class="text-center">
<div class="w-10 h-10 rounded-full bg-blue-600/20 text-blue-400 font-bold flex items-center justify-center mx-auto mb-2">4</div>
<p class="text-white text-sm font-medium">Monitor</p>
<p class="text-gray-500 text-xs">Dashboard shows all your devices</p>
</div>
</div>
<p class="text-gray-500 text-xs text-center mt-6">A comprehensive User Guide is included with every installation &mdash; covers all features, Zabbix integration, troubleshooting and more.</p>
</div>
</div>
</section>

<!-- How It Works -->
<section class="border-t border-gray-800/20 py-20 bg-gray-950/40">
<div class="max-w-5xl mx-auto px-6">
<div class="text-center mb-14">
<h2 class="text-3xl sm:text-4xl font-bold mb-4"><span class="grad-text">How It Works</span></h2>
<p class="text-gray-400 text-lg">Get up and running in minutes, not days.</p>
</div>
<div class="grid sm:grid-cols-2 lg:grid-cols-4 gap-8">
<div class="text-center">
<div class="w-14 h-14 rounded-2xl bg-blue-600 text-white text-xl font-bold flex items-center justify-center mx-auto mb-4">1</div>
<h3 class="text-white font-semibold mb-2">Download</h3>
<p class="text-gray-400 text-sm">Download the installer for your platform &mdash; Debian/Ubuntu .deb or Windows .exe.</p>
</div>
<div class="text-center">
<div class="w-14 h-14 rounded-2xl bg-cyan-600 text-white text-xl font-bold flex items-center justify-center mx-auto mb-4">2</div>
<h3 class="text-white font-semibold mb-2">Install</h3>
<p class="text-gray-400 text-sm">Run the installer. On Linux: <code class="text-cyan-400 text-xs">sudo dpkg -i connexa_*.deb</code></p>
</div>
<div class="text-center">
<div class="w-14 h-14 rounded-2xl bg-green-600 text-white text-xl font-bold flex items-center justify-center mx-auto mb-4">3</div>
<h3 class="text-white font-semibold mb-2">Configure</h3>
<p class="text-gray-400 text-sm">Add your devices via RouterOS API or SNMP. Connexa auto-discovers your network.</p>
</div>
<div class="text-center">
<div class="w-14 h-14 rounded-2xl bg-emerald-600 text-white text-xl font-bold flex items-center justify-center mx-auto mb-4">4</div>
<h3 class="text-white font-semibold mb-2">Monitor</h3>
<p class="text-gray-400 text-sm">Watch your network come alive. Real-time dashboards, alerts, and automation.</p>
</div>
</div>
<div class="text-center mt-10">
<a href="/get-started" class="glow-btn px-8 py-3 rounded-xl text-white font-semibold no-underline">Start Setup &rarr;</a>
</div>
</div>
</section>

<!-- Downloads -->
<section id="downloads" class="border-t border-gray-800/20 py-20">
<div class="max-w-5xl mx-auto px-6">
<div class="text-center mb-12">
<h2 class="text-3xl sm:text-4xl font-bold mb-4"><span class="grad-text">Download Connexa</span></h2>
<p class="text-gray-400 text-lg">Version __VERSION__ &mdash; Available for Linux &amp; Windows</p>
</div>
<div class="grid md:grid-cols-2 gap-6 max-w-3xl mx-auto">
<div class="glass rounded-2xl p-8 text-center hover:border-blue-500/40 transition-all">
<div class="text-5xl mb-4">&#128039;</div>
<h3 class="text-xl font-semibold mb-2 text-white">Debian / Ubuntu</h3>
<p class="text-gray-400 text-sm mb-1">connexa___VERSION___amd64.deb</p>
<p class="text-gray-500 text-xs mb-6">Ubuntu 22.04+ / Debian 11+</p>
<a href="/static/connexa___VERSION___amd64.deb" class="glow-btn py-3 px-8 rounded-xl text-white font-medium no-underline">&#11015; Download .deb</a>
<p class="text-gray-600 text-xs mt-4">Install: <code class="bg-gray-800 px-2 py-0.5 rounded text-gray-400">sudo dpkg -i connexa_*.deb</code></p>
</div>
<div class="glass rounded-2xl p-8 text-center hover:border-blue-500/40 transition-all">
<div class="text-5xl mb-4">&#128187;</div>
<h3 class="text-xl font-semibold mb-2 text-white">Windows</h3>
<p class="text-gray-400 text-sm mb-1">Connexa-Setup-__VERSION__.exe</p>
<p class="text-gray-500 text-xs mb-6">Windows 10 / 11 (64-bit)</p>
<a href="/static/Connexa-Setup-__VERSION__.exe" class="glow-btn py-3 px-8 rounded-xl text-white font-medium no-underline">&#11015; Download .exe</a>
<p class="text-gray-600 text-xs mt-4">Run installer and follow the setup wizard</p>
</div>
</div>
<div class="text-center mt-8 text-gray-500 text-sm">
Need a license key? <a href="/get-started" class="text-blue-400 hover:underline no-underline">Get started</a> or email <a href="mailto:__EMAIL__" class="text-blue-400 hover:underline no-underline">__EMAIL__</a>
</div>
</div>
</section>

<!-- Pricing -->
<section id="pricing" class="border-t border-gray-800/20 py-20 bg-gray-950/40">
<div class="max-w-5xl mx-auto px-6">
<div class="text-center mb-12">
<h2 class="text-3xl sm:text-4xl font-bold mb-4"><span class="grad-text">Simple, Transparent Pricing</span></h2>
<p class="text-gray-400 text-lg">Start free. Upgrade when you're ready.</p>
</div>
<div class="grid md:grid-cols-3 gap-6">
<!-- Trial -->
<div class="card rounded-2xl p-8">
<h3 class="text-lg font-semibold text-gray-400 mb-2">Trial</h3>
<div class="text-4xl font-bold text-white mb-1">Free</div>
<p class="text-gray-500 text-sm mb-6">7-day full access</p>
<ul class="space-y-3 text-sm text-gray-400 mb-8">
<li class="flex items-start gap-2"><span class="text-green-400 mt-0.5">&#10003;</span> Up to 10 devices</li>
<li class="flex items-start gap-2"><span class="text-green-400 mt-0.5">&#10003;</span> All features included</li>
<li class="flex items-start gap-2"><span class="text-green-400 mt-0.5">&#10003;</span> Email support</li>
<li class="flex items-start gap-2"><span class="text-green-400 mt-0.5">&#10003;</span> No credit card needed</li>
</ul>
<a href="/get-started?plan=trial" class="block text-center py-3 rounded-lg border border-gray-700 text-gray-300 hover:border-blue-500 hover:text-white transition text-sm font-medium no-underline">Start Free Trial</a>
</div>
<!-- Professional -->
<div class="card rounded-2xl p-8 border-blue-500/30 relative">
<div class="absolute -top-3 left-1/2 -translate-x-1/2 bg-blue-600 text-white text-xs font-semibold px-3 py-1 rounded-full">Most Popular</div>
<h3 class="text-lg font-semibold text-blue-400 mb-2">Professional</h3>
<div class="text-4xl font-bold text-white mb-1">R600<span class="text-lg text-gray-500">/mo</span></div>
<p class="text-gray-500 text-sm mb-2">Per license &bull; R6 800/yr (save R400)</p>
<div class="bg-emerald-500/10 border border-emerald-500/20 rounded-lg px-3 py-2 mb-6">
<p class="text-emerald-400 text-xs font-medium">&#9889; Pay securely online with PayFast</p>
</div>
<ul class="space-y-3 text-sm text-gray-400 mb-8">
<li class="flex items-start gap-2"><span class="text-green-400 mt-0.5">&#10003;</span> Unlimited devices</li>
<li class="flex items-start gap-2"><span class="text-green-400 mt-0.5">&#10003;</span> All features included</li>
<li class="flex items-start gap-2"><span class="text-green-400 mt-0.5">&#10003;</span> Priority support</li>
<li class="flex items-start gap-2"><span class="text-green-400 mt-0.5">&#10003;</span> Zabbix integration</li>
<li class="flex items-start gap-2"><span class="text-green-400 mt-0.5">&#10003;</span> Email alerts</li>
</ul>
<a href="/get-started?plan=professional" class="glow-btn block text-center py-3 rounded-lg text-white text-sm font-medium no-underline">Get Started</a>
</div>
<!-- Enterprise -->
<div class="card rounded-2xl p-8">
<h3 class="text-lg font-semibold text-gray-400 mb-2">Enterprise</h3>
<div class="text-4xl font-bold text-white mb-1">Custom</div>
<p class="text-gray-500 text-sm mb-6">Multi-tenant / MSP</p>
<ul class="space-y-3 text-sm text-gray-400 mb-8">
<li class="flex items-start gap-2"><span class="text-green-400 mt-0.5">&#10003;</span> Multi-company support</li>
<li class="flex items-start gap-2"><span class="text-green-400 mt-0.5">&#10003;</span> White-label branding</li>
<li class="flex items-start gap-2"><span class="text-green-400 mt-0.5">&#10003;</span> Dedicated account manager</li>
<li class="flex items-start gap-2"><span class="text-green-400 mt-0.5">&#10003;</span> On-premises deployment</li>
<li class="flex items-start gap-2"><span class="text-green-400 mt-0.5">&#10003;</span> Custom integrations</li>
</ul>
<a href="/get-started?plan=enterprise" class="block text-center py-3 rounded-lg border border-gray-700 text-gray-300 hover:border-blue-500 hover:text-white transition text-sm font-medium no-underline">Contact Sales</a>
</div>
</div>
</div>
</section>

<!-- FAQ -->
<section id="faq" class="border-t border-gray-800/20 py-20">
<div class="max-w-3xl mx-auto px-6">
<div class="text-center mb-12">
<h2 class="text-3xl sm:text-4xl font-bold mb-4"><span class="grad-text">Frequently Asked Questions</span></h2>
</div>
<div class="space-y-3" id="faq-list">
<div class="glass rounded-xl overflow-hidden">
<button class="w-full flex items-center justify-between px-6 py-4 text-left" onclick="toggleFaq(this)">
<span class="text-white font-medium text-sm">What devices does Connexa support?</span>
<span class="faq-icon text-gray-400 text-xl font-light">+</span>
</button>
<div class="faq-body px-6 text-sm text-gray-400 leading-relaxed"><div class="pb-4">Connexa supports MikroTik (RouterOS via API), Ubiquiti (UniFi &amp; airMAX), Cambium, and Mimosa devices. Any SNMP-capable device can also be monitored. We continuously add support for more vendors.</div></div>
</div>
<div class="glass rounded-xl overflow-hidden">
<button class="w-full flex items-center justify-between px-6 py-4 text-left" onclick="toggleFaq(this)">
<span class="text-white font-medium text-sm">How does the free trial work?</span>
<span class="faq-icon text-gray-400 text-xl font-light">+</span>
</button>
<div class="faq-body px-6 text-sm text-gray-400 leading-relaxed"><div class="pb-4">Download and install Connexa. You get 7 days of full access to all features with up to 10 devices. No credit card required. When you're ready, purchase a professional license to unlock unlimited devices.</div></div>
</div>
<div class="glass rounded-xl overflow-hidden">
<button class="w-full flex items-center justify-between px-6 py-4 text-left" onclick="toggleFaq(this)">
<span class="text-white font-medium text-sm">Can I pay with PayFast?</span>
<span class="faq-icon text-gray-400 text-xl font-light">+</span>
</button>
<div class="faq-body px-6 text-sm text-gray-400 leading-relaxed"><div class="pb-4">Yes! We support PayFast for secure online payments. Licenses are R600 per month or R6 800 per year (save R400). You can choose how many licenses you need and select monthly or annual billing. Pay with credit card, debit card, instant EFT, or other methods supported by PayFast. Select PayFast as your payment method during checkout in the Get Started wizard.</div></div>
</div>
<div class="glass rounded-xl overflow-hidden">
<button class="w-full flex items-center justify-between px-6 py-4 text-left" onclick="toggleFaq(this)">
<span class="text-white font-medium text-sm">What happens when my license expires?</span>
<span class="faq-icon text-gray-400 text-xl font-light">+</span>
</button>
<div class="faq-body px-6 text-sm text-gray-400 leading-relaxed"><div class="pb-4">Connexa has a 30-day offline grace period. After your license expires, the application continues working for 30 days while you renew. After that, monitoring features are paused until renewal.</div></div>
</div>
<div class="glass rounded-xl overflow-hidden">
<button class="w-full flex items-center justify-between px-6 py-4 text-left" onclick="toggleFaq(this)">
<span class="text-white font-medium text-sm">Is my data secure?</span>
<span class="faq-icon text-gray-400 text-xl font-light">+</span>
</button>
<div class="faq-body px-6 text-sm text-gray-400 leading-relaxed"><div class="pb-4">Absolutely. Connexa runs on YOUR server &mdash; your data never leaves your network. Device credentials are encrypted at rest. Multi-tenancy ensures complete data isolation between companies.</div></div>
</div>
<div class="glass rounded-xl overflow-hidden">
<button class="w-full flex items-center justify-between px-6 py-4 text-left" onclick="toggleFaq(this)">
<span class="text-white font-medium text-sm">Do you offer custom deployments?</span>
<span class="faq-icon text-gray-400 text-xl font-light">+</span>
</button>
<div class="faq-body px-6 text-sm text-gray-400 leading-relaxed"><div class="pb-4">Yes. Our Enterprise plan includes on-premises deployment, custom branding, dedicated support, and integrations tailored to your infrastructure. Contact us at __EMAIL__ to discuss your needs.</div></div>
</div>
</div>
</div>
</section>

<!-- Contact -->
<section id="contact" class="border-t border-gray-800/20 py-20 bg-gray-950/40">
<div class="max-w-4xl mx-auto px-6">
<div class="text-center mb-12">
<h2 class="text-3xl sm:text-4xl font-bold mb-4"><span class="grad-text">Get in Touch</span></h2>
<p class="text-gray-400 text-lg">Questions? Need a demo? We'd love to hear from you.</p>
</div>
<div class="grid lg:grid-cols-5 gap-8">
<div class="lg:col-span-3">
<form id="contact-form" class="glass rounded-2xl p-8 space-y-5">
<div class="grid sm:grid-cols-2 gap-4">
<div>
<label class="text-xs text-gray-400 block mb-1.5">Full Name *</label>
<input id="cf-name" type="text" required class="w-full bg-gray-900/80 border border-gray-700 text-white px-4 py-2.5 rounded-lg text-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500/20 outline-none transition">
</div>
<div>
<label class="text-xs text-gray-400 block mb-1.5">Email *</label>
<input id="cf-email" type="email" required class="w-full bg-gray-900/80 border border-gray-700 text-white px-4 py-2.5 rounded-lg text-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500/20 outline-none transition">
</div>
</div>
<div class="grid sm:grid-cols-2 gap-4">
<div>
<label class="text-xs text-gray-400 block mb-1.5">Company</label>
<input id="cf-company" type="text" class="w-full bg-gray-900/80 border border-gray-700 text-white px-4 py-2.5 rounded-lg text-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500/20 outline-none transition">
</div>
<div>
<label class="text-xs text-gray-400 block mb-1.5">Subject</label>
<select id="cf-subject" class="w-full bg-gray-900/80 border border-gray-700 text-white px-4 py-2.5 rounded-lg text-sm focus:border-blue-500 outline-none transition">
<option value="General Inquiry">General Inquiry</option>
<option value="Sales">Sales / Pricing</option>
<option value="Support">Technical Support</option>
<option value="Enterprise">Enterprise Plan</option>
<option value="Partnership">Partnership</option>
</select>
</div>
</div>
<div>
<label class="text-xs text-gray-400 block mb-1.5">Message *</label>
<textarea id="cf-message" rows="4" required class="w-full bg-gray-900/80 border border-gray-700 text-white px-4 py-2.5 rounded-lg text-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500/20 outline-none transition resize-none"></textarea>
</div>
<button type="submit" class="glow-btn w-full py-3 rounded-lg text-white font-medium text-sm">Send Message</button>
<p id="cf-result" class="text-sm text-center hidden"></p>
</form>
</div>
<div class="lg:col-span-2 space-y-4">
<div class="glass rounded-2xl p-6">
<div class="text-2xl mb-2">&#9993;</div>
<h3 class="text-white font-medium mb-1">Email</h3>
<a href="mailto:__EMAIL__" class="text-blue-400 hover:underline text-sm no-underline">__EMAIL__</a>
</div>
<div class="glass rounded-2xl p-6">
<div class="text-2xl mb-2">&#128222;</div>
<h3 class="text-white font-medium mb-1">Response Time</h3>
<p class="text-gray-400 text-sm">Within 24 hours on business days</p>
</div>
<div class="glass rounded-2xl p-6">
<div class="text-2xl mb-2">&#127470;&#127462;</div>
<h3 class="text-white font-medium mb-1">Location</h3>
<p class="text-gray-400 text-sm">South Africa</p>
</div>
</div>
</div>
</div>
</section>

""" + _FOOTER + """

""" + _SHARED_JS + """
<script>
// FAQ toggle
function toggleFaq(btn){
  const body=btn.nextElementSibling;
  const icon=btn.querySelector('.faq-icon');
  body.classList.toggle('open');
  icon.classList.toggle('open');
}
// Contact form
document.getElementById('contact-form')?.addEventListener('submit', async(e)=>{
  e.preventDefault();
  const btn=e.target.querySelector('button[type=submit]');
  const res=document.getElementById('cf-result');
  btn.textContent='Sending...';btn.disabled=true;
  try{
    const r=await fetch('/api/contact',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({
      name:document.getElementById('cf-name').value,
      email:document.getElementById('cf-email').value,
      company:document.getElementById('cf-company').value,
      subject:document.getElementById('cf-subject').value,
      message:document.getElementById('cf-message').value
    })});
    const d=await r.json();
    res.textContent=d.message;res.className='text-sm text-center text-green-400';res.classList.remove('hidden');
    e.target.reset();
  }catch(err){
    res.textContent='Something went wrong. Please email us directly.';res.className='text-sm text-center text-red-400';res.classList.remove('hidden');
  }
  btn.textContent='Send Message';btn.disabled=false;
});
// Counter animation
const counters=document.querySelectorAll('.counter');
const io=new IntersectionObserver(entries=>{entries.forEach(ent=>{if(ent.isIntersecting){
  const el=ent.target,target=+el.dataset.target;let n=0;const step=Math.ceil(target/60);
  const timer=setInterval(()=>{n+=step;if(n>=target){n=target;clearInterval(timer)}el.textContent=n.toLocaleString()},20);
  io.unobserve(el);
}})},{threshold:0.5});
counters.forEach(c=>io.observe(c));
</script>
</body>
</html>"""


# ══════════════════════════════════════════════════════════════════
#   GET STARTED WIZARD
# ══════════════════════════════════════════════════════════════════

GET_STARTED_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
""" + _HEAD + """
<title>Get Started with Connexa - __COMPANY__</title>
</head>
<body>
""" + _NAV + """

<div class="max-w-4xl mx-auto px-6 pt-28 pb-20">
<div class="text-center mb-10">
<h1 class="text-3xl sm:text-4xl font-bold mb-3"><span class="grad-text">Get Started with Connexa</span></h1>
<p class="text-gray-400">Follow these steps to set up your network management platform.</p>
</div>

<!-- Step Indicator -->
<div class="flex items-center justify-center gap-2 mb-12">
<div class="step-dot active" id="sd-1">1</div><div class="w-8 h-px bg-gray-700"></div>
<div class="step-dot pending" id="sd-2">2</div><div class="w-8 h-px bg-gray-700"></div>
<div class="step-dot pending" id="sd-3">3</div><div class="w-8 h-px bg-gray-700"></div>
<div class="step-dot pending" id="sd-4">4</div><div class="w-8 h-px bg-gray-700"></div>
<div class="step-dot pending" id="sd-5">5</div>
</div>

<!-- Step 1: Choose Plan -->
<div id="step-1" class="step-panel">
<h2 class="text-xl font-bold text-white mb-6 text-center">Step 1: Choose Your Plan</h2>
<div class="grid md:grid-cols-3 gap-4">
<button onclick="selectPlan('trial')" class="plan-card glass rounded-xl p-6 text-left hover:border-blue-500/50 transition" data-plan="trial">
<h3 class="text-white font-semibold mb-1">Trial</h3>
<div class="text-2xl font-bold text-white mb-1">Free</div>
<p class="text-gray-500 text-xs mb-3">7 days &bull; Up to 10 devices</p>
<ul class="text-xs text-gray-400 space-y-1">
<li>&#10003; All features</li>
<li>&#10003; No credit card</li>
<li>&#10003; Email support</li>
</ul>
</button>
<button onclick="selectPlan('professional')" class="plan-card glass rounded-xl p-6 text-left hover:border-blue-500/50 transition border-blue-500/30" data-plan="professional">
<div class="text-[10px] text-blue-400 font-semibold mb-1">RECOMMENDED</div>
<h3 class="text-white font-semibold mb-1">Professional</h3>
<div class="text-2xl font-bold text-white mb-1">R600<span class="text-sm text-gray-500">/mo</span></div>
<p class="text-gray-500 text-xs mb-3">Per license &bull; R6 800/yr</p>
<ul class="text-xs text-gray-400 space-y-1">
<li>&#10003; Everything in Trial</li>
<li>&#10003; Priority support</li>
<li>&#10003; Zabbix integration</li>
<li>&#9889; PayFast secure checkout</li>
</ul>
</button>
<button onclick="selectPlan('enterprise')" class="plan-card glass rounded-xl p-6 text-left hover:border-blue-500/50 transition" data-plan="enterprise">
<h3 class="text-white font-semibold mb-1">Enterprise</h3>
<div class="text-2xl font-bold text-white mb-1">Custom</div>
<p class="text-gray-500 text-xs mb-3">Multi-tenant / MSP</p>
<ul class="text-xs text-gray-400 space-y-1">
<li>&#10003; Multi-company</li>
<li>&#10003; White-label</li>
<li>&#10003; Dedicated support</li>
</ul>
</button>
</div>
<div class="mt-8 flex justify-end">
<button onclick="nextStep(2)" id="btn-next-1" class="glow-btn px-8 py-2.5 rounded-lg text-white text-sm font-medium opacity-50 pointer-events-none">Next &rarr;</button>
</div>
</div>

<!-- Step 2: Your Details -->
<div id="step-2" class="step-panel hidden">
<h2 class="text-xl font-bold text-white mb-6 text-center">Step 2: Your Details</h2>
<div class="max-w-md mx-auto glass rounded-2xl p-8 space-y-4">
<div>
<label class="text-xs text-gray-400 block mb-1.5">Full Name *</label>
<input id="gs-name" type="text" required class="w-full bg-gray-900/80 border border-gray-700 text-white px-4 py-2.5 rounded-lg text-sm focus:border-blue-500 outline-none transition">
</div>
<div>
<label class="text-xs text-gray-400 block mb-1.5">Email *</label>
<input id="gs-email" type="email" required class="w-full bg-gray-900/80 border border-gray-700 text-white px-4 py-2.5 rounded-lg text-sm focus:border-blue-500 outline-none transition">
</div>
<div>
<label class="text-xs text-gray-400 block mb-1.5">Company Name</label>
<input id="gs-company" type="text" class="w-full bg-gray-900/80 border border-gray-700 text-white px-4 py-2.5 rounded-lg text-sm focus:border-blue-500 outline-none transition">
</div>
<div>
<label class="text-xs text-gray-400 block mb-1.5">Number of Devices (approx)</label>
<select id="gs-devices" class="w-full bg-gray-900/80 border border-gray-700 text-white px-4 py-2.5 rounded-lg text-sm focus:border-blue-500 outline-none transition">
<option>1-10</option><option>11-50</option><option>51-200</option><option>200+</option>
</select>
</div>
</div>
<div class="mt-8 flex justify-between">
<button onclick="prevStep(1)" class="px-6 py-2.5 rounded-lg border border-gray-700 text-gray-400 hover:text-white hover:border-gray-500 text-sm transition">&larr; Back</button>
<button onclick="nextStep(3)" class="glow-btn px-8 py-2.5 rounded-lg text-white text-sm font-medium">Next &rarr;</button>
</div>
</div>

<!-- Step 3: Payment -->
<div id="step-3" class="step-panel hidden">
<h2 class="text-xl font-bold text-white mb-6 text-center">Step 3: Payment</h2>

<!-- Trial: generate license & email -->
<div id="pay-trial" class="hidden max-w-md mx-auto glass rounded-2xl p-8 text-center">
<div class="text-5xl mb-4">&#127881;</div>
<h3 class="text-white font-semibold text-lg mb-2">No Payment Required!</h3>
<p class="text-gray-400 text-sm mb-4">Your 7-day trial is completely free. No credit card needed.</p>
<p class="text-gray-400 text-sm mb-6">Click below to generate your trial license key &mdash; it will be emailed to you instantly.</p>
<div id="trial-status" class="hidden mb-4 p-3 rounded-lg text-sm"></div>
<button id="btn-activate-trial" onclick="activateTrial()" class="glow-btn px-8 py-2.5 rounded-lg text-white text-sm font-medium">Activate Free Trial &rarr;</button>
</div>

<!-- Enterprise: contact us -->
<div id="pay-enterprise" class="hidden max-w-md mx-auto glass rounded-2xl p-8 text-center">
<div class="text-5xl mb-4">&#128188;</div>
<h3 class="text-white font-semibold text-lg mb-2">Let's Talk</h3>
<p class="text-gray-400 text-sm mb-4">Enterprise pricing is customized to your needs. We'll reach out within 24 hours to discuss your requirements.</p>
<a href="mailto:__EMAIL__?subject=Enterprise%20Inquiry" class="glow-btn px-8 py-2.5 rounded-lg text-white text-sm font-medium no-underline">Email Us: __EMAIL__</a>
</div>

<!-- Professional: payment options -->
<div id="pay-professional" class="hidden max-w-lg mx-auto space-y-4">
<div class="glass rounded-2xl p-6 mb-6">
<p class="text-gray-400 text-sm text-center mb-4">Professional License</p>

<!-- Quantity selector -->
<div class="flex items-center justify-between bg-gray-900/40 rounded-xl p-4 mb-3">
<div>
<label class="text-white text-sm font-medium">Number of Licenses</label>
<p class="text-gray-500 text-[11px]">Each license activates one installation</p>
</div>
<div class="flex items-center gap-3">
<button onclick="changeQty(-1)" class="w-8 h-8 rounded-lg bg-gray-800 border border-gray-700 text-white text-lg flex items-center justify-center hover:border-blue-500 transition">-</button>
<span id="qty-display" class="text-white font-bold text-lg w-8 text-center">1</span>
<button onclick="changeQty(1)" class="w-8 h-8 rounded-lg bg-gray-800 border border-gray-700 text-white text-lg flex items-center justify-center hover:border-blue-500 transition">+</button>
</div>
</div>

<!-- Billing cycle selector -->
<div class="bg-gray-900/40 rounded-xl p-4 mb-4">
<label class="text-white text-sm font-medium block mb-3">Billing Cycle</label>
<div class="grid grid-cols-2 gap-3">
<button onclick="setBilling('monthly')" id="btn-monthly" class="billing-opt rounded-xl p-3 text-center border-2 border-blue-500 bg-blue-500/10 transition">
<div class="text-white font-bold text-lg">R600</div>
<div class="text-gray-400 text-xs">per month</div>
</button>
<button onclick="setBilling('annual')" id="btn-annual" class="billing-opt rounded-xl p-3 text-center border-2 border-gray-700 hover:border-blue-500/50 transition">
<div class="text-white font-bold text-lg">R6 800</div>
<div class="text-gray-400 text-xs">per year</div>
<div class="text-emerald-400 text-[10px] font-medium mt-0.5">Save R400/yr</div>
</button>
</div>
</div>

<!-- Price summary -->
<div class="border-t border-gray-700/50 pt-4">
<div class="flex justify-between text-sm text-gray-400 mb-1">
<span id="price-breakdown">R600 &times; 1 license(s) &times; 1 month</span>
</div>
<div class="flex justify-between items-end">
<span class="text-gray-400 text-sm">Total</span>
<span id="price-total" class="text-3xl font-bold text-white">R600</span>
</div>
</div>
<p class="text-gray-500 text-xs text-center mt-3">Unlimited devices per license &bull; All features &bull; Priority support</p>
</div>

<p class="text-center text-sm text-gray-400 mb-4">Choose your payment method:</p>

<!-- PayFast -->
<button onclick="selectPayment('payfast')" class="pay-opt w-full glass rounded-xl p-5 flex items-center gap-4 text-left hover:border-emerald-500/40 transition" data-method="payfast">
<div class="w-12 h-12 rounded-xl bg-emerald-500/10 flex items-center justify-center text-2xl flex-shrink-0">&#9889;</div>
<div class="flex-1">
<h4 class="text-white font-medium text-sm">PayFast</h4>
<p class="text-emerald-400 text-xs">Credit card, debit card, instant EFT &amp; more</p>
<p class="text-gray-500 text-[11px] mt-0.5">Secure payment powered by PayFast</p>
</div>
<div class="w-5 h-5 rounded-full border-2 border-gray-600 flex-shrink-0 pay-radio"></div>
</button>

<!-- EFT -->
<button onclick="selectPayment('eft')" class="pay-opt w-full glass rounded-xl p-5 flex items-center gap-4 text-left hover:border-blue-500/40 transition" data-method="eft">
<div class="w-12 h-12 rounded-xl bg-blue-500/10 flex items-center justify-center text-2xl flex-shrink-0">&#127974;</div>
<div class="flex-1">
<h4 class="text-white font-medium text-sm">EFT / Bank Transfer</h4>
<p class="text-gray-400 text-xs">Direct bank deposit</p>
<p class="text-gray-500 text-[11px] mt-0.5">We'll email banking details</p>
</div>
<div class="w-5 h-5 rounded-full border-2 border-gray-600 flex-shrink-0 pay-radio"></div>
</button>

<!-- Email Invoice -->
<button onclick="selectPayment('invoice')" class="pay-opt w-full glass rounded-xl p-5 flex items-center gap-4 text-left hover:border-purple-500/40 transition" data-method="invoice">
<div class="w-12 h-12 rounded-xl bg-purple-500/10 flex items-center justify-center text-2xl flex-shrink-0">&#128231;</div>
<div class="flex-1">
<h4 class="text-white font-medium text-sm">Request Invoice</h4>
<p class="text-gray-400 text-xs">We'll email a formal invoice</p>
<p class="text-gray-500 text-[11px] mt-0.5">Ideal for company procurement</p>
</div>
<div class="w-5 h-5 rounded-full border-2 border-gray-600 flex-shrink-0 pay-radio"></div>
</button>

<div id="payment-msg" class="hidden glass rounded-xl p-5 text-sm text-gray-300">
</div>

<div class="flex justify-between mt-4">
<button onclick="prevStep(2)" class="px-6 py-2.5 rounded-lg border border-gray-700 text-gray-400 hover:text-white text-sm transition">&larr; Back</button>
<button onclick="submitPayment()" id="btn-pay" class="glow-btn px-8 py-2.5 rounded-lg text-white text-sm font-medium opacity-50 pointer-events-none">Confirm &amp; Continue &rarr;</button>
</div>
</div>
</div>

<!-- Step 4: Download -->
<div id="step-4" class="step-panel hidden">
<h2 class="text-xl font-bold text-white mb-6 text-center">Step 4: Download &amp; Install</h2>
<div class="grid md:grid-cols-2 gap-6 max-w-xl mx-auto">
<div class="glass rounded-xl p-6 text-center">
<div class="text-4xl mb-3">&#128039;</div>
<h3 class="text-white font-semibold mb-1">Linux (DEB)</h3>
<p class="text-gray-500 text-xs mb-4">Ubuntu 22.04+ / Debian 11+</p>
<a href="/static/connexa___VERSION___amd64.deb" class="glow-btn py-2.5 px-6 rounded-lg text-white text-sm font-medium no-underline">Download .deb</a>
<div class="mt-4 text-left bg-gray-900/50 rounded-lg p-3 text-xs text-gray-400 space-y-1">
<p class="text-gray-500 font-medium">Installation:</p>
<code class="block text-cyan-400">sudo dpkg -i connexa___VERSION___amd64.deb</code>
<code class="block text-cyan-400">sudo apt-get install -f</code>
<code class="block text-cyan-400">connexa</code>
</div>
</div>
<div class="glass rounded-xl p-6 text-center">
<div class="text-4xl mb-3">&#128187;</div>
<h3 class="text-white font-semibold mb-1">Windows</h3>
<p class="text-gray-500 text-xs mb-4">Windows 10/11 (64-bit)</p>
<a href="/static/Connexa-Setup-__VERSION__.exe" class="glow-btn py-2.5 px-6 rounded-lg text-white text-sm font-medium no-underline">Download .exe</a>
<div class="mt-4 text-left bg-gray-900/50 rounded-lg p-3 text-xs text-gray-400 space-y-1">
<p class="text-gray-500 font-medium">Installation:</p>
<p>1. Run Connexa-Setup-__VERSION__.exe</p>
<p>2. Follow the setup wizard</p>
<p>3. Launch Connexa from desktop</p>
</div>
</div>
</div>
<div class="mt-8 flex justify-between">
<button onclick="prevStep(3)" class="px-6 py-2.5 rounded-lg border border-gray-700 text-gray-400 hover:text-white text-sm transition">&larr; Back</button>
<button onclick="nextStep(5)" class="glow-btn px-8 py-2.5 rounded-lg text-white text-sm font-medium">I've Installed It &rarr;</button>
</div>
</div>

<!-- Step 5: Activate -->
<div id="step-5" class="step-panel hidden">
<h2 class="text-xl font-bold text-white mb-6 text-center">Step 5: Activate Your License</h2>
<div class="max-w-lg mx-auto">
<div class="glass rounded-2xl p-8">
<div id="activate-trial" class="hidden">
<div class="text-center mb-6">
<div class="text-5xl mb-3">&#127942;</div>
<h3 class="text-white font-semibold text-lg">You're All Set!</h3>
<p class="text-gray-400 text-sm mt-2">Your 7-day trial license key has been generated and emailed to you.</p>
</div>
<div id="trial-key-display" class="bg-gray-900/60 border border-cyan-500/30 rounded-xl p-5 mb-4 text-center hidden">
<p class="text-gray-500 text-xs mb-1">Your Trial License Key</p>
<p id="trial-key-value" class="text-cyan-400 font-mono text-lg font-bold tracking-wider"></p>
</div>
<div class="bg-blue-500/10 border border-blue-500/20 rounded-xl p-4 text-sm text-blue-300">
<p class="font-medium mb-1">What's Next:</p>
<ol class="list-decimal ml-4 space-y-1 text-blue-400/80">
<li>Check your email for the trial license key</li>
<li>Download and install Connexa</li>
<li>Enter your license key when prompted</li>
<li>Enjoy full access for 7 days!</li>
</ol>
</div>
<p class="text-gray-500 text-xs mt-3 text-center">Ready to upgrade? <a href="/get-started?plan=professional" class="text-blue-400 no-underline">Get a full license</a> starting at R600/month.</p>
</div>
<div id="activate-paid" class="hidden">
<div class="text-center mb-6">
<div class="text-5xl mb-3">&#128273;</div>
<h3 class="text-white font-semibold text-lg">Activate Your License</h3>
<p class="text-gray-400 text-sm mt-2">Your license key will be emailed to you after payment confirmation. Enter it in Connexa to activate:</p>
</div>
<div class="space-y-4 text-sm">
<div class="bg-gray-900/50 rounded-xl p-4">
<p class="text-gray-400 mb-3">&#x2460; Launch Connexa and go to <span class="text-cyan-400">Settings &rarr; License</span></p>
<p class="text-gray-400 mb-3">&#x2461; Enter your license key in the format: <span class="text-cyan-400 font-mono">XXXXX-XXXXX-XXXXX-XXXXX-XXXXX</span></p>
<p class="text-gray-400 mb-3">&#x2462; Click <span class="text-cyan-400">Activate</span> &mdash; your license binds to this machine</p>
<p class="text-gray-400">&#x2463; That's it! Full access is now unlocked.</p>
</div>
</div>
<p class="text-gray-500 text-xs mt-4 text-center">Didn't get your key? Check spam or contact <a href="mailto:__EMAIL__" class="text-blue-400 no-underline">__EMAIL__</a></p>
</div>
<div id="activate-enterprise" class="hidden text-center">
<div class="text-5xl mb-3">&#129309;</div>
<h3 class="text-white font-semibold text-lg">We'll Be in Touch</h3>
<p class="text-gray-400 text-sm mt-2 mb-6">Our team will contact you within 24 hours to set up your enterprise deployment. We'll handle installation, configuration, and license provisioning for you.</p>
<a href="mailto:__EMAIL__" class="glow-btn px-6 py-2.5 rounded-lg text-white text-sm font-medium no-underline">Contact: __EMAIL__</a>
</div>
</div>
<div class="mt-8 flex items-center justify-between">
<button onclick="prevStep(4)" class="px-6 py-2.5 rounded-lg border border-gray-700 text-gray-400 hover:text-white text-sm transition">&larr; Back</button>
<a href="/" class="glow-btn px-8 py-2.5 rounded-lg text-white text-sm font-medium no-underline">Back to Homepage &rarr;</a>
</div>
</div>
</div>
</div>

""" + _FOOTER + """
""" + _SHARED_JS + """
<script>
let currentStep=1, selectedPlan='', selectedPayment='';
let licenseQty=1, billingCycle='monthly';
const PRICE_MONTHLY=600, PRICE_ANNUAL=6800;

// Check URL params for pre-selected plan
const params=new URLSearchParams(window.location.search);
if(params.get('plan')){selectPlan(params.get('plan'))}

function changeQty(delta){
  licenseQty=Math.max(1,Math.min(100,licenseQty+delta));
  document.getElementById('qty-display').textContent=licenseQty;
  updatePrice();
}
function setBilling(cycle){
  billingCycle=cycle;
  document.querySelectorAll('.billing-opt').forEach(b=>{b.style.borderColor='#374151';b.style.background='transparent'});
  const btn=document.getElementById('btn-'+cycle);
  btn.style.borderColor='#3b82f6';btn.style.background='rgba(59,130,246,0.1)';
  updatePrice();
}
function updatePrice(){
  const unitPrice=billingCycle==='annual'?PRICE_ANNUAL:PRICE_MONTHLY;
  const total=unitPrice*licenseQty;
  const period=billingCycle==='annual'?'year':'month';
  const label=billingCycle==='annual'?'R6,800':'R600';
  document.getElementById('price-breakdown').textContent=label+' x '+licenseQty+' license(s) x 1 '+period;
  document.getElementById('price-total').textContent='R'+total.toLocaleString();
  // Update PayFast message if visible
  const msg=document.getElementById('payment-msg');
  if(selectedPayment==='payfast' && !msg.classList.contains('hidden')){
    msg.innerHTML='<div class="text-emerald-400 font-medium mb-1">&#9889; PayFast Secure Checkout</div><p class="text-gray-400 text-xs">You\\'ll be redirected to PayFast to pay <strong class="text-white">R'+total.toLocaleString()+'</strong> for '+licenseQty+' license(s) ('+period+'ly). Your license key(s) will be generated and emailed automatically.</p>';
  }
}

function selectPlan(plan){
  selectedPlan=plan;
  document.querySelectorAll('.plan-card').forEach(c=>{c.style.borderColor=c.dataset.plan===plan?'#3b82f6':'rgba(71,85,105,0.3)'});
  const btn=document.getElementById('btn-next-1');btn.style.opacity='1';btn.style.pointerEvents='auto';
}

function selectPayment(method){
  selectedPayment=method;
  document.querySelectorAll('.pay-opt').forEach(c=>{
    const radio=c.querySelector('.pay-radio');
    if(c.dataset.method===method){c.style.borderColor='#3b82f6';radio.style.borderColor='#3b82f6';radio.style.background='#3b82f6'}
    else{c.style.borderColor='rgba(71,85,105,0.3)';radio.style.borderColor='#475569';radio.style.background='transparent'}
  });
  const msg=document.getElementById('payment-msg');
  msg.classList.remove('hidden');
  if(method==='payfast'){
    const unitPrice=billingCycle==='annual'?PRICE_ANNUAL:PRICE_MONTHLY;
    const total=unitPrice*licenseQty;
    const period=billingCycle==='annual'?'year':'month';
    msg.innerHTML='<div class="text-emerald-400 font-medium mb-1">&#9889; PayFast Secure Checkout</div><p class="text-gray-400 text-xs">You\\'ll be redirected to PayFast to pay <strong class="text-white">R'+total.toLocaleString()+'</strong> for '+licenseQty+' license(s) ('+period+'ly). Your license key(s) will be generated and emailed automatically.</p>';
  }else if(method==='eft'){
    msg.innerHTML='<div class="text-blue-400 font-medium mb-1">&#127974; EFT / Bank Transfer</div><p class="text-gray-400 text-xs mb-2">Banking Details:</p><div class="bg-gray-900/50 rounded-lg p-3 text-xs"><p><strong class="text-white">Bank:</strong> FNB</p><p><strong class="text-white">Account:</strong> __COMPANY__ (Pty) Ltd</p><p><strong class="text-white">Reference:</strong> Your email address</p></div><p class="text-gray-500 text-[11px] mt-2">License key will be emailed within 24 hours of payment confirmation.</p>';
  }else{
    msg.innerHTML='<div class="text-purple-400 font-medium mb-1">&#128231; Invoice Request</div><p class="text-gray-400 text-xs">We\\'ll email a formal tax invoice within 24 hours. Payment terms: 7 days. License key issued upon payment.</p>';
  }
  const btn=document.getElementById('btn-pay');btn.style.opacity='1';btn.style.pointerEvents='auto';
}

function nextStep(n){
  if(n===3){
    document.getElementById('pay-trial').classList.add('hidden');
    document.getElementById('pay-professional').classList.add('hidden');
    document.getElementById('pay-enterprise').classList.add('hidden');
    if(selectedPlan==='trial'){document.getElementById('pay-trial').classList.remove('hidden')}
    else if(selectedPlan==='enterprise'){document.getElementById('pay-enterprise').classList.remove('hidden')}
    else{document.getElementById('pay-professional').classList.remove('hidden')}
  }
  if(n===5){
    document.getElementById('activate-trial').classList.add('hidden');
    document.getElementById('activate-paid').classList.add('hidden');
    document.getElementById('activate-enterprise').classList.add('hidden');
    if(selectedPlan==='trial'){document.getElementById('activate-trial').classList.remove('hidden')}
    else if(selectedPlan==='enterprise'){document.getElementById('activate-enterprise').classList.remove('hidden')}
    else{document.getElementById('activate-paid').classList.remove('hidden')}
  }
  goToStep(n);
}
function prevStep(n){goToStep(n)}
function goToStep(n){
  document.querySelectorAll('.step-panel').forEach(p=>p.classList.add('hidden'));
  document.getElementById('step-'+n).classList.remove('hidden');
  for(let i=1;i<=5;i++){
    const d=document.getElementById('sd-'+i);
    d.className='step-dot '+(i<n?'done':i===n?'active':'pending');
  }
  currentStep=n;
  window.scrollTo({top:0,behavior:'smooth'});
}

async function submitPayment(){
  const name=document.getElementById('gs-name')?.value||'';
  const email=document.getElementById('gs-email')?.value||'';
  const company=document.getElementById('gs-company')?.value||'';
  if(!email){alert('Please go back and fill in your details');return}

  if(selectedPayment==='payfast' && selectedPlan==='professional'){
    // POST form to PayFast
    try{
      const res=await fetch('/api/payfast/checkout',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({
        name,email,company,plan:selectedPlan,quantity:licenseQty,billing_cycle:billingCycle
      })});
      const data=await res.json();
      if(data.form_fields && data.payfast_url){
        const form=document.createElement('form');
        form.method='POST';
        form.action=data.payfast_url;
        for(const [key,val] of Object.entries(data.form_fields)){
          const input=document.createElement('input');
          input.type='hidden';
          input.name=key;
          input.value=val;
          form.appendChild(input);
        }
        document.body.appendChild(form);
        form.submit();
        return;
      }else{
        alert(data.detail||'Payment error. Please try again.');
        return;
      }
    }catch(e){alert('Payment error. Please try again.');return}
  }

  // Trial plan - already handled by activateTrial()
  if(selectedPlan==='trial'){nextStep(4);return}

  // EFT / Invoice - send contact form
  const unitPrice=billingCycle==='annual'?PRICE_ANNUAL:PRICE_MONTHLY;
  const total=unitPrice*licenseQty;
  const period=billingCycle==='annual'?'annual':'monthly';
  try{
    await fetch('/api/contact',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({
      name,email,company,subject:'License Order - '+selectedPlan+' ('+selectedPayment+')',
      message:'Plan: '+selectedPlan+'\\nPayment: '+selectedPayment+'\\nLicenses: '+licenseQty+'\\nBilling: '+period+'\\nTotal: R'+total+'\\nDevices: '+(document.getElementById('gs-devices')?.value||'N/A')
    })});
  }catch(e){}
  nextStep(4);
}
async function activateTrial(){
  const name=document.getElementById('gs-name')?.value||'';
  const email=document.getElementById('gs-email')?.value||'';
  const company=document.getElementById('gs-company')?.value||'';
  if(!email){alert('Please go back to Step 2 and enter your email address.');return}

  const btn=document.getElementById('btn-activate-trial');
  const status=document.getElementById('trial-status');
  btn.disabled=true;
  btn.textContent='Generating...';
  btn.style.opacity='0.5';

  try{
    const res=await fetch('/api/trial/activate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name,email,company})});
    const data=await res.json();
    if(data.success){
      status.className='mb-4 p-3 rounded-lg text-sm bg-green-500/10 border border-green-500/30 text-green-400';
      status.innerHTML='&#10003; '+data.message+' Check your inbox (and spam folder).';
      status.classList.remove('hidden');
      btn.textContent='Trial Activated!';
      btn.style.background='#22c55e';
      // Auto-advance after short delay
      setTimeout(()=>nextStep(4),2000);
    }else{
      status.className='mb-4 p-3 rounded-lg text-sm bg-red-500/10 border border-red-500/30 text-red-400';
      status.textContent=data.detail||'Something went wrong. Please try again.';
      status.classList.remove('hidden');
      btn.disabled=false;btn.textContent='Activate Free Trial \u2192';btn.style.opacity='1';
    }
  }catch(e){
    status.className='mb-4 p-3 rounded-lg text-sm bg-red-500/10 border border-red-500/30 text-red-400';
    status.textContent='Connection error. Please try again.';
    status.classList.remove('hidden');
    btn.disabled=false;btn.textContent='Activate Free Trial \u2192';btn.style.opacity='1';
  }
}
</script>
</body>
</html>"""


# (Documentation template removed — About section is now on homepage)

_REMOVED_DOCS = """<!DOCTYPE html>
<html lang="en">
<head>
""" + _HEAD + """
<title>Documentation - Connexa __VERSION__</title>
<style>
.doc-section{display:none}.doc-section.active{display:block}
.doc-sidebar{position:sticky;top:5rem;max-height:calc(100vh - 6rem);overflow-y:auto}
.doc-sidebar::-webkit-scrollbar{width:4px}.doc-sidebar::-webkit-scrollbar-thumb{background:#334155;border-radius:4px}
.doc-content h2{font-size:1.5rem;font-weight:700;color:#fff;margin-bottom:1rem;padding-bottom:.5rem;border-bottom:1px solid rgba(71,85,105,0.3)}
.doc-content h3{font-size:1.125rem;font-weight:600;color:#e2e8f0;margin-top:1.5rem;margin-bottom:.75rem}
.doc-content p{color:#94a3b8;font-size:.9rem;line-height:1.75;margin-bottom:1rem}
.doc-content ul,.doc-content ol{color:#94a3b8;font-size:.9rem;line-height:1.75;margin-bottom:1rem;padding-left:1.5rem}
.doc-content li{margin-bottom:.25rem}
.doc-content code{background:#1e293b;color:#22d3ee;padding:.125rem .375rem;border-radius:.25rem;font-size:.8rem}
.doc-content pre{background:#0f172a;border:1px solid #1e293b;border-radius:.5rem;padding:1rem;overflow-x:auto;margin-bottom:1rem}
.doc-content pre code{background:transparent;padding:0;font-size:.8rem;color:#e2e8f0}
.doc-content .tip{background:rgba(59,130,246,0.1);border:1px solid rgba(59,130,246,0.2);border-radius:.5rem;padding:1rem;margin-bottom:1rem}
.doc-content .tip p{color:#93c5fd;margin:0}
.doc-content .warn{background:rgba(234,179,8,0.1);border:1px solid rgba(234,179,8,0.2);border-radius:.5rem;padding:1rem;margin-bottom:1rem}
.doc-content .warn p{color:#fde68a;margin:0}
</style>
</head>
<body>
""" + _NAV + """

<div class="max-w-7xl mx-auto px-4 sm:px-6 pt-24 pb-20">
<div class="flex gap-8">
<!-- Sidebar -->
<aside class="hidden lg:block w-64 flex-shrink-0">
<div class="doc-sidebar">
<h3 class="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3 px-1">Documentation</h3>
<nav class="space-y-0.5" id="doc-nav">
<a href="#overview" class="doc-link active" onclick="showDoc('overview',this)">Overview</a>
<a href="#requirements" class="doc-link" onclick="showDoc('requirements',this)">System Requirements</a>
<a href="#installation" class="doc-link" onclick="showDoc('installation',this)">Installation</a>
<a href="#first-setup" class="doc-link" onclick="showDoc('first-setup',this)">First-Time Setup</a>
<a href="#dashboard" class="doc-link" onclick="showDoc('dashboard',this)">Dashboard</a>
<a href="#devices" class="doc-link" onclick="showDoc('devices',this)">Device Management</a>
<a href="#towers" class="doc-link" onclick="showDoc('towers',this)">Tower Monitoring</a>
<a href="#wireless" class="doc-link" onclick="showDoc('wireless',this)">Wireless Clients</a>
<a href="#scripts" class="doc-link" onclick="showDoc('scripts',this)">Scripts &amp; Push Jobs</a>
<a href="#scheduler" class="doc-link" onclick="showDoc('scheduler',this)">Task Scheduler</a>
<a href="#zabbix" class="doc-link" onclick="showDoc('zabbix',this)">Zabbix Integration</a>
<a href="#multitenancy" class="doc-link" onclick="showDoc('multitenancy',this)">Multi-Tenancy</a>
<a href="#licensing" class="doc-link" onclick="showDoc('licensing',this)">License Management</a>
<a href="#troubleshooting" class="doc-link" onclick="showDoc('troubleshooting',this)">Troubleshooting</a>
<a href="#api" class="doc-link" onclick="showDoc('api',this)">API Reference</a>
</nav>
</div>
</aside>

<!-- Mobile doc nav -->
<div class="lg:hidden mb-6 w-full">
<select id="doc-mobile-nav" onchange="showDoc(this.value)" class="w-full bg-gray-900 border border-gray-700 text-white px-4 py-2.5 rounded-lg text-sm">
<option value="overview">Overview</option>
<option value="requirements">System Requirements</option>
<option value="installation">Installation</option>
<option value="first-setup">First-Time Setup</option>
<option value="dashboard">Dashboard</option>
<option value="devices">Device Management</option>
<option value="towers">Tower Monitoring</option>
<option value="wireless">Wireless Clients</option>
<option value="scripts">Scripts &amp; Push Jobs</option>
<option value="scheduler">Task Scheduler</option>
<option value="zabbix">Zabbix Integration</option>
<option value="multitenancy">Multi-Tenancy</option>
<option value="licensing">License Management</option>
<option value="troubleshooting">Troubleshooting</option>
<option value="api">API Reference</option>
</select>
</div>

<!-- Content -->
<main class="flex-1 min-w-0 doc-content">

<div id="doc-overview" class="doc-section active">
<h2>Overview</h2>
<p>Connexa is a professional network management platform built for Internet Service Providers (ISPs), Wireless ISPs (WISPs), and Managed Service Providers (MSPs). It provides a unified dashboard to monitor, manage, and automate your entire network infrastructure.</p>
<h3>Key Capabilities</h3>
<ul>
<li><strong>Device Management</strong> &mdash; Add and manage MikroTik, Ubiquiti, Cambium, and Mimosa devices via RouterOS API or SNMP</li>
<li><strong>Tower Monitoring</strong> &mdash; Real-time monitoring of tower equipment with signal levels, client counts, and uptime</li>
<li><strong>Wireless Client Tracking</strong> &mdash; Track every connected client with signal strength, SNR, CCQ, and data rates</li>
<li><strong>Script Automation</strong> &mdash; Push RouterOS scripts to devices individually or in bulk</li>
<li><strong>Task Scheduling</strong> &mdash; Schedule recurring maintenance tasks with cron-like precision</li>
<li><strong>Zabbix Integration</strong> &mdash; Connect to Zabbix for advanced monitoring and alerting</li>
<li><strong>Multi-Tenancy</strong> &mdash; Isolate data between companies for MSP deployments</li>
<li><strong>Email Alerts</strong> &mdash; Configurable notifications for outages and threshold breaches</li>
</ul>
<h3>Architecture</h3>
<p>Connexa runs as a self-hosted application on your own server. The backend is a Python FastAPI server communicating with your network devices. The frontend is a modern React web application accessible via browser or the desktop Electron app.</p>
<div class="tip"><p><strong>Tip:</strong> Your data never leaves your network. Connexa runs entirely on-premises &mdash; only the license validation makes a brief outbound call to verify your key.</p></div>
</div>

<div id="doc-requirements" class="doc-section">
<h2>System Requirements</h2>
<h3>Server (Backend)</h3>
<ul>
<li><strong>OS:</strong> Ubuntu 22.04 LTS or newer (recommended), Debian 11+</li>
<li><strong>CPU:</strong> 2+ cores (4 recommended for 100+ devices)</li>
<li><strong>RAM:</strong> 2 GB minimum, 4 GB recommended</li>
<li><strong>Disk:</strong> 10 GB for application + database</li>
<li><strong>Network:</strong> Access to managed devices (RouterOS API port 8728, SNMP 161)</li>
<li><strong>Python:</strong> 3.10+ (included in .deb package)</li>
</ul>
<h3>Desktop Client (Electron)</h3>
<ul>
<li><strong>Linux:</strong> Ubuntu 22.04+, Debian 11+ (amd64)</li>
<li><strong>Windows:</strong> Windows 10 or 11 (64-bit)</li>
<li><strong>RAM:</strong> 512 MB</li>
<li><strong>Disk:</strong> 200 MB</li>
</ul>
<h3>Supported Devices</h3>
<ul>
<li><strong>MikroTik</strong> &mdash; All RouterOS devices (via API, port 8728/8729)</li>
<li><strong>Ubiquiti</strong> &mdash; UniFi &amp; airMAX (via SNMP)</li>
<li><strong>Cambium</strong> &mdash; ePMP &amp; PMP series (via SNMP)</li>
<li><strong>Mimosa</strong> &mdash; A5/B5/C5 series (via SNMP)</li>
<li><strong>Generic</strong> &mdash; Any SNMP-capable device</li>
</ul>
</div>

<div id="doc-installation" class="doc-section">
<h2>Installation</h2>
<h3>Linux (Debian/Ubuntu)</h3>
<pre><code># Download the .deb package
wget https://connexify-server.onrender.com/static/connexa___VERSION___amd64.deb

# Install
sudo dpkg -i connexa___VERSION___amd64.deb

# Fix any missing dependencies
sudo apt-get install -f

# Start the service
sudo systemctl start connexa-backend
sudo systemctl enable connexa-backend

# Verify it's running
curl http://localhost:8001/api/health</code></pre>
<h3>Windows</h3>
<ol>
<li>Download <code>Connexa-Setup-__VERSION__.exe</code> from the <a href="/#downloads" class="text-blue-400">downloads page</a></li>
<li>Run the installer and follow the setup wizard</li>
<li>Launch Connexa from the desktop shortcut or Start menu</li>
<li>Enter your server address (if connecting to a remote backend)</li>
</ol>
<h3>Docker</h3>
<pre><code># Pull and run with Docker Compose
docker compose -f docker/compose.yaml up -d

# Access at http://localhost:8001</code></pre>
<div class="tip"><p><strong>Tip:</strong> The Linux .deb package includes both the backend server and a systemd service file. It runs on port 8001 by default.</p></div>
</div>

<div id="doc-first-setup" class="doc-section">
<h2>First-Time Setup</h2>
<h3>1. Access the Dashboard</h3>
<p>Open your browser and navigate to <code>http://your-server-ip:8001</code>. You'll see the Connexa login page.</p>
<h3>2. Default Credentials</h3>
<pre><code>Username: admin
Password: admin</code></pre>
<div class="warn"><p><strong>Important:</strong> Change your admin password immediately after first login via Settings &rarr; Users.</p></div>
<h3>3. Add Your First Device</h3>
<ol>
<li>Go to <strong>Settings &rarr; Devices</strong></li>
<li>Click <strong>Add Device</strong></li>
<li>Enter the device IP address, credentials, and connection type (RouterOS API or SNMP)</li>
<li>Click <strong>Test Connection</strong> to verify</li>
<li>Save the device</li>
</ol>
<h3>4. Configure Device Groups</h3>
<p>Organize devices into groups by tower, location, or function. This helps with bulk operations and dashboard organization.</p>
<h3>5. Set Up Email Alerts</h3>
<p>Go to <strong>Settings &rarr; Email</strong> and configure your SMTP settings to receive outage notifications and task completion alerts.</p>
</div>

<div id="doc-dashboard" class="doc-section">
<h2>Dashboard</h2>
<p>The main dashboard provides an at-a-glance view of your entire network:</p>
<ul>
<li><strong>Device Status Summary</strong> &mdash; Total devices, online/offline counts, and uptime percentage</li>
<li><strong>Tower Overview</strong> &mdash; All towers with client counts and health indicators</li>
<li><strong>Recent Alerts</strong> &mdash; Latest outages, threshold breaches, and events</li>
<li><strong>Quick Actions</strong> &mdash; Common tasks like adding devices, running scripts, and viewing logs</li>
</ul>
<h3>Customization</h3>
<p>The dashboard updates in real-time as device data is polled. Polling intervals are configurable per device or globally.</p>
</div>

<div id="doc-devices" class="doc-section">
<h2>Device Management</h2>
<p>Connexa supports multiple connection methods to manage your network devices.</p>
<h3>RouterOS API (MikroTik)</h3>
<p>For MikroTik devices, Connexa connects via the RouterOS API (port 8728 for plain, 8729 for SSL). This provides the richest feature set including:</p>
<ul>
<li>Full interface statistics and traffic monitoring</li>
<li>Wireless registration table access</li>
<li>Script execution and configuration changes</li>
<li>Firmware version tracking</li>
<li>System resource monitoring (CPU, RAM, disk)</li>
</ul>
<h3>SNMP</h3>
<p>For non-MikroTik devices (Ubiquiti, Cambium, Mimosa), Connexa uses SNMP v2c or v3. Configure the community string or v3 credentials on each device.</p>
<h3>Bulk Operations</h3>
<p>Select multiple devices to perform bulk operations: push scripts, update firmware, reboot, or change configurations across your entire fleet.</p>
</div>

<div id="doc-towers" class="doc-section">
<h2>Tower Monitoring</h2>
<p>Tower monitoring gives you a bird's-eye view of your wireless infrastructure.</p>
<h3>Tower View</h3>
<ul>
<li>See all access points and sectors per tower</li>
<li>Real-time client counts per sector</li>
<li>Signal level distribution across clients</li>
<li>Bandwidth utilization per tower</li>
</ul>
<h3>Client Classification</h3>
<p>Connexa automatically classifies devices as <strong>Towers</strong> (APs, base stations, sectors) or <strong>Clients</strong> (CPEs, subscribers, stations) based on device type keywords. This powers the tower monitoring view and the quick-select buttons in Task Scheduler.</p>
</div>

<div id="doc-wireless" class="doc-section">
<h2>Wireless Clients</h2>
<p>Track every wireless client connected to your network.</p>
<h3>Client Metrics</h3>
<ul>
<li><strong>Signal Strength</strong> &mdash; RX/TX signal in dBm with color coding</li>
<li><strong>SNR</strong> &mdash; Signal-to-noise ratio</li>
<li><strong>CCQ</strong> &mdash; Client connection quality percentage</li>
<li><strong>Data Rates</strong> &mdash; TX/RX rates in Mbps</li>
<li><strong>Uptime</strong> &mdash; How long the client has been connected</li>
<li><strong>MAC Address</strong> &mdash; Client hardware address</li>
</ul>
<h3>Signal Thresholds</h3>
<p>Configure signal thresholds to flag clients with poor connections. Default color coding:</p>
<ul>
<li><strong style="color:#22c55e">Green</strong> &mdash; Better than -65 dBm (excellent)</li>
<li><strong style="color:#eab308">Yellow</strong> &mdash; -65 to -75 dBm (good)</li>
<li><strong style="color:#f97316">Orange</strong> &mdash; -75 to -80 dBm (fair)</li>
<li><strong style="color:#ef4444">Red</strong> &mdash; Worse than -80 dBm (poor)</li>
</ul>
</div>

<div id="doc-scripts" class="doc-section">
<h2>Scripts &amp; Push Jobs</h2>
<p>Automate your network management with RouterOS script execution.</p>
<h3>Script Library</h3>
<p>Create and save reusable scripts in the Script Library. Scripts are categorized and can be shared across your team.</p>
<h3>Push Jobs</h3>
<p>Push scripts to one or multiple devices simultaneously:</p>
<ol>
<li>Select devices from the device list (use "All Towers" or "All Clients" for quick selection)</li>
<li>Choose a script from the library or write a custom one</li>
<li>Click Push &mdash; Connexa executes the script on every selected device</li>
<li>View execution results per device in the job results panel</li>
</ol>
<div class="tip"><p><strong>Tip:</strong> Use the "All Towers" button to quickly select all access points and base stations, or "All Clients" to select all CPE/subscriber devices.</p></div>
</div>

<div id="doc-scheduler" class="doc-section">
<h2>Task Scheduler</h2>
<p>Schedule recurring tasks for hands-free network management.</p>
<h3>Creating a Scheduled Task</h3>
<ol>
<li>Navigate to <strong>Task Scheduler</strong></li>
<li>Click <strong>New Task</strong></li>
<li>Select target devices</li>
<li>Choose or write a script</li>
<li>Set the schedule (one-time, daily, weekly, monthly, or cron expression)</li>
<li>Save the task</li>
</ol>
<h3>Common Use Cases</h3>
<ul>
<li>Daily configuration backups</li>
<li>Weekly firmware checks</li>
<li>Monthly bandwidth report generation</li>
<li>Automatic reboots during maintenance windows</li>
</ul>
</div>

<div id="doc-zabbix" class="doc-section">
<h2>Zabbix Integration</h2>
<p>Connect Connexa with Zabbix for enterprise-grade monitoring and alerting.</p>
<h3>Setup</h3>
<ol>
<li>Go to <strong>Settings &rarr; Integrations &rarr; Zabbix</strong></li>
<li>Enter your Zabbix server URL and API token</li>
<li>Click <strong>Test Connection</strong></li>
<li>Map Connexa device groups to Zabbix host groups</li>
</ol>
<h3>Features</h3>
<ul>
<li>Automatic host synchronization from Zabbix</li>
<li>Zabbix problem/trigger display in Connexa dashboard</li>
<li>Historical data graphs from Zabbix in device detail views</li>
<li>Unified alerting combining Connexa and Zabbix events</li>
</ul>
</div>

<div id="doc-multitenancy" class="doc-section">
<h2>Multi-Tenancy</h2>
<p>Run a single Connexa instance for multiple client companies with complete data isolation.</p>
<h3>Setup</h3>
<ol>
<li>Go to <strong>Settings &rarr; Companies</strong></li>
<li>Click <strong>Add Company</strong></li>
<li>Enter company name, contact details, and assign users</li>
<li>Each company sees only their own devices, towers, and data</li>
</ol>
<h3>User Roles</h3>
<ul>
<li><strong>Super Admin</strong> &mdash; Sees all companies, manages system settings</li>
<li><strong>Company Admin</strong> &mdash; Manages devices and users within their company</li>
<li><strong>Operator</strong> &mdash; View-only access to dashboards and reports</li>
</ul>
</div>

<div id="doc-licensing" class="doc-section">
<h2>License Management</h2>
<h3>License Types</h3>
<ul>
<li><strong>Trial</strong> &mdash; 7 days, up to 10 devices, all features</li>
<li><strong>Professional</strong> &mdash; Unlimited devices, all features, priority support (R500/month)</li>
<li><strong>Enterprise</strong> &mdash; Custom pricing, multi-tenant, dedicated support</li>
</ul>
<h3>Activation</h3>
<p>Your license key is in the format <code>XXXXX-XXXXX-XXXXX-XXXXX-XXXXX</code>. Enter it in <strong>Settings &rarr; License</strong> and click Activate. The license binds to your machine's hardware fingerprint.</p>
<h3>Hardware Binding</h3>
<p>Licenses are bound to the hardware they're first activated on. If you need to move to a new server, contact <a href="mailto:__EMAIL__" class="text-blue-400">__EMAIL__</a> to unbind your license.</p>
<h3>Offline Grace Period</h3>
<p>If the license server is unreachable, Connexa continues operating for up to 30 days using cached license data. This ensures your monitoring doesn't go down due to internet issues.</p>
</div>

<div id="doc-troubleshooting" class="doc-section">
<h2>Troubleshooting</h2>
<h3>Service Won't Start</h3>
<pre><code># Check service status
sudo systemctl status connexa-backend

# View logs
sudo journalctl -u connexa-backend -n 50 --no-pager

# Common fix: ensure port 8001 is free
sudo lsof -i :8001</code></pre>
<h3>Can't Connect to Devices</h3>
<ul>
<li>Verify the device IP is reachable: <code>ping &lt;device-ip&gt;</code></li>
<li>Check RouterOS API is enabled: <code>/ip service print</code> on the device</li>
<li>Ensure API port (8728) is not blocked by firewall</li>
<li>Verify credentials are correct</li>
</ul>
<h3>License Validation Fails</h3>
<ul>
<li>Ensure the server has internet access to reach <code>license.connexify.co.za</code></li>
<li>Check that your license key is entered correctly (including dashes)</li>
<li>If the license expired, contact <a href="mailto:__EMAIL__" class="text-blue-400">__EMAIL__</a> to renew</li>
<li>The 30-day grace period covers temporary connectivity issues</li>
</ul>
<h3>High CPU Usage</h3>
<ul>
<li>Reduce polling frequency for large device counts</li>
<li>Check for runaway scripts in Task Scheduler</li>
<li>Verify the database isn't excessively large (check disk usage)</li>
</ul>
</div>

<div id="doc-api" class="doc-section">
<h2>API Reference</h2>
<p>Connexa exposes a REST API on port 8001 for integration with your existing tools.</p>
<h3>Authentication</h3>
<p>API requests require an authentication token. Obtain one via the login endpoint:</p>
<pre><code>POST /api/auth/login
Content-Type: application/json

{"username": "admin", "password": "your-password"}</code></pre>
<h3>Key Endpoints</h3>
<ul>
<li><code>GET /api/health</code> &mdash; Server health check</li>
<li><code>GET /api/devices</code> &mdash; List all devices</li>
<li><code>GET /api/devices/{id}</code> &mdash; Device details</li>
<li><code>POST /api/devices</code> &mdash; Add a device</li>
<li><code>GET /api/towers</code> &mdash; List towers with client counts</li>
<li><code>GET /api/wireless-clients</code> &mdash; All wireless clients</li>
<li><code>POST /api/scripts/push</code> &mdash; Push a script to devices</li>
<li><code>GET /api/tasks</code> &mdash; List scheduled tasks</li>
</ul>
<div class="tip"><p><strong>Tip:</strong> Visit <code>http://your-server:8001/docs</code> for the interactive Swagger API documentation.</p></div>
</div>

</main>
</div>
</div>

""" + _FOOTER + """
""" + _SHARED_JS + """
<script>
function showDoc(id, el){
  document.querySelectorAll('.doc-section').forEach(s=>s.classList.remove('active'));
  const target=document.getElementById('doc-'+id);
  if(target)target.classList.add('active');
  if(el){document.querySelectorAll('#doc-nav .doc-link').forEach(a=>a.classList.remove('active'));el.classList.add('active')}
  document.getElementById('doc-mobile-nav').value=id;
  window.scrollTo({top:0,behavior:'smooth'});
  return false;
}
// Handle URL hash
if(window.location.hash){
  const id=window.location.hash.substring(1);
  const link=document.querySelector('#doc-nav a[href="#'+id+'"]');
  if(link)showDoc(id,link);
}
</script>
</body>
</html>"""
