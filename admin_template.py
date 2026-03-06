"""Admin dashboard HTML template for Connexify License Server."""

ADMIN_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Connexa License Admin</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        body { font-family: 'Inter', system-ui, sans-serif; background: #0a0a0f; }
        .glass { background: rgba(15, 23, 42, 0.6); border: 1px solid rgba(71, 85, 105, 0.3); backdrop-filter: blur(12px); }
        input, select { background: rgba(15, 23, 42, 0.8); border: 1px solid rgba(71, 85, 105, 0.4); color: #e2e8f0; }
        input:focus, select:focus { border-color: #3b82f6; outline: none; }
        .status-active { background: #22c55e; }
        .status-inactive { background: #64748b; }
        .status-expired { background: #ef4444; }
        .modal-bg { background: rgba(0, 0, 0, 0.7); backdrop-filter: blur(4px); }
        .tab-btn { transition: all 0.2s; border-bottom: 2px solid transparent; }
        .tab-btn.active { border-bottom-color: #3b82f6; color: #fff; }
        .tab-btn:hover { color: #cbd5e1; }
    </style>
</head>
<body class="min-h-screen text-slate-300">
    <header class="glass border-t-0 border-x-0 sticky top-0 z-40">
        <div class="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
            <div class="flex items-center gap-3">
                <div class="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-cyan-400 flex items-center justify-center text-white text-xs font-bold">C</div>
                <span class="text-white font-semibold">Connexa Admin</span>
            </div>
            <div class="flex items-center gap-4">
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

            <!-- Tab Navigation -->
            <div class="flex gap-1 border-b border-slate-700/50 mb-6 overflow-x-auto">
                <button onclick="switchTab('licenses')" class="tab-btn active px-5 py-3 text-sm font-medium text-slate-400" data-tab="licenses">&#128272; Licenses</button>
                <button onclick="switchTab('social')" class="tab-btn px-5 py-3 text-sm font-medium text-slate-400" data-tab="social">&#128226; Social Media</button>
                <button onclick="switchTab('admin')" class="tab-btn px-5 py-3 text-sm font-medium text-slate-400" data-tab="admin">&#128737; Administrators</button>
            </div>

            <!-- TAB: Licenses -->
            <div id="tab-licenses" class="tab-content">
                <div class="flex flex-wrap items-center justify-between gap-4 mb-6">
                    <h2 class="text-xl font-bold text-white">Licenses</h2>
                    <div class="flex gap-3">
                        <button onclick="showCreateModal()" class="bg-blue-600 hover:bg-blue-500 text-white px-5 py-2.5 rounded-lg text-sm font-medium transition flex items-center gap-2">
                            <span class="text-lg">+</span> Create License
                        </button>
                        <button onclick="loadLicenses()" class="bg-slate-700 hover:bg-slate-600 text-white px-4 py-2.5 rounded-lg text-sm font-medium transition">&#8635; Refresh</button>
                    </div>
                </div>
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

            <!-- TAB: Administrators (combined Portal Users, Admin Users, SMTP) -->
            <div id="tab-admin" class="tab-content hidden">
                <!-- Admin Sub-tabs -->
                <div class="flex gap-2 mb-6">
                    <button onclick="switchAdminSub('users')" class="admin-sub-btn active px-4 py-2 text-xs font-medium text-white bg-blue-600/30 border border-blue-500/30 rounded-lg" data-sub="users">&#128101; Portal Users</button>
                    <button onclick="switchAdminSub('admins')" class="admin-sub-btn px-4 py-2 text-xs font-medium text-slate-400 bg-slate-800/30 border border-slate-700/30 rounded-lg" data-sub="admins">&#128737; Admin Users</button>
                    <button onclick="switchAdminSub('smtp')" class="admin-sub-btn px-4 py-2 text-xs font-medium text-slate-400 bg-slate-800/30 border border-slate-700/30 rounded-lg" data-sub="smtp">&#128231; SMTP Settings</button>
                </div>

                <!-- Sub: Portal Users -->
                <div id="admin-sub-users" class="admin-sub-content">
                    <div class="flex flex-wrap items-center justify-between gap-4 mb-6">
                        <h2 class="text-xl font-bold text-white">Portal Users</h2>
                        <button onclick="loadPortalUsers()" class="bg-slate-700 hover:bg-slate-600 text-white px-4 py-2.5 rounded-lg text-sm font-medium transition">&#8635; Refresh</button>
                    </div>
                    <div class="glass rounded-xl overflow-hidden">
                        <div class="overflow-x-auto">
                            <table class="w-full text-sm">
                                <thead>
                                    <tr class="border-b border-slate-700/50 text-left text-slate-400">
                                        <th class="px-5 py-3 font-medium">Name</th>
                                        <th class="px-5 py-3 font-medium">Email</th>
                                        <th class="px-5 py-3 font-medium">Company</th>
                                        <th class="px-5 py-3 font-medium">Licenses</th>
                                        <th class="px-5 py-3 font-medium">Status</th>
                                        <th class="px-5 py-3 font-medium">Registered</th>
                                        <th class="px-5 py-3 font-medium text-right">Actions</th>
                                    </tr>
                                </thead>
                                <tbody id="users-table-body">
                                    <tr><td colspan="7" class="px-5 py-10 text-center text-slate-500">Loading...</td></tr>
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>

                <!-- Sub: SMTP Settings -->
                <div id="admin-sub-smtp" class="admin-sub-content hidden">
                    <div class="flex flex-wrap items-center justify-between gap-4 mb-6">
                        <h2 class="text-xl font-bold text-white">SMTP / Email Settings</h2>
                    </div>
                    <div class="max-w-xl">
                        <div class="glass rounded-2xl p-8 space-y-5">
                            <div class="grid grid-cols-2 gap-4">
                                <div>
                                    <label class="text-xs text-slate-400 block mb-1.5">SMTP Host</label>
                                    <input id="smtp-host" type="text" class="w-full px-4 py-2.5 rounded-lg text-sm">
                                </div>
                                <div>
                                    <label class="text-xs text-slate-400 block mb-1.5">SMTP Port</label>
                                    <input id="smtp-port" type="number" class="w-full px-4 py-2.5 rounded-lg text-sm">
                                </div>
                            </div>
                            <div>
                                <label class="text-xs text-slate-400 block mb-1.5">SMTP Username</label>
                                <input id="smtp-user" type="text" class="w-full px-4 py-2.5 rounded-lg text-sm">
                            </div>
                            <div>
                                <label class="text-xs text-slate-400 block mb-1.5">SMTP Password</label>
                                <input id="smtp-pass" type="password" class="w-full px-4 py-2.5 rounded-lg text-sm">
                            </div>
                            <div class="grid grid-cols-2 gap-4">
                                <div>
                                    <label class="text-xs text-slate-400 block mb-1.5">From Email</label>
                                    <input id="smtp-from-email" type="email" class="w-full px-4 py-2.5 rounded-lg text-sm">
                                </div>
                                <div>
                                    <label class="text-xs text-slate-400 block mb-1.5">From Name</label>
                                    <input id="smtp-from-name" type="text" class="w-full px-4 py-2.5 rounded-lg text-sm">
                                </div>
                            </div>
                            <div class="flex gap-3 pt-2">
                                <button onclick="saveSmtp()" class="bg-blue-600 hover:bg-blue-500 text-white px-6 py-2.5 rounded-lg text-sm font-medium transition">Save Settings</button>
                                <button onclick="testSmtp()" class="bg-slate-700 hover:bg-slate-600 text-white px-6 py-2.5 rounded-lg text-sm font-medium transition">&#128231; Send Test Email</button>
                            </div>
                            <p id="smtp-result" class="text-sm hidden"></p>
                        </div>
                    </div>
                </div>

                <!-- Sub: Admin Users -->
                <div id="admin-sub-admins" class="admin-sub-content hidden">
                    <div class="flex flex-wrap items-center justify-between gap-4 mb-6">
                        <h2 class="text-xl font-bold text-white">Admin Users</h2>
                        <button onclick="showAddAdminModal()" class="bg-blue-600 hover:bg-blue-500 text-white px-5 py-2.5 rounded-lg text-sm font-medium transition flex items-center gap-2">
                            <span class="text-lg">+</span> Add Admin
                        </button>
                    </div>
                    <div class="glass rounded-xl overflow-hidden">
                        <div class="overflow-x-auto">
                            <table class="w-full text-sm">
                                <thead>
                                    <tr class="border-b border-slate-700/50 text-left text-slate-400">
                                        <th class="px-5 py-3 font-medium">Name</th>
                                        <th class="px-5 py-3 font-medium">Email</th>
                                        <th class="px-5 py-3 font-medium">Role</th>
                                        <th class="px-5 py-3 font-medium">Added</th>
                                        <th class="px-5 py-3 font-medium text-right">Actions</th>
                                    </tr>
                                </thead>
                                <tbody id="admins-table-body">
                                    <tr><td colspan="5" class="px-5 py-10 text-center text-slate-500">Loading...</td></tr>
                                </tbody>
                            </table>
                        </div>
                    </div>
                    <div class="glass rounded-xl p-5 mt-6">
                        <h3 class="text-white font-medium text-sm mb-2">Admin Token</h3>
                        <p class="text-xs text-slate-400 mb-3">All admin operations use the shared admin token. Change it via the <code class="text-cyan-400">ADMIN_SECRET_TOKEN</code> environment variable.</p>
                        <div class="flex items-center gap-3">
                            <input id="admin-token-display" type="password" readonly class="flex-1 px-4 py-2 rounded-lg text-sm font-mono bg-slate-900/80 border border-slate-700 text-slate-300">
                            <button onclick="toggleTokenVisibility()" class="px-3 py-2 rounded-lg bg-slate-700 hover:bg-slate-600 text-xs text-white transition">&#128065;</button>
                        </div>
                    </div>
                </div>
            </div>

            <!-- TAB: Social Media -->
            <div id="tab-social" class="tab-content hidden">
                <!-- Social Stats -->
                <div class="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
                    <div class="glass rounded-xl p-4">
                        <p class="text-xs text-slate-400 mb-1">Total Posts</p>
                        <p id="social-stat-total" class="text-2xl font-bold text-white">-</p>
                    </div>
                    <div class="glass rounded-xl p-4">
                        <p class="text-xs text-slate-400 mb-1">Drafts</p>
                        <p id="social-stat-draft" class="text-2xl font-bold text-yellow-400">-</p>
                    </div>
                    <div class="glass rounded-xl p-4">
                        <p class="text-xs text-slate-400 mb-1">Scheduled</p>
                        <p id="social-stat-scheduled" class="text-2xl font-bold text-blue-400">-</p>
                    </div>
                    <div class="glass rounded-xl p-4">
                        <p class="text-xs text-slate-400 mb-1">Published</p>
                        <p id="social-stat-published" class="text-2xl font-bold text-green-400">-</p>
                    </div>
                    <div class="glass rounded-xl p-4">
                        <p class="text-xs text-slate-400 mb-1">Accounts</p>
                        <p id="social-stat-accounts" class="text-2xl font-bold text-cyan-400">-</p>
                    </div>
                </div>

                <!-- Sub-tabs -->
                <div class="flex gap-2 mb-6">
                    <button onclick="switchSocialSub('posts')" class="social-sub-btn active px-4 py-2 text-xs font-medium text-white bg-blue-600/30 border border-blue-500/30 rounded-lg" data-sub="posts">Posts</button>
                    <button onclick="switchSocialSub('calendar')" class="social-sub-btn px-4 py-2 text-xs font-medium text-slate-400 bg-slate-800/30 border border-slate-700/30 rounded-lg" data-sub="calendar">Calendar</button>
                    <button onclick="switchSocialSub('accounts')" class="social-sub-btn px-4 py-2 text-xs font-medium text-slate-400 bg-slate-800/30 border border-slate-700/30 rounded-lg" data-sub="accounts">Accounts</button>
                    <button onclick="switchSocialSub('automation')" class="social-sub-btn px-4 py-2 text-xs font-medium text-slate-400 bg-slate-800/30 border border-slate-700/30 rounded-lg" data-sub="automation">&#9889; Automation</button>
                </div>

                <!-- Sub: Posts List -->
                <div id="social-sub-posts" class="social-sub-content">
                    <div class="flex flex-wrap items-center justify-between gap-4 mb-4">
                        <h2 class="text-xl font-bold text-white">Social Posts</h2>
                        <div class="flex gap-2">
                            <select id="social-filter-status" onchange="loadSocialPosts()" class="px-3 py-2 rounded-lg text-xs">
                                <option value="">All Statuses</option>
                                <option value="draft">Drafts</option>
                                <option value="scheduled">Scheduled</option>
                                <option value="published">Published</option>
                            </select>
                            <button onclick="showSocialPostModal()" class="bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded-lg text-xs font-medium transition">+ New Post</button>
                            <button onclick="showImportCSVModal()" class="bg-slate-700 hover:bg-slate-600 text-white px-4 py-2 rounded-lg text-xs font-medium transition">&#128196; Import CSV</button>
                            <button onclick="showBulkScheduleModal()" class="bg-purple-700 hover:bg-purple-600 text-white px-4 py-2 rounded-lg text-xs font-medium transition">&#128197; Bulk Schedule</button>
                        </div>
                    </div>
                    <div class="glass rounded-xl overflow-hidden">
                        <div class="overflow-x-auto">
                            <table class="w-full text-sm">
                                <thead>
                                    <tr class="border-b border-slate-700/50 text-left text-slate-400">
                                        <th class="px-4 py-3 font-medium w-8"><input type="checkbox" id="select-all-posts" onchange="toggleSelectAll()" class="w-4 h-4 rounded"></th>
                                        <th class="px-4 py-3 font-medium">Content</th>
                                        <th class="px-4 py-3 font-medium">Platforms</th>
                                        <th class="px-4 py-3 font-medium">Scheduled</th>
                                        <th class="px-4 py-3 font-medium">Status</th>
                                        <th class="px-4 py-3 font-medium">Campaign</th>
                                        <th class="px-4 py-3 font-medium text-right">Actions</th>
                                    </tr>
                                </thead>
                                <tbody id="social-posts-body">
                                    <tr><td colspan="7" class="px-4 py-10 text-center text-slate-500">Loading...</td></tr>
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>

                <!-- Sub: Calendar View -->
                <div id="social-sub-calendar" class="social-sub-content hidden">
                    <div class="flex items-center justify-between mb-4">
                        <h2 class="text-xl font-bold text-white">Post Schedule</h2>
                        <div class="flex items-center gap-3">
                            <button onclick="calendarPrev()" class="px-3 py-1.5 rounded-lg bg-slate-700 text-white text-sm">&larr;</button>
                            <span id="calendar-month" class="text-white font-medium text-sm"></span>
                            <button onclick="calendarNext()" class="px-3 py-1.5 rounded-lg bg-slate-700 text-white text-sm">&rarr;</button>
                        </div>
                    </div>
                    <div class="glass rounded-xl p-4">
                        <div class="grid grid-cols-7 gap-1 mb-2">
                            <div class="text-center text-xs text-slate-500 py-1">Sun</div>
                            <div class="text-center text-xs text-slate-500 py-1">Mon</div>
                            <div class="text-center text-xs text-slate-500 py-1">Tue</div>
                            <div class="text-center text-xs text-slate-500 py-1">Wed</div>
                            <div class="text-center text-xs text-slate-500 py-1">Thu</div>
                            <div class="text-center text-xs text-slate-500 py-1">Fri</div>
                            <div class="text-center text-xs text-slate-500 py-1">Sat</div>
                        </div>
                        <div id="calendar-grid" class="grid grid-cols-7 gap-1"></div>
                    </div>
                </div>

                <!-- Sub: Accounts -->
                <div id="social-sub-accounts" class="social-sub-content hidden">
                    <!-- Publishing Pipeline Status -->
                    <div class="glass rounded-xl p-6 mb-6 border border-slate-700/30">
                        <div class="flex items-center justify-between mb-4">
                            <h2 class="text-xl font-bold text-white">Publishing Pipeline</h2>
                            <button onclick="loadPublishStatus()" class="text-xs text-slate-400 hover:text-white">&#8635; Refresh</button>
                        </div>
                        <div id="pipeline-status" class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                            <div class="bg-slate-800/50 rounded-lg p-4 text-center">
                                <div id="pipe-twitter-dot" class="w-3 h-3 rounded-full bg-red-500 mx-auto mb-2"></div>
                                <p class="text-sm text-white font-medium">Twitter / X</p>
                                <p id="pipe-twitter-status" class="text-xs text-slate-400 mt-1">Not connected</p>
                                <button onclick="showSetupGuide('twitter')" class="mt-2 text-[10px] text-blue-400 hover:text-blue-300 underline">Setup Guide</button>
                            </div>
                            <div class="bg-slate-800/50 rounded-lg p-4 text-center">
                                <div id="pipe-linkedin-dot" class="w-3 h-3 rounded-full bg-red-500 mx-auto mb-2"></div>
                                <p class="text-sm text-white font-medium">LinkedIn</p>
                                <p id="pipe-linkedin-status" class="text-xs text-slate-400 mt-1">Not connected</p>
                                <button onclick="showSetupGuide('linkedin')" class="mt-2 text-[10px] text-blue-400 hover:text-blue-300 underline">Setup Guide</button>
                            </div>
                            <div class="bg-slate-800/50 rounded-lg p-4 text-center">
                                <div id="pipe-facebook-dot" class="w-3 h-3 rounded-full bg-red-500 mx-auto mb-2"></div>
                                <p class="text-sm text-white font-medium">Facebook</p>
                                <p id="pipe-facebook-status" class="text-xs text-slate-400 mt-1">Not connected</p>
                                <button onclick="showSetupGuide('facebook')" class="mt-2 text-[10px] text-blue-400 hover:text-blue-300 underline">Setup Guide</button>
                            </div>
                        </div>
                        <div class="flex items-center gap-4 text-xs text-slate-500 border-t border-slate-700/30 pt-3">
                            <span>Queue: <strong id="pipe-queue-count" class="text-white">0</strong> scheduled</span>
                            <span>Published: <strong id="pipe-published-count" class="text-white">0</strong></span>
                            <span>Failed: <strong id="pipe-failed-count" class="text-red-400">0</strong></span>
                        </div>
                    </div>

                    <!-- Connected Accounts -->
                    <div class="flex flex-wrap items-center justify-between gap-4 mb-4">
                        <h3 class="text-lg font-bold text-white">Connected Accounts</h3>
                        <button onclick="showAccountModal()" class="bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded-lg text-xs font-medium transition">+ Add Account</button>
                    </div>
                    <div id="accounts-list" class="grid grid-cols-1 md:grid-cols-2 gap-4"></div>
                </div>

                <!-- Sub: Automation -->
                <div id="social-sub-automation" class="social-sub-content hidden">
                    <div class="flex flex-wrap items-center justify-between gap-4 mb-6">
                        <div>
                            <h2 class="text-xl font-bold text-white">SA ISP Outreach Automation</h2>
                            <p class="text-xs text-slate-400 mt-1">Automated content targeting South African ISPs & FNOs with anti-spam protections</p>
                        </div>
                        <div class="flex gap-2">
                            <button onclick="generateNow()" class="bg-purple-600 hover:bg-purple-500 text-white px-4 py-2 rounded-lg text-xs font-medium transition">&#9889; Generate Now</button>
                            <button onclick="previewAutomation()" class="bg-slate-700 hover:bg-slate-600 text-white px-4 py-2 rounded-lg text-xs font-medium transition">&#128065; Preview</button>
                        </div>
                    </div>

                    <!-- Automation Status Card -->
                    <div class="glass rounded-xl p-6 mb-6">
                        <div class="flex items-center justify-between mb-4">
                            <div class="flex items-center gap-3">
                                <div id="auto-status-dot" class="w-3 h-3 rounded-full bg-red-500"></div>
                                <span id="auto-status-text" class="text-sm text-white font-medium">Disabled</span>
                            </div>
                            <label class="flex items-center gap-2 cursor-pointer">
                                <span class="text-xs text-slate-400">Enable Automation</span>
                                <input type="checkbox" id="auto-enabled" onchange="toggleAutomation()" class="w-10 h-5 rounded-full appearance-none bg-slate-700 checked:bg-green-600 transition cursor-pointer relative after:content-[''] after:absolute after:top-0.5 after:left-0.5 after:w-4 after:h-4 after:rounded-full after:bg-white after:transition checked:after:translate-x-5">
                            </label>
                        </div>
                        <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
                            <div>
                                <p class="text-xs text-slate-400">Total Generated</p>
                                <p id="auto-stat-generated" class="text-lg font-bold text-white">0</p>
                            </div>
                            <div>
                                <p class="text-xs text-slate-400">Last Run</p>
                                <p id="auto-stat-lastrun" class="text-xs font-medium text-slate-300">Never</p>
                            </div>
                            <div>
                                <p class="text-xs text-slate-400">Content Library</p>
                                <p id="auto-stat-templates" class="text-lg font-bold text-cyan-400">-</p>
                            </div>
                            <div>
                                <p class="text-xs text-slate-400">Target Audience</p>
                                <p class="text-lg font-bold text-purple-400">SA ISPs</p>
                            </div>
                        </div>
                    </div>

                    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
                        <!-- Schedule Settings -->
                        <div class="glass rounded-xl p-6">
                            <h3 class="text-white font-medium text-sm mb-4">&#128337; Posting Schedule</h3>
                            <div class="space-y-4">
                                <div class="grid grid-cols-2 gap-4">
                                    <div>
                                        <label class="text-xs text-slate-400 block mb-1">Max Posts/Day (per platform)</label>
                                        <input id="auto-max-daily" type="number" value="2" min="1" max="5" class="w-full px-3 py-2 rounded-lg text-sm">
                                    </div>
                                    <div>
                                        <label class="text-xs text-slate-400 block mb-1">Max Posts/Week (per platform)</label>
                                        <input id="auto-max-weekly" type="number" value="8" min="1" max="20" class="w-full px-3 py-2 rounded-lg text-sm">
                                    </div>
                                </div>
                                <div>
                                    <label class="text-xs text-slate-400 block mb-1">Min Hours Between Posts</label>
                                    <input id="auto-min-gap" type="number" value="8" min="2" max="48" class="w-full px-3 py-2 rounded-lg text-sm">
                                </div>
                                <div>
                                    <label class="text-xs text-slate-400 block mb-1">Active Platforms</label>
                                    <div class="flex flex-wrap gap-2 mt-1">
                                        <label class="flex items-center gap-1.5 text-xs text-slate-300"><input type="checkbox" id="auto-plat-twitter" checked class="w-3.5 h-3.5 rounded"> Twitter/X</label>
                                        <label class="flex items-center gap-1.5 text-xs text-slate-300"><input type="checkbox" id="auto-plat-linkedin" checked class="w-3.5 h-3.5 rounded"> LinkedIn</label>
                                        <label class="flex items-center gap-1.5 text-xs text-slate-300"><input type="checkbox" id="auto-plat-facebook" class="w-3.5 h-3.5 rounded"> Facebook</label>
                                    </div>
                                </div>
                                <div>
                                    <label class="text-xs text-slate-400 block mb-2">Posting Windows (SAST)</label>
                                    <div class="space-y-1 text-xs text-slate-300">
                                        <div class="flex items-center gap-2 bg-slate-800/50 rounded px-3 py-1.5">&#9728; Morning: 07:00 – 09:00</div>
                                        <div class="flex items-center gap-2 bg-slate-800/50 rounded px-3 py-1.5">&#9749; Lunch: 12:00 – 13:00</div>
                                        <div class="flex items-center gap-2 bg-slate-800/50 rounded px-3 py-1.5">&#127751; Evening: 17:00 – 19:00</div>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <!-- Anti-Spam Settings -->
                        <div class="glass rounded-xl p-6">
                            <h3 class="text-white font-medium text-sm mb-4">&#128737; Anti-Spam Protections</h3>
                            <div class="space-y-4">
                                <div>
                                    <label class="text-xs text-slate-400 block mb-1">Max Hashtags Per Post</label>
                                    <input id="auto-max-hashtags" type="number" value="4" min="1" max="8" class="w-full px-3 py-2 rounded-lg text-sm">
                                </div>
                                <div>
                                    <label class="text-xs text-slate-400 block mb-1">Cooldown After Burst (hours)</label>
                                    <input id="auto-cooldown" type="number" value="24" min="6" max="72" class="w-full px-3 py-2 rounded-lg text-sm">
                                    <p class="text-[10px] text-slate-500 mt-1">If 3+ posts sent in 12h, wait this long before next</p>
                                </div>
                                <div>
                                    <label class="text-xs text-slate-400 block mb-1">No Duplicate Content (days)</label>
                                    <input id="auto-no-dupe-days" type="number" value="30" min="7" max="90" class="w-full px-3 py-2 rounded-lg text-sm">
                                </div>
                                <div>
                                    <label class="text-xs text-slate-400 block mb-1">@Mention Target Every N Posts</label>
                                    <input id="auto-mention-freq" type="number" value="5" min="3" max="20" class="w-full px-3 py-2 rounded-lg text-sm">
                                    <p class="text-[10px] text-slate-500 mt-1">Only mention SA ISP handles occasionally to avoid spam flags</p>
                                </div>
                                <div class="bg-slate-800/50 rounded-lg p-3 mt-2">
                                    <p class="text-xs text-slate-400 mb-2">&#9989; Active protections:</p>
                                    <ul class="text-[10px] text-slate-500 space-y-1">
                                        <li>• Content variation enforced (60% minimum difference)</li>
                                        <li>• Rate limiting per platform per day/week</li>
                                        <li>• Burst detection with automatic cooldown</li>
                                        <li>• Posting only during peak engagement windows</li>
                                        <li>• No posting on Sundays</li>
                                        <li>• @Mentions throttled to avoid spam detection</li>
                                    </ul>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Content Mix -->
                    <div class="glass rounded-xl p-6 mb-6">
                        <h3 class="text-white font-medium text-sm mb-4">&#127912; Content Mix (weighted %)</h3>
                        <div class="grid grid-cols-2 md:grid-cols-5 gap-4">
                            <div>
                                <label class="text-xs text-slate-400 block mb-1">Product Highlights</label>
                                <input id="auto-mix-product" type="number" value="30" min="0" max="100" class="w-full px-3 py-2 rounded-lg text-sm">
                            </div>
                            <div>
                                <label class="text-xs text-slate-400 block mb-1">Industry Insights</label>
                                <input id="auto-mix-industry" type="number" value="25" min="0" max="100" class="w-full px-3 py-2 rounded-lg text-sm">
                            </div>
                            <div>
                                <label class="text-xs text-slate-400 block mb-1">Tips & Education</label>
                                <input id="auto-mix-tips" type="number" value="20" min="0" max="100" class="w-full px-3 py-2 rounded-lg text-sm">
                            </div>
                            <div>
                                <label class="text-xs text-slate-400 block mb-1">Case Studies</label>
                                <input id="auto-mix-cases" type="number" value="15" min="0" max="100" class="w-full px-3 py-2 rounded-lg text-sm">
                            </div>
                            <div>
                                <label class="text-xs text-slate-400 block mb-1">Announcements</label>
                                <input id="auto-mix-announce" type="number" value="10" min="0" max="100" class="w-full px-3 py-2 rounded-lg text-sm">
                            </div>
                        </div>
                        <div class="flex gap-3 mt-4">
                            <button onclick="saveAutomationConfig()" class="bg-blue-600 hover:bg-blue-500 text-white px-5 py-2 rounded-lg text-xs font-medium transition">Save Settings</button>
                        </div>
                        <p id="auto-save-result" class="text-xs mt-2 hidden"></p>
                    </div>

                    <!-- Automation Log -->
                    <div class="glass rounded-xl p-6">
                        <div class="flex items-center justify-between mb-4">
                            <h3 class="text-white font-medium text-sm">&#128220; Automation Log</h3>
                            <button onclick="loadAutomationLog()" class="text-xs text-slate-400 hover:text-white">&#8635; Refresh</button>
                        </div>
                        <div id="auto-log" class="max-h-64 overflow-y-auto space-y-1">
                            <p class="text-xs text-slate-500 text-center py-4">Loading...</p>
                        </div>
                    </div>
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

    <!-- User Licenses Modal -->
    <div id="user-licenses-modal" class="fixed inset-0 z-50 hidden items-center justify-center modal-bg">
        <div class="glass rounded-2xl p-8 w-full max-w-lg mx-4">
            <h3 class="text-lg font-bold text-white mb-2">User Licenses</h3>
            <p id="user-licenses-email" class="text-xs text-cyan-400 mb-4"></p>
            <div id="user-licenses-list" class="space-y-3 max-h-80 overflow-y-auto">
                <p class="text-slate-500 text-sm text-center py-4">Loading...</p>
            </div>
            <div class="flex justify-end mt-6">
                <button onclick="closeModal('user-licenses-modal')" class="bg-slate-700 hover:bg-slate-600 text-white px-6 py-2.5 rounded-lg text-sm font-medium transition">Close</button>
            </div>
        </div>
    </div>

    <!-- Add Admin Modal -->
    <div id="add-admin-modal" class="fixed inset-0 z-50 hidden items-center justify-center modal-bg">
        <div class="glass rounded-2xl p-8 w-full max-w-md mx-4">
            <h3 class="text-lg font-bold text-white mb-6">Add Admin User</h3>
            <div class="space-y-4">
                <div>
                    <label class="text-xs text-slate-400 block mb-1">Name</label>
                    <input id="admin-add-name" type="text" placeholder="John Smith" class="w-full px-4 py-2.5 rounded-lg text-sm">
                </div>
                <div>
                    <label class="text-xs text-slate-400 block mb-1">Email</label>
                    <input id="admin-add-email" type="email" placeholder="admin@company.com" class="w-full px-4 py-2.5 rounded-lg text-sm">
                </div>
                <div>
                    <label class="text-xs text-slate-400 block mb-1">Role</label>
                    <select id="admin-add-role" class="w-full px-4 py-2.5 rounded-lg text-sm">
                        <option value="admin">Admin</option>
                        <option value="viewer">Viewer (read-only)</option>
                    </select>
                </div>
                <div class="flex gap-3 mt-6">
                    <button onclick="addAdmin()" class="flex-1 bg-blue-600 hover:bg-blue-500 text-white py-2.5 rounded-lg text-sm font-medium transition">Add Admin</button>
                    <button onclick="closeModal('add-admin-modal')" class="flex-1 bg-slate-700 hover:bg-slate-600 text-white py-2.5 rounded-lg text-sm font-medium transition">Cancel</button>
                </div>
                <p id="admin-add-result" class="text-sm text-center hidden"></p>
            </div>
        </div>
    </div>

    <!-- Social Post Modal -->
    <div id="social-post-modal" class="fixed inset-0 z-50 hidden items-center justify-center modal-bg">
        <div class="glass rounded-2xl p-8 w-full max-w-lg mx-4 max-h-[90vh] overflow-y-auto">
            <h3 id="social-post-modal-title" class="text-lg font-bold text-white mb-6">New Post</h3>
            <input type="hidden" id="social-post-edit-id" value="">
            <div class="space-y-4">
                <div>
                    <label class="text-xs text-slate-400 block mb-1">Content</label>
                    <textarea id="sp-content" rows="4" placeholder="Write your post content..." class="w-full px-4 py-2.5 rounded-lg text-sm resize-none" style="background:rgba(15,23,42,0.8);border:1px solid rgba(71,85,105,0.4);color:#e2e8f0;"></textarea>
                    <span id="sp-char-count" class="text-xs text-slate-500 mt-1 block">0 / 280</span>
                </div>
                <div>
                    <label class="text-xs text-slate-400 block mb-1">Platforms</label>
                    <div class="flex flex-wrap gap-2">
                        <label class="flex items-center gap-1.5 text-xs text-slate-300"><input type="checkbox" id="sp-plat-twitter" class="w-3.5 h-3.5 rounded"> Twitter/X</label>
                        <label class="flex items-center gap-1.5 text-xs text-slate-300"><input type="checkbox" id="sp-plat-linkedin" class="w-3.5 h-3.5 rounded"> LinkedIn</label>
                        <label class="flex items-center gap-1.5 text-xs text-slate-300"><input type="checkbox" id="sp-plat-facebook" class="w-3.5 h-3.5 rounded"> Facebook</label>
                        <label class="flex items-center gap-1.5 text-xs text-slate-300"><input type="checkbox" id="sp-plat-instagram" class="w-3.5 h-3.5 rounded"> Instagram</label>
                    </div>
                </div>
                <div class="grid grid-cols-2 gap-4">
                    <div>
                        <label class="text-xs text-slate-400 block mb-1">Scheduled Date</label>
                        <input id="sp-date" type="date" class="w-full px-4 py-2.5 rounded-lg text-sm">
                    </div>
                    <div>
                        <label class="text-xs text-slate-400 block mb-1">Time</label>
                        <input id="sp-time" type="time" value="09:00" class="w-full px-4 py-2.5 rounded-lg text-sm">
                    </div>
                </div>
                <div>
                    <label class="text-xs text-slate-400 block mb-1">Hashtags</label>
                    <input id="sp-hashtags" type="text" placeholder="#connexa #networkmonitoring" class="w-full px-4 py-2.5 rounded-lg text-sm">
                </div>
                <div>
                    <label class="text-xs text-slate-400 block mb-1">Campaign</label>
                    <input id="sp-campaign" type="text" placeholder="e.g. v5.2 Launch" class="w-full px-4 py-2.5 rounded-lg text-sm">
                </div>
                <div>
                    <label class="text-xs text-slate-400 block mb-1">Image URL (optional)</label>
                    <input id="sp-image" type="url" placeholder="https://..." class="w-full px-4 py-2.5 rounded-lg text-sm">
                </div>
                <div>
                    <label class="text-xs text-slate-400 block mb-1">Status</label>
                    <select id="sp-status" class="w-full px-4 py-2.5 rounded-lg text-sm">
                        <option value="draft">Draft</option>
                        <option value="scheduled">Scheduled</option>
                        <option value="published">Published</option>
                    </select>
                </div>
                <div class="flex gap-3 mt-4">
                    <button onclick="saveSocialPost()" class="flex-1 bg-blue-600 hover:bg-blue-500 text-white py-2.5 rounded-lg text-sm font-medium transition">Save</button>
                    <button onclick="closeModal('social-post-modal')" class="flex-1 bg-slate-700 hover:bg-slate-600 text-white py-2.5 rounded-lg text-sm font-medium transition">Cancel</button>
                </div>
            </div>
        </div>
    </div>

    <!-- Import CSV Modal -->
    <div id="import-csv-modal" class="fixed inset-0 z-50 hidden items-center justify-center modal-bg">
        <div class="glass rounded-2xl p-8 w-full max-w-lg mx-4">
            <h3 class="text-lg font-bold text-white mb-4">Import Posts from CSV</h3>
            <p class="text-xs text-slate-400 mb-4">Paste CSV data below. Columns: content, platforms, scheduled_date, scheduled_time, hashtags, campaign, status</p>
            <textarea id="csv-data" rows="8" placeholder="content,platforms,scheduled_date,scheduled_time,hashtags,campaign,status
&quot;Check out Connexa v5.2!&quot;,twitter;linkedin,2025-03-06,09:00,#connexa #networkmonitoring,v5.2 Launch,draft" class="w-full px-4 py-2.5 rounded-lg text-sm font-mono resize-none" style="background:rgba(15,23,42,0.8);border:1px solid rgba(71,85,105,0.4);color:#e2e8f0;"></textarea>
            <div class="flex gap-3 mt-4">
                <button onclick="importCSV()" class="flex-1 bg-blue-600 hover:bg-blue-500 text-white py-2.5 rounded-lg text-sm font-medium transition">Import</button>
                <button onclick="closeModal('import-csv-modal')" class="flex-1 bg-slate-700 hover:bg-slate-600 text-white py-2.5 rounded-lg text-sm font-medium transition">Cancel</button>
            </div>
            <p id="csv-result" class="text-sm text-center mt-3 hidden"></p>
        </div>
    </div>

    <!-- Bulk Schedule Modal -->
    <div id="bulk-schedule-modal" class="fixed inset-0 z-50 hidden items-center justify-center modal-bg">
        <div class="glass rounded-2xl p-8 w-full max-w-md mx-4">
            <h3 class="text-lg font-bold text-white mb-4">Bulk Schedule Posts</h3>
            <p class="text-xs text-slate-400 mb-4">Schedule all selected / draft posts with a recurring interval.</p>
            <div class="space-y-4">
                <div>
                    <label class="text-xs text-slate-400 block mb-1">Start Date</label>
                    <input id="bulk-start-date" type="date" class="w-full px-4 py-2.5 rounded-lg text-sm">
                </div>
                <div>
                    <label class="text-xs text-slate-400 block mb-1">Post Every (days)</label>
                    <input id="bulk-interval" type="number" value="3" min="1" class="w-full px-4 py-2.5 rounded-lg text-sm">
                </div>
                <div>
                    <label class="text-xs text-slate-400 block mb-1">Time of Day</label>
                    <input id="bulk-time" type="time" value="09:00" class="w-full px-4 py-2.5 rounded-lg text-sm">
                </div>
                <div class="flex gap-3 mt-4">
                    <button onclick="bulkSchedule()" class="flex-1 bg-purple-600 hover:bg-purple-500 text-white py-2.5 rounded-lg text-sm font-medium transition">Schedule</button>
                    <button onclick="closeModal('bulk-schedule-modal')" class="flex-1 bg-slate-700 hover:bg-slate-600 text-white py-2.5 rounded-lg text-sm font-medium transition">Cancel</button>
                </div>
            </div>
        </div>
    </div>

    <!-- Social Account Modal -->
    <div id="account-modal" class="fixed inset-0 z-50 hidden items-center justify-center modal-bg">
        <div class="glass rounded-2xl p-8 w-full max-w-md mx-4 max-h-[90vh] overflow-y-auto">
            <h3 id="account-modal-title" class="text-lg font-bold text-white mb-6">Add Account</h3>
            <input type="hidden" id="acc-edit-id" value="">
            <div class="space-y-4">
                <div>
                    <label class="text-xs text-slate-400 block mb-1">Platform</label>
                    <select id="acc-platform" class="w-full px-4 py-2.5 rounded-lg text-sm">
                        <option value="twitter">Twitter / X</option>
                        <option value="linkedin">LinkedIn</option>
                        <option value="facebook">Facebook</option>
                        <option value="instagram">Instagram</option>
                    </select>
                </div>
                <div>
                    <label class="text-xs text-slate-400 block mb-1">Account Name / Handle</label>
                    <input id="acc-name" type="text" placeholder="@connexify" class="w-full px-4 py-2.5 rounded-lg text-sm">
                </div>
                <div>
                    <label class="text-xs text-slate-400 block mb-1">API Key / Client ID</label>
                    <input id="acc-api-key" type="text" class="w-full px-4 py-2.5 rounded-lg text-sm">
                </div>
                <div>
                    <label class="text-xs text-slate-400 block mb-1">API Secret / Client Secret</label>
                    <input id="acc-api-secret" type="password" class="w-full px-4 py-2.5 rounded-lg text-sm">
                </div>
                <div>
                    <label class="text-xs text-slate-400 block mb-1">Access Token</label>
                    <input id="acc-access-token" type="text" class="w-full px-4 py-2.5 rounded-lg text-sm">
                </div>
                <div>
                    <label class="text-xs text-slate-400 block mb-1">Access Token Secret (Twitter) / Page ID (Facebook)</label>
                    <input id="acc-extra" type="text" class="w-full px-4 py-2.5 rounded-lg text-sm">
                </div>
                <div class="flex gap-3 mt-4">
                    <button onclick="saveAccount()" class="flex-1 bg-blue-600 hover:bg-blue-500 text-white py-2.5 rounded-lg text-sm font-medium transition">Save</button>
                    <button onclick="closeModal('account-modal')" class="flex-1 bg-slate-700 hover:bg-slate-600 text-white py-2.5 rounded-lg text-sm font-medium transition">Cancel</button>
                </div>
            </div>
        </div>
    </div>

    <!-- Toast -->
    <div id="toast" class="fixed bottom-6 right-6 bg-green-600 text-white px-6 py-3 rounded-xl shadow-lg text-sm font-medium transform translate-y-20 opacity-0 transition-all duration-300 z-50"></div>

    <script>
        let TOKEN = '';
        const BASE = window.location.origin;

        // Auth
        document.getElementById('token-input').addEventListener('keydown', e => { if (e.key === 'Enter') login(); });

        async function login() {
            TOKEN = document.getElementById('token-input').value.trim();
            if (!TOKEN) return;
            try {
                const r = await fetch(`${BASE}/api/admin/stats?admin_token=${encodeURIComponent(TOKEN)}`);
                if (!r.ok) throw new Error('Invalid token');
                document.getElementById('login-section').classList.add('hidden');
                document.getElementById('dashboard-section').classList.remove('hidden');
                document.getElementById('admin-token-display').value = TOKEN;
                loadLicenses();
                loadStats();
            } catch (e) {
                const el = document.getElementById('login-error');
                el.textContent = 'Invalid admin token';
                el.classList.remove('hidden');
            }
        }

        // Tabs
        function switchTab(tab) {
            document.querySelectorAll('.tab-content').forEach(el => el.classList.add('hidden'));
            document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));
            document.getElementById('tab-' + tab).classList.remove('hidden');
            document.querySelector(`.tab-btn[data-tab="${tab}"]`).classList.add('active');
            if (tab === 'admin') { loadPortalUsers(); loadAdmins(); }
            if (tab === 'social') { loadSocialPosts(); loadSocialStats(); }
        }

        // Admin sub-tabs
        function switchAdminSub(sub) {
            document.querySelectorAll('.admin-sub-content').forEach(el => el.classList.add('hidden'));
            document.querySelectorAll('.admin-sub-btn').forEach(el => {
                el.classList.remove('active');
                el.className = el.className.replace('text-white bg-blue-600/30 border-blue-500/30', 'text-slate-400 bg-slate-800/30 border-slate-700/30');
            });
            document.getElementById('admin-sub-' + sub).classList.remove('hidden');
            const btn = document.querySelector(`.admin-sub-btn[data-sub="${sub}"]`);
            btn.className = btn.className.replace('text-slate-400 bg-slate-800/30 border-slate-700/30', 'text-white bg-blue-600/30 border-blue-500/30');
            btn.classList.add('active');
            if (sub === 'users') loadPortalUsers();
            if (sub === 'admins') loadAdmins();
            if (sub === 'smtp') loadSmtpSettings();
        }

        // Stats
        async function loadStats() {
            const r = await fetch(`${BASE}/api/admin/stats?admin_token=${encodeURIComponent(TOKEN)}`);
            const d = await r.json();
            document.getElementById('stat-total').textContent = d.total_licenses;
            document.getElementById('stat-active').textContent = d.active_licenses;
            document.getElementById('stat-bound').textContent = d.bound_licenses;
            document.getElementById('stat-expired').textContent = d.expired_licenses;
        }

        // Licenses
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
                const statusClass = isExpired ? 'status-expired' : (lic.active ? 'status-active' : 'status-inactive');
                const statusText = isExpired ? 'Expired' : (lic.active ? 'Active' : 'Inactive');
                const expDate = lic.expires ? lic.expires.substring(0, 10) : 'N/A';
                const hwBound = lic.hardware_id ? '&#128274; Bound' : '&#128275; Unbound';
                const hwClass = lic.hardware_id ? 'text-cyan-400' : 'text-slate-500';
                const email = lic.customer_email || '<span class="text-slate-600 italic">none</span>';
                const demoTag = lic.is_demo ? '<span class="ml-2 text-[10px] bg-yellow-600/20 text-yellow-400 px-1.5 py-0.5 rounded">DEMO</span>' : '';
                return `<tr class="border-b border-slate-700/30 hover:bg-slate-800/30 transition">
                    <td class="px-5 py-3"><span class="font-mono text-xs text-cyan-300">${lic.key}</span>${demoTag}</td>
                    <td class="px-5 py-3 text-xs">${email}</td>
                    <td class="px-5 py-3"><span class="inline-flex items-center gap-1.5 text-xs"><span class="w-2 h-2 rounded-full ${statusClass}"></span>${statusText}</span></td>
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
                method: 'POST', headers: {'Content-Type': 'application/json'},
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
                el.className = 'text-sm text-center text-red-400'; el.classList.remove('hidden');
            }
        }

        let editingKey = '';
        function showEditModal(key) {
            editingKey = key;
            fetch(`${BASE}/api/admin/list-licenses?admin_token=${encodeURIComponent(TOKEN)}`)
                .then(r => r.json()).then(d => {
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
                admin_token: TOKEN, license_key: editingKey,
                customer_email: document.getElementById('edit-email').value.trim(),
                expires: document.getElementById('edit-expires').value + 'T23:59:59',
                active: document.getElementById('edit-active').value === 'true'
            };
            if (document.getElementById('edit-unbind').checked) body.hardware_id = '';
            const r = await fetch(`${BASE}/api/admin/edit-license`, {
                method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(body)
            });
            const d = await r.json();
            if (d.success) { closeModal('edit-modal'); showToast('License updated'); loadLicenses(); }
            else {
                const el = document.getElementById('edit-result');
                el.textContent = d.detail || 'Error updating'; el.className = 'text-sm text-center text-red-400'; el.classList.remove('hidden');
            }
        }

        async function unbindLicense(key) {
            if (!confirm('Unbind hardware from license ' + key + '?')) return;
            const r = await fetch(`${BASE}/api/admin/edit-license`, {
                method: 'POST', headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ admin_token: TOKEN, license_key: key, hardware_id: '' })
            });
            const d = await r.json();
            if (d.success) { showToast('Hardware unbound'); loadLicenses(); }
        }

        async function deleteLicense(key) {
            if (!confirm('DELETE license ' + key + '? This cannot be undone!')) return;
            const r = await fetch(`${BASE}/api/admin/delete-license`, {
                method: 'POST', headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ admin_token: TOKEN, license_key: key })
            });
            const d = await r.json();
            if (d.success) { showToast('License deleted'); loadLicenses(); }
        }

        // Portal Users
        async function loadPortalUsers() {
            const r = await fetch(`${BASE}/api/admin/portal-users?token=${encodeURIComponent(TOKEN)}`);
            const d = await r.json();
            const tbody = document.getElementById('users-table-body');
            if (!d.users || d.users.length === 0) {
                tbody.innerHTML = '<tr><td colspan="7" class="px-5 py-10 text-center text-slate-500">No portal users found</td></tr>';
                return;
            }
            tbody.innerHTML = d.users.map(u => {
                const suspended = u.is_suspended;
                const statusBadge = suspended
                    ? '<span class="text-xs bg-red-600/20 text-red-400 px-2 py-0.5 rounded">Suspended</span>'
                    : '<span class="text-xs bg-green-600/20 text-green-400 px-2 py-0.5 rounded">Active</span>';
                const date = u.created_at ? u.created_at.substring(0, 10) : 'N/A';
                const toggleBtn = suspended
                    ? `<button onclick="toggleUser('${u.email}','unsuspend')" class="px-2.5 py-1.5 rounded-md bg-green-700/50 hover:bg-green-600/50 text-xs text-green-300 transition" title="Unsuspend">&#10003;</button>`
                    : `<button onclick="toggleUser('${u.email}','suspend')" class="px-2.5 py-1.5 rounded-md bg-red-700/50 hover:bg-red-600/50 text-xs text-red-300 transition" title="Suspend">&#10007;</button>`;
                return `<tr class="border-b border-slate-700/30 hover:bg-slate-800/30 transition">
                    <td class="px-5 py-3 text-xs text-white">${u.full_name || '<span class="text-slate-600 italic">-</span>'}</td>
                    <td class="px-5 py-3 text-xs text-cyan-300">${u.email}</td>
                    <td class="px-5 py-3 text-xs">${u.company || '-'}</td>
                    <td class="px-5 py-3 text-xs">
                        <button onclick="viewUserLicenses('${u.email}')" class="text-blue-400 hover:text-blue-300 underline">${u.license_count} license(s)</button>
                    </td>
                    <td class="px-5 py-3">${statusBadge}</td>
                    <td class="px-5 py-3 text-xs text-slate-400">${date}</td>
                    <td class="px-5 py-3 text-right">${toggleBtn}</td>
                </tr>`;
            }).join('');
        }

        async function toggleUser(email, action) {
            const r = await fetch(`${BASE}/api/admin/portal-user/toggle`, {
                method: 'POST', headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ admin_token: TOKEN, email: email, action })
            });
            const d = await r.json();
            if (d.success) { showToast('User ' + action + 'ed'); loadPortalUsers(); }
        }

        async function viewUserLicenses(email) {
            document.getElementById('user-licenses-email').textContent = email;
            document.getElementById('user-licenses-list').innerHTML = '<p class="text-slate-500 text-sm text-center py-4">Loading...</p>';
            document.getElementById('user-licenses-modal').classList.remove('hidden');
            document.getElementById('user-licenses-modal').classList.add('flex');
            const r = await fetch(`${BASE}/api/admin/portal-user/licenses?token=${encodeURIComponent(TOKEN)}&email=${encodeURIComponent(email)}`);
            const d = await r.json();
            const list = document.getElementById('user-licenses-list');
            if (!d.licenses || d.licenses.length === 0) {
                list.innerHTML = '<p class="text-slate-500 text-sm text-center py-4">No licenses found</p>';
                return;
            }
            list.innerHTML = d.licenses.map(lic => {
                const expDate = lic.expires_at ? lic.expires_at.substring(0, 10) : 'N/A';
                const statusColor = lic.status === 'active' ? 'text-green-400' : 'text-red-400';
                return `<div class="bg-slate-800/50 rounded-lg p-4 border border-slate-700/30">
                    <div class="flex items-center justify-between mb-2">
                        <span class="font-mono text-xs text-cyan-300">${lic.license_key}</span>
                        <span class="text-xs ${statusColor} capitalize">${lic.status}</span>
                    </div>
                    <div class="flex items-center gap-4 text-xs text-slate-400">
                        <span>Type: <strong class="text-white capitalize">${lic.license_type}</strong></span>
                        <span>Expires: <strong class="text-white">${expDate}</strong></span>
                        <span>${lic.duration_days} days</span>
                    </div>
                </div>`;
            }).join('');
        }

        // SMTP Settings
        async function loadSmtpSettings() {
            const r = await fetch(`${BASE}/api/admin/smtp-settings?token=${encodeURIComponent(TOKEN)}`);
            const d = await r.json();
            if (d.settings) {
                document.getElementById('smtp-host').value = d.settings.host || '';
                document.getElementById('smtp-port').value = d.settings.port || 587;
                document.getElementById('smtp-user').value = d.settings.user || '';
                document.getElementById('smtp-pass').value = d.settings.password || '';
                document.getElementById('smtp-from-email').value = d.settings.from_email || '';
                document.getElementById('smtp-from-name').value = d.settings.from_name || '';
            }
        }

        async function saveSmtp() {
            const el = document.getElementById('smtp-result');
            const r = await fetch(`${BASE}/api/admin/smtp-settings`, {
                method: 'POST', headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    admin_token: TOKEN,
                    host: document.getElementById('smtp-host').value.trim(),
                    port: parseInt(document.getElementById('smtp-port').value) || 587,
                    user: document.getElementById('smtp-user').value.trim(),
                    password: document.getElementById('smtp-pass').value,
                    from_email: document.getElementById('smtp-from-email').value.trim(),
                    from_name: document.getElementById('smtp-from-name').value.trim()
                })
            });
            const d = await r.json();
            el.textContent = d.message || 'Settings saved';
            el.className = d.success ? 'text-sm text-green-400' : 'text-sm text-red-400';
            el.classList.remove('hidden');
            if (d.success) showToast('SMTP settings saved');
        }

        async function testSmtp() {
            const el = document.getElementById('smtp-result');
            el.textContent = 'Sending test email...';
            el.className = 'text-sm text-yellow-400';
            el.classList.remove('hidden');
            const r = await fetch(`${BASE}/api/admin/smtp-test`, {
                method: 'POST', headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ admin_token: TOKEN })
            });
            const d = await r.json();
            el.textContent = d.message;
            el.className = d.success ? 'text-sm text-green-400' : 'text-sm text-red-400';
            if (d.success) showToast('Test email sent!');
        }

        // Admin Management
        async function loadAdmins() {
            const r = await fetch(`${BASE}/api/admin/admins?token=${encodeURIComponent(TOKEN)}`);
            const d = await r.json();
            const tbody = document.getElementById('admins-table-body');
            if (!d.admins || d.admins.length === 0) {
                tbody.innerHTML = '<tr><td colspan="5" class="px-5 py-10 text-center text-slate-500">No admins found</td></tr>';
                return;
            }
            tbody.innerHTML = d.admins.map(a => {
                const date = a.created_at ? a.created_at.substring(0, 10) : 'N/A';
                const roleBadge = a.role === 'super'
                    ? '<span class="text-xs bg-purple-600/20 text-purple-400 px-2 py-0.5 rounded">Super Admin</span>'
                    : a.role === 'viewer'
                    ? '<span class="text-xs bg-slate-600/20 text-slate-400 px-2 py-0.5 rounded">Viewer</span>'
                    : '<span class="text-xs bg-blue-600/20 text-blue-400 px-2 py-0.5 rounded">Admin</span>';
                const removeBtn = a.role !== 'super'
                    ? `<button onclick="removeAdmin('${a.id}')" class="px-2.5 py-1.5 rounded-md bg-red-700/50 hover:bg-red-600/50 text-xs text-red-300 transition" title="Remove">&#128465;</button>`
                    : '<span class="text-xs text-slate-600">Protected</span>';
                return `<tr class="border-b border-slate-700/30 hover:bg-slate-800/30 transition">
                    <td class="px-5 py-3 text-xs text-white">${a.name}</td>
                    <td class="px-5 py-3 text-xs text-cyan-300">${a.email}</td>
                    <td class="px-5 py-3">${roleBadge}</td>
                    <td class="px-5 py-3 text-xs text-slate-400">${date}</td>
                    <td class="px-5 py-3 text-right">${removeBtn}</td>
                </tr>`;
            }).join('');
        }

        function showAddAdminModal() {
            document.getElementById('admin-add-name').value = '';
            document.getElementById('admin-add-email').value = '';
            document.getElementById('admin-add-role').value = 'admin';
            document.getElementById('admin-add-result').classList.add('hidden');
            document.getElementById('add-admin-modal').classList.remove('hidden');
            document.getElementById('add-admin-modal').classList.add('flex');
        }

        async function addAdmin() {
            const r = await fetch(`${BASE}/api/admin/admins/add`, {
                method: 'POST', headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    admin_token: TOKEN,
                    name: document.getElementById('admin-add-name').value.trim(),
                    email: document.getElementById('admin-add-email').value.trim(),
                    role: document.getElementById('admin-add-role').value
                })
            });
            const d = await r.json();
            if (d.success) { closeModal('add-admin-modal'); showToast('Admin added'); loadAdmins(); }
            else {
                const el = document.getElementById('admin-add-result');
                el.textContent = d.detail || 'Error adding admin';
                el.className = 'text-sm text-center text-red-400'; el.classList.remove('hidden');
            }
        }

        async function removeAdmin(id) {
            if (!confirm('Remove this admin user?')) return;
            const r = await fetch(`${BASE}/api/admin/admins/remove`, {
                method: 'POST', headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ admin_token: TOKEN, admin_id: id })
            });
            const d = await r.json();
            if (d.success) { showToast('Admin removed'); loadAdmins(); }
        }

        function toggleTokenVisibility() {
            const el = document.getElementById('admin-token-display');
            el.type = el.type === 'password' ? 'text' : 'password';
        }

        // Helpers
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

        document.querySelectorAll('.modal-bg').forEach(el => {
            el.addEventListener('click', e => { if (e.target === el) closeModal(el.id); });
        });

        // ═══════════════════════════════════════════════
        //   SOCIAL MEDIA MANAGEMENT
        // ═══════════════════════════════════════════════

        let socialPosts = [];
        let socialAccounts = [];
        let calendarDate = new Date();

        // Social sub-tabs
        function switchSocialSub(sub) {
            document.querySelectorAll('.social-sub-content').forEach(el => el.classList.add('hidden'));
            document.querySelectorAll('.social-sub-btn').forEach(el => {
                el.classList.remove('active');
                el.className = el.className.replace('text-white bg-blue-600/30 border-blue-500/30', 'text-slate-400 bg-slate-800/30 border-slate-700/30');
            });
            document.getElementById('social-sub-' + sub).classList.remove('hidden');
            const btn = document.querySelector(`.social-sub-btn[data-sub="${sub}"]`);
            btn.className = btn.className.replace('text-slate-400 bg-slate-800/30 border-slate-700/30', 'text-white bg-blue-600/30 border-blue-500/30');
            btn.classList.add('active');
            if (sub === 'calendar') renderCalendar();
            if (sub === 'accounts') { loadSocialAccounts(); loadPublishStatus(); }
            if (sub === 'automation') loadAutomationConfig();
        }

        // Social Stats
        async function loadSocialStats() {
            try {
                const r = await fetch(`${BASE}/api/admin/social/stats?admin_token=${encodeURIComponent(TOKEN)}`);
                const d = await r.json();
                document.getElementById('social-stat-total').textContent = d.total_posts;
                document.getElementById('social-stat-draft').textContent = d.draft;
                document.getElementById('social-stat-scheduled').textContent = d.scheduled;
                document.getElementById('social-stat-published').textContent = d.published;
                document.getElementById('social-stat-accounts').textContent = d.active_accounts;
            } catch(e) { console.error('Stats error:', e); }
        }

        // Load Posts
        async function loadSocialPosts() {
            try {
                const r = await fetch(`${BASE}/api/admin/social/posts?admin_token=${encodeURIComponent(TOKEN)}`);
                const d = await r.json();
                socialPosts = d.posts || [];
                renderSocialPosts();
                loadSocialStats();
            } catch(e) { console.error('Load posts error:', e); }
        }

        function renderSocialPosts() {
            const filter = document.getElementById('social-filter-status').value;
            let posts = socialPosts;
            if (filter) posts = posts.filter(p => p.status === filter);
            // Sort: scheduled first, then drafts, then published; within each by date
            posts.sort((a, b) => {
                const order = {scheduled: 0, draft: 1, published: 2};
                const oa = order[a.status] ?? 3, ob = order[b.status] ?? 3;
                if (oa !== ob) return oa - ob;
                return (a.scheduled_date || '').localeCompare(b.scheduled_date || '');
            });
            const tbody = document.getElementById('social-posts-body');
            if (posts.length === 0) {
                tbody.innerHTML = '<tr><td colspan="7" class="px-4 py-10 text-center text-slate-500">No posts found. Click + New Post to start.</td></tr>';
                return;
            }
            tbody.innerHTML = posts.map(p => {
                const statusColors = {draft: 'bg-yellow-600/20 text-yellow-400', scheduled: 'bg-blue-600/20 text-blue-400', published: 'bg-green-600/20 text-green-400'};
                const statusCls = statusColors[p.status] || 'bg-slate-600/20 text-slate-400';
                const pIcons = (p.platforms || []).map(pl => {
                    const icons = {twitter: '𝕏', linkedin: 'in', facebook: 'f', instagram: '📷'};
                    return `<span class="inline-block px-1.5 py-0.5 rounded text-[10px] bg-slate-700 text-slate-300">${icons[pl] || pl}</span>`;
                }).join(' ');
                const truncated = (p.content || '').length > 80 ? p.content.substring(0, 80) + '...' : (p.content || '');
                const schedDate = p.scheduled_date ? `${p.scheduled_date} ${p.scheduled_time || ''}` : '<span class="text-slate-600">Not set</span>';
                return `<tr class="border-b border-slate-700/30 hover:bg-slate-800/30 transition">
                    <td class="px-4 py-3"><input type="checkbox" class="post-checkbox w-4 h-4 rounded" data-id="${p.id}"></td>
                    <td class="px-4 py-3 text-xs text-slate-200 max-w-xs">${escapeHtml(truncated)}</td>
                    <td class="px-4 py-3">${pIcons || '<span class="text-slate-600 text-xs">-</span>'}</td>
                    <td class="px-4 py-3 text-xs text-slate-300">${schedDate}</td>
                    <td class="px-4 py-3"><span class="text-xs px-2 py-0.5 rounded ${statusCls}">${p.status}</span></td>
                    <td class="px-4 py-3 text-xs text-slate-400">${escapeHtml(p.campaign || '-')}</td>
                    <td class="px-4 py-3 text-right">
                        <div class="flex items-center justify-end gap-1">
                            <button onclick="editSocialPost('${p.id}')" class="px-2 py-1.5 rounded-md bg-slate-700 hover:bg-slate-600 text-xs text-white transition" title="Edit">&#9998;</button>
                            <button onclick="duplicatePost('${p.id}')" class="px-2 py-1.5 rounded-md bg-slate-700 hover:bg-slate-600 text-xs text-cyan-300 transition" title="Duplicate">&#128203;</button>
                            ${p.status === 'scheduled' ? `<button onclick="publishPostNow('${p.id}')" class="px-2 py-1.5 rounded-md bg-blue-700/50 hover:bg-blue-600/50 text-xs text-blue-300 transition" title="Publish Now">&#128640;</button>` : ''}
                            ${p.status !== 'published' ? `<button onclick="markPublished('${p.id}')" class="px-2 py-1.5 rounded-md bg-green-700/50 hover:bg-green-600/50 text-xs text-green-300 transition" title="Mark Published">&#10003;</button>` : ''}
                            <button onclick="deleteSocialPost('${p.id}')" class="px-2 py-1.5 rounded-md bg-red-700/50 hover:bg-red-600/50 text-xs text-red-300 transition" title="Delete">&#128465;</button>
                        </div>
                    </td>
                </tr>`;
            }).join('');
        }

        function escapeHtml(text) {
            const d = document.createElement('div');
            d.textContent = text;
            return d.innerHTML;
        }

        function toggleSelectAll() {
            const checked = document.getElementById('select-all-posts').checked;
            document.querySelectorAll('.post-checkbox').forEach(cb => cb.checked = checked);
        }

        function getSelectedPostIds() {
            return Array.from(document.querySelectorAll('.post-checkbox:checked')).map(cb => cb.dataset.id);
        }

        // Character counter
        document.addEventListener('input', e => {
            if (e.target.id === 'sp-content') {
                const len = e.target.value.length;
                const counter = document.getElementById('sp-char-count');
                counter.textContent = `${len} / 280`;
                counter.className = len > 280 ? 'text-xs text-red-400 mt-1 block' : 'text-xs text-slate-500 mt-1 block';
            }
        });

        // Create / Edit Post Modal
        function showSocialPostModal() {
            document.getElementById('social-post-modal-title').textContent = 'New Post';
            document.getElementById('social-post-edit-id').value = '';
            document.getElementById('sp-content').value = '';
            document.getElementById('sp-date').value = '';
            document.getElementById('sp-time').value = '09:00';
            document.getElementById('sp-hashtags').value = '';
            document.getElementById('sp-campaign').value = '';
            document.getElementById('sp-image').value = '';
            document.getElementById('sp-status').value = 'draft';
            ['twitter','linkedin','facebook','instagram'].forEach(p => document.getElementById('sp-plat-'+p).checked = false);
            document.getElementById('sp-char-count').textContent = '0 / 280';
            document.getElementById('social-post-modal').classList.remove('hidden');
            document.getElementById('social-post-modal').classList.add('flex');
        }

        function editSocialPost(id) {
            const post = socialPosts.find(p => p.id === id);
            if (!post) return;
            document.getElementById('social-post-modal-title').textContent = 'Edit Post';
            document.getElementById('social-post-edit-id').value = id;
            document.getElementById('sp-content').value = post.content || '';
            document.getElementById('sp-date').value = post.scheduled_date || '';
            document.getElementById('sp-time').value = post.scheduled_time || '09:00';
            document.getElementById('sp-hashtags').value = post.hashtags || '';
            document.getElementById('sp-campaign').value = post.campaign || '';
            document.getElementById('sp-image').value = post.image_url || '';
            document.getElementById('sp-status').value = post.status || 'draft';
            const platforms = post.platforms || [];
            ['twitter','linkedin','facebook','instagram'].forEach(p => {
                document.getElementById('sp-plat-'+p).checked = platforms.includes(p);
            });
            const len = (post.content || '').length;
            document.getElementById('sp-char-count').textContent = `${len} / 280`;
            document.getElementById('social-post-modal').classList.remove('hidden');
            document.getElementById('social-post-modal').classList.add('flex');
        }

        async function saveSocialPost() {
            const editId = document.getElementById('social-post-edit-id').value;
            const platforms = [];
            ['twitter','linkedin','facebook','instagram'].forEach(p => {
                if (document.getElementById('sp-plat-'+p).checked) platforms.push(p);
            });
            const body = {
                admin_token: TOKEN,
                content: document.getElementById('sp-content').value.trim(),
                platforms,
                scheduled_date: document.getElementById('sp-date').value,
                scheduled_time: document.getElementById('sp-time').value || '09:00',
                hashtags: document.getElementById('sp-hashtags').value.trim(),
                campaign: document.getElementById('sp-campaign').value.trim(),
                image_url: document.getElementById('sp-image').value.trim(),
                status: document.getElementById('sp-status').value,
            };
            let url = `${BASE}/api/admin/social/posts`;
            if (editId) { body.post_id = editId; url += '/edit'; }
            const r = await fetch(url, { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(body) });
            const d = await r.json();
            if (d.success) { closeModal('social-post-modal'); showToast(editId ? 'Post updated' : 'Post created'); loadSocialPosts(); }
        }

        async function deleteSocialPost(id) {
            if (!confirm('Delete this post?')) return;
            const r = await fetch(`${BASE}/api/admin/social/posts/delete`, {
                method: 'POST', headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ admin_token: TOKEN, post_id: id })
            });
            if ((await r.json()).success) { showToast('Post deleted'); loadSocialPosts(); }
        }

        async function duplicatePost(id) {
            const r = await fetch(`${BASE}/api/admin/social/posts/duplicate`, {
                method: 'POST', headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ admin_token: TOKEN, post_id: id })
            });
            if ((await r.json()).success) { showToast('Post duplicated'); loadSocialPosts(); }
        }

        async function markPublished(id) {
            const r = await fetch(`${BASE}/api/admin/social/posts/mark-published`, {
                method: 'POST', headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ admin_token: TOKEN, post_id: id })
            });
            if ((await r.json()).success) { showToast('Marked as published'); loadSocialPosts(); }
        }

        // CSV Import
        function showImportCSVModal() {
            document.getElementById('csv-data').value = '';
            document.getElementById('csv-result').classList.add('hidden');
            document.getElementById('import-csv-modal').classList.remove('hidden');
            document.getElementById('import-csv-modal').classList.add('flex');
        }

        async function importCSV() {
            const raw = document.getElementById('csv-data').value.trim();
            if (!raw) return;
            const lines = raw.split('\\n');
            const header = lines[0].toLowerCase().split(',').map(h => h.trim().replace(/^"|"$/g, ''));
            const rows = [];
            for (let i = 1; i < lines.length; i++) {
                const vals = parseCSVLine(lines[i]);
                if (vals.length < 1) continue;
                const row = {};
                header.forEach((h, idx) => { row[h] = (vals[idx] || '').trim(); });
                if (row.content || row.text) rows.push(row);
            }
            if (rows.length === 0) {
                const el = document.getElementById('csv-result');
                el.textContent = 'No valid rows found. Check your CSV format.';
                el.className = 'text-sm text-center mt-3 text-red-400'; el.classList.remove('hidden');
                return;
            }
            const r = await fetch(`${BASE}/api/admin/social/posts/import-csv`, {
                method: 'POST', headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ admin_token: TOKEN, csv_rows: rows })
            });
            const d = await r.json();
            if (d.success) {
                closeModal('import-csv-modal');
                showToast(`Imported ${d.imported} posts`);
                loadSocialPosts();
            }
        }

        function parseCSVLine(line) {
            const result = []; let current = ''; let inQuotes = false;
            for (let i = 0; i < line.length; i++) {
                const ch = line[i];
                if (ch === '"') { inQuotes = !inQuotes; }
                else if (ch === ',' && !inQuotes) { result.push(current); current = ''; }
                else { current += ch; }
            }
            result.push(current);
            return result;
        }

        // Bulk Schedule
        function showBulkScheduleModal() {
            const today = new Date().toISOString().split('T')[0];
            document.getElementById('bulk-start-date').value = today;
            document.getElementById('bulk-interval').value = '3';
            document.getElementById('bulk-time').value = '09:00';
            document.getElementById('bulk-schedule-modal').classList.remove('hidden');
            document.getElementById('bulk-schedule-modal').classList.add('flex');
        }

        async function bulkSchedule() {
            let ids = getSelectedPostIds();
            if (ids.length === 0) {
                // If none selected, use all drafts
                ids = socialPosts.filter(p => p.status === 'draft').map(p => p.id);
            }
            if (ids.length === 0) { showToast('No posts to schedule'); return; }
            const r = await fetch(`${BASE}/api/admin/social/posts/bulk-schedule`, {
                method: 'POST', headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    admin_token: TOKEN,
                    post_ids: ids,
                    start_date: document.getElementById('bulk-start-date').value,
                    interval_days: parseInt(document.getElementById('bulk-interval').value) || 3,
                    time: document.getElementById('bulk-time').value || '09:00'
                })
            });
            const d = await r.json();
            if (d.success) {
                closeModal('bulk-schedule-modal');
                showToast(`Scheduled ${d.scheduled} posts`);
                loadSocialPosts();
            }
        }

        // Calendar
        function renderCalendar() {
            const year = calendarDate.getFullYear();
            const month = calendarDate.getMonth();
            const monthNames = ['January','February','March','April','May','June','July','August','September','October','November','December'];
            document.getElementById('calendar-month').textContent = `${monthNames[month]} ${year}`;
            const firstDay = new Date(year, month, 1).getDay();
            const daysInMonth = new Date(year, month + 1, 0).getDate();
            const today = new Date().toISOString().split('T')[0];
            // Build map of posts per day
            const dayPosts = {};
            socialPosts.forEach(p => {
                if (p.scheduled_date) {
                    const d = p.scheduled_date.substring(0, 10);
                    if (!dayPosts[d]) dayPosts[d] = [];
                    dayPosts[d].push(p);
                }
            });
            let html = '';
            // Blanks for first row
            for (let i = 0; i < firstDay; i++) html += '<div class="min-h-[80px] rounded-lg"></div>';
            for (let day = 1; day <= daysInMonth; day++) {
                const dateStr = `${year}-${String(month+1).padStart(2,'0')}-${String(day).padStart(2,'0')}`;
                const isToday = dateStr === today;
                const posts = dayPosts[dateStr] || [];
                const bgClass = isToday ? 'bg-blue-900/30 border-blue-500/40' : 'bg-slate-800/30 border-slate-700/20';
                html += `<div class="min-h-[80px] rounded-lg border ${bgClass} p-1.5">`;
                html += `<div class="text-xs font-medium ${isToday ? 'text-blue-400' : 'text-slate-400'} mb-1">${day}</div>`;
                posts.forEach(p => {
                    const colors = {draft: 'bg-yellow-600/30 text-yellow-300', scheduled: 'bg-blue-600/30 text-blue-300', published: 'bg-green-600/30 text-green-300'};
                    const cls = colors[p.status] || 'bg-slate-600/30 text-slate-300';
                    const text = (p.content || '').substring(0, 25);
                    html += `<div class="text-[10px] ${cls} rounded px-1 py-0.5 mb-0.5 truncate cursor-pointer" onclick="editSocialPost('${p.id}')" title="${escapeHtml(p.content || '')}">${escapeHtml(text)}</div>`;
                });
                html += '</div>';
            }
            document.getElementById('calendar-grid').innerHTML = html;
        }

        function calendarPrev() { calendarDate.setMonth(calendarDate.getMonth() - 1); renderCalendar(); }
        function calendarNext() { calendarDate.setMonth(calendarDate.getMonth() + 1); renderCalendar(); }

        // Social Accounts
        async function loadSocialAccounts() {
            try {
                const r = await fetch(`${BASE}/api/admin/social/accounts?admin_token=${encodeURIComponent(TOKEN)}`);
                const d = await r.json();
                socialAccounts = d.accounts || [];
                renderAccounts();
            } catch(e) { console.error('Load accounts error:', e); }
        }

        function renderAccounts() {
            const container = document.getElementById('accounts-list');
            if (socialAccounts.length === 0) {
                container.innerHTML = '<div class="col-span-2 glass rounded-xl p-8 text-center text-slate-500">No social accounts configured. Click + Add Account to connect a platform.</div>';
                return;
            }
            const platformColors = {
                twitter: 'from-slate-800 to-slate-900 border-slate-600', linkedin: 'from-blue-900/30 to-blue-950/30 border-blue-700/30',
                facebook: 'from-blue-800/20 to-blue-900/20 border-blue-600/30', instagram: 'from-purple-900/20 to-pink-900/20 border-purple-600/30'
            };
            const platformIcons = { twitter: '𝕏', linkedin: 'in', facebook: 'f', instagram: '📷' };
            container.innerHTML = socialAccounts.map(a => {
                const cls = platformColors[a.platform] || 'from-slate-800 to-slate-900 border-slate-600';
                const icon = platformIcons[a.platform] || '?';
                const enabledBadge = a.enabled !== false
                    ? '<span class="text-[10px] bg-green-600/20 text-green-400 px-1.5 py-0.5 rounded">Active</span>'
                    : '<span class="text-[10px] bg-red-600/20 text-red-400 px-1.5 py-0.5 rounded">Disabled</span>';
                return `<div class="rounded-xl bg-gradient-to-br ${cls} border p-5">
                    <div class="flex items-center justify-between mb-3">
                        <div class="flex items-center gap-3">
                            <div class="w-10 h-10 rounded-lg bg-slate-700/50 flex items-center justify-center text-lg font-bold text-white">${icon}</div>
                            <div>
                                <p class="text-white text-sm font-medium capitalize">${a.platform}</p>
                                <p class="text-xs text-slate-400">${escapeHtml(a.account_name || '-')}</p>
                            </div>
                        </div>
                        ${enabledBadge}
                    </div>
                    <div class="text-xs text-slate-500 mb-3">API Key: ${a.api_key ? '••••' + a.api_key.slice(-4) : 'Not set'}</div>
                    <div id="test-result-${a.id}" class="text-xs mb-2 hidden"></div>
                    <div class="flex gap-2">
                        <button onclick="testAccount('${a.id}')" class="px-3 py-1.5 rounded-md bg-green-700/50 hover:bg-green-600/50 text-xs text-green-300 transition">&#9889; Test</button>
                        <button onclick="editAccount('${a.id}')" class="px-3 py-1.5 rounded-md bg-slate-700 hover:bg-slate-600 text-xs text-white transition">Edit</button>
                        <button onclick="deleteAccount('${a.id}')" class="px-3 py-1.5 rounded-md bg-red-700/50 hover:bg-red-600/50 text-xs text-red-300 transition">Remove</button>
                    </div>
                </div>`;
            }).join('');
        }

        function showAccountModal(acc) {
            document.getElementById('account-modal-title').textContent = acc ? 'Edit Account' : 'Add Account';
            document.getElementById('acc-edit-id').value = acc ? acc.id : '';
            document.getElementById('acc-platform').value = acc ? acc.platform : 'twitter';
            document.getElementById('acc-name').value = acc ? acc.account_name : '';
            document.getElementById('acc-api-key').value = acc ? acc.api_key : '';
            document.getElementById('acc-api-secret').value = acc ? (acc.api_secret || '') : '';
            document.getElementById('acc-access-token').value = acc ? acc.access_token : '';
            document.getElementById('acc-extra').value = acc ? (acc.access_token_secret || acc.page_id || '') : '';
            document.getElementById('account-modal').classList.remove('hidden');
            document.getElementById('account-modal').classList.add('flex');
        }

        function editAccount(id) {
            const acc = socialAccounts.find(a => a.id === id);
            if (acc) showAccountModal(acc);
        }

        async function saveAccount() {
            const platform = document.getElementById('acc-platform').value;
            const body = {
                admin_token: TOKEN,
                id: document.getElementById('acc-edit-id').value || undefined,
                platform,
                account_name: document.getElementById('acc-name').value.trim(),
                api_key: document.getElementById('acc-api-key').value.trim(),
                api_secret: document.getElementById('acc-api-secret').value,
                access_token: document.getElementById('acc-access-token').value.trim(),
            };
            const extra = document.getElementById('acc-extra').value.trim();
            if (platform === 'twitter') body.access_token_secret = extra;
            else body.page_id = extra;
            const r = await fetch(`${BASE}/api/admin/social/accounts`, {
                method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(body)
            });
            const d = await r.json();
            if (d.success) { closeModal('account-modal'); showToast('Account saved'); loadSocialAccounts(); }
        }

        async function deleteAccount(id) {
            if (!confirm('Remove this social account?')) return;
            const r = await fetch(`${BASE}/api/admin/social/accounts/delete`, {
                method: 'POST', headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ admin_token: TOKEN, account_id: id })
            });
            if ((await r.json()).success) { showToast('Account removed'); loadSocialAccounts(); }
        }

        // ═══════════════════════════════════════════════
        //   AUTOMATION ENGINE UI
        // ═══════════════════════════════════════════════

        let autoConfig = null;

        async function loadAutomationConfig() {
            try {
                const r = await fetch(`${BASE}/api/admin/social/automation/config?admin_token=${encodeURIComponent(TOKEN)}`);
                const d = await r.json();
                autoConfig = d.config;
                renderAutomationConfig();
                loadAutomationLog();
                loadContentLibraryStats();
            } catch(e) { console.error('Automation config error:', e); }
        }

        function renderAutomationConfig() {
            if (!autoConfig) return;
            const enabled = autoConfig.enabled;
            document.getElementById('auto-enabled').checked = enabled;
            document.getElementById('auto-status-dot').className = 'w-3 h-3 rounded-full ' + (enabled ? 'bg-green-500 animate-pulse' : 'bg-red-500');
            document.getElementById('auto-status-text').textContent = enabled ? 'Active — Monitoring & Generating' : 'Disabled';
            document.getElementById('auto-stat-generated').textContent = autoConfig.total_generated || 0;
            document.getElementById('auto-stat-lastrun').textContent = autoConfig.last_run ? autoConfig.last_run.substring(0, 16).replace('T', ' ') : 'Never';

            const sched = autoConfig.posting_schedule || {};
            document.getElementById('auto-max-daily').value = sched.max_posts_per_day || 2;
            document.getElementById('auto-max-weekly').value = sched.max_posts_per_week || 8;
            document.getElementById('auto-min-gap').value = sched.min_hours_between_posts || 8;

            const platforms = autoConfig.platforms || [];
            document.getElementById('auto-plat-twitter').checked = platforms.includes('twitter');
            document.getElementById('auto-plat-linkedin').checked = platforms.includes('linkedin');
            document.getElementById('auto-plat-facebook').checked = platforms.includes('facebook');

            const spam = autoConfig.anti_spam || {};
            document.getElementById('auto-max-hashtags').value = spam.max_hashtags_per_post || 4;
            document.getElementById('auto-cooldown').value = spam.cooldown_after_burst || 24;
            document.getElementById('auto-no-dupe-days').value = spam.no_duplicate_content_days || 30;
            document.getElementById('auto-mention-freq').value = spam.mention_frequency || 5;

            const mix = autoConfig.content_mix || {};
            document.getElementById('auto-mix-product').value = mix.product_highlights || 30;
            document.getElementById('auto-mix-industry').value = mix.industry_insights || 25;
            document.getElementById('auto-mix-tips').value = mix.tips_and_education || 20;
            document.getElementById('auto-mix-cases').value = mix.case_studies || 15;
            document.getElementById('auto-mix-announce').value = mix.announcements || 10;
        }

        async function toggleAutomation() {
            const enabled = document.getElementById('auto-enabled').checked;
            const r = await fetch(`${BASE}/api/admin/social/automation/config`, {
                method: 'POST', headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ admin_token: TOKEN, enabled })
            });
            const d = await r.json();
            if (d.success) {
                autoConfig = d.config;
                renderAutomationConfig();
                showToast(enabled ? 'Automation enabled' : 'Automation disabled');
            }
        }

        async function saveAutomationConfig() {
            const platforms = [];
            if (document.getElementById('auto-plat-twitter').checked) platforms.push('twitter');
            if (document.getElementById('auto-plat-linkedin').checked) platforms.push('linkedin');
            if (document.getElementById('auto-plat-facebook').checked) platforms.push('facebook');

            const body = {
                admin_token: TOKEN,
                platforms,
                posting_schedule: {
                    max_posts_per_day: parseInt(document.getElementById('auto-max-daily').value) || 2,
                    max_posts_per_week: parseInt(document.getElementById('auto-max-weekly').value) || 8,
                    min_hours_between_posts: parseInt(document.getElementById('auto-min-gap').value) || 8,
                },
                anti_spam: {
                    max_hashtags_per_post: parseInt(document.getElementById('auto-max-hashtags').value) || 4,
                    cooldown_after_burst: parseInt(document.getElementById('auto-cooldown').value) || 24,
                    no_duplicate_content_days: parseInt(document.getElementById('auto-no-dupe-days').value) || 30,
                    mention_frequency: parseInt(document.getElementById('auto-mention-freq').value) || 5,
                },
                content_mix: {
                    product_highlights: parseInt(document.getElementById('auto-mix-product').value) || 30,
                    industry_insights: parseInt(document.getElementById('auto-mix-industry').value) || 25,
                    tips_and_education: parseInt(document.getElementById('auto-mix-tips').value) || 20,
                    case_studies: parseInt(document.getElementById('auto-mix-cases').value) || 15,
                    announcements: parseInt(document.getElementById('auto-mix-announce').value) || 10,
                },
            };

            const r = await fetch(`${BASE}/api/admin/social/automation/config`, {
                method: 'POST', headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(body)
            });
            const d = await r.json();
            const el = document.getElementById('auto-save-result');
            if (d.success) {
                autoConfig = d.config;
                el.textContent = 'Settings saved';
                el.className = 'text-xs mt-2 text-green-400';
                showToast('Automation settings saved');
            } else {
                el.textContent = 'Error saving settings';
                el.className = 'text-xs mt-2 text-red-400';
            }
            el.classList.remove('hidden');
            setTimeout(() => el.classList.add('hidden'), 3000);
        }

        async function generateNow() {
            const platforms = [];
            if (document.getElementById('auto-plat-twitter').checked) platforms.push('twitter');
            if (document.getElementById('auto-plat-linkedin').checked) platforms.push('linkedin');
            if (document.getElementById('auto-plat-facebook').checked) platforms.push('facebook');
            if (platforms.length === 0) { showToast('Select at least one platform'); return; }

            const r = await fetch(`${BASE}/api/admin/social/automation/generate-now`, {
                method: 'POST', headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ admin_token: TOKEN, platforms })
            });
            const d = await r.json();
            if (d.success) {
                const count = d.generated.filter(g => g.success).length;
                const skipped = d.generated.filter(g => !g.success);
                if (count > 0) {
                    showToast(`Generated ${count} post(s)`);
                    loadSocialPosts();
                    loadAutomationConfig();
                } else if (skipped.length > 0) {
                    showToast('Skipped: ' + skipped[0].reason);
                }
            }
        }

        async function previewAutomation() {
            const r = await fetch(`${BASE}/api/admin/social/automation/preview`, {
                method: 'POST', headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ admin_token: TOKEN, count: 5, platform: 'twitter' })
            });
            const d = await r.json();
            if (d.previews && d.previews.length > 0) {
                let html = '<div class="space-y-3">';
                d.previews.forEach((p, i) => {
                    const catColors = {
                        product_highlights: 'bg-blue-600/20 text-blue-400',
                        industry_insights: 'bg-purple-600/20 text-purple-400',
                        tips_and_education: 'bg-green-600/20 text-green-400',
                        case_studies: 'bg-orange-600/20 text-orange-400',
                        announcements: 'bg-cyan-600/20 text-cyan-400',
                    };
                    const catCls = catColors[p.category] || 'bg-slate-600/20 text-slate-400';
                    html += `<div class="bg-slate-800/50 rounded-lg p-4 border border-slate-700/30">
                        <div class="flex items-center gap-2 mb-2">
                            <span class="text-xs px-2 py-0.5 rounded ${catCls}">${(p.category || '').replace(/_/g, ' ')}</span>
                            <span class="text-[10px] text-slate-500">${p.platform}</span>
                        </div>
                        <p class="text-xs text-slate-200">${escapeHtml(p.content)}</p>
                    </div>`;
                });
                html += '</div>';
                // Show in a simple overlay
                const overlay = document.createElement('div');
                overlay.className = 'fixed inset-0 z-50 flex items-center justify-center modal-bg';
                overlay.onclick = (e) => { if (e.target === overlay) overlay.remove(); };
                overlay.innerHTML = `<div class="glass rounded-2xl p-8 w-full max-w-lg mx-4 max-h-[80vh] overflow-y-auto">
                    <h3 class="text-lg font-bold text-white mb-4">Content Preview (next 5 posts)</h3>
                    ${html}
                    <div class="flex justify-end mt-4"><button onclick="this.closest('.fixed').remove()" class="bg-slate-700 hover:bg-slate-600 text-white px-6 py-2.5 rounded-lg text-sm font-medium transition">Close</button></div>
                </div>`;
                document.body.appendChild(overlay);
            } else {
                showToast('No previews available — check rate limits');
            }
        }

        async function loadAutomationLog() {
            try {
                const r = await fetch(`${BASE}/api/admin/social/automation/log?admin_token=${encodeURIComponent(TOKEN)}&limit=30`);
                const d = await r.json();
                const container = document.getElementById('auto-log');
                const entries = (d.entries || []).reverse();
                if (entries.length === 0) {
                    container.innerHTML = '<p class="text-xs text-slate-500 text-center py-4">No automation activity yet. Enable automation or click Generate Now.</p>';
                    return;
                }
                container.innerHTML = entries.map(e => {
                    const actionColors = {
                        generated: 'text-green-400', manual_generate: 'text-cyan-400',
                        skipped: 'text-yellow-400', error: 'text-red-400',
                        published: 'text-emerald-400', publish_failed: 'text-red-400',
                    };
                    const color = actionColors[e.action] || 'text-slate-400';
                    const time = e.timestamp ? e.timestamp.substring(11, 16) : '';
                    const date = e.timestamp ? e.timestamp.substring(0, 10) : '';
                    return `<div class="flex items-start gap-2 text-xs py-1.5 border-b border-slate-800/50">
                        <span class="text-slate-500 whitespace-nowrap">${date} ${time}</span>
                        <span class="${color} font-medium min-w-[56px]">${e.action}</span>
                        <span class="text-slate-400">${e.platform || '-'}</span>
                        <span class="text-slate-500 truncate flex-1">${escapeHtml(e.content_preview || e.reason || e.note || '')}</span>
                    </div>`;
                }).join('');
            } catch(e) { console.error('Log error:', e); }
        }

        async function loadContentLibraryStats() {
            try {
                const r = await fetch(`${BASE}/api/admin/social/automation/content-library?admin_token=${encodeURIComponent(TOKEN)}`);
                const d = await r.json();
                document.getElementById('auto-stat-templates').textContent = d.total_templates || '-';
            } catch(e) {}
        }

        // ═══════════════════════════════════════════════
        //   PUBLISHING PIPELINE & SETUP WIZARD
        // ═══════════════════════════════════════════════

        async function loadPublishStatus() {
            try {
                const r = await fetch(`${BASE}/api/admin/social/publish/status?admin_token=${encodeURIComponent(TOKEN)}`);
                const d = await r.json();
                ['twitter', 'linkedin', 'facebook'].forEach(p => {
                    const s = d.accounts[p] || {};
                    const dot = document.getElementById(`pipe-${p}-dot`);
                    const label = document.getElementById(`pipe-${p}-status`);
                    if (s.connected) {
                        dot.className = 'w-3 h-3 rounded-full bg-green-500 mx-auto mb-2';
                        label.textContent = s.account_name || 'Connected';
                        label.className = 'text-xs text-green-400 mt-1';
                    } else {
                        dot.className = 'w-3 h-3 rounded-full bg-red-500 mx-auto mb-2';
                        label.textContent = 'Not connected';
                        label.className = 'text-xs text-slate-400 mt-1';
                    }
                });
                document.getElementById('pipe-queue-count').textContent = d.queue.scheduled || 0;
                document.getElementById('pipe-published-count').textContent = d.queue.published || 0;
                document.getElementById('pipe-failed-count').textContent = d.queue.failed || 0;
            } catch(e) { console.error('Pipeline status error:', e); }
        }

        async function testAccount(accountId) {
            const el = document.getElementById(`test-result-${accountId}`);
            el.textContent = 'Testing...';
            el.className = 'text-xs mb-2 text-yellow-400';
            el.classList.remove('hidden');
            try {
                const r = await fetch(`${BASE}/api/admin/social/accounts/test`, {
                    method: 'POST', headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ admin_token: TOKEN, account_id: accountId })
                });
                const d = await r.json();
                if (d.success) {
                    el.textContent = `Connected as ${d.username || d.name || 'verified'}`;
                    el.className = 'text-xs mb-2 text-green-400';
                    showToast(`${d.platform} connected successfully!`);
                } else {
                    el.textContent = d.error || 'Connection failed';
                    el.className = 'text-xs mb-2 text-red-400';
                }
            } catch(e) {
                el.textContent = 'Network error';
                el.className = 'text-xs mb-2 text-red-400';
            }
        }

        async function showSetupGuide(platform) {
            try {
                const r = await fetch(`${BASE}/api/admin/social/setup-guide?admin_token=${encodeURIComponent(TOKEN)}`);
                const d = await r.json();
                const guide = d.platforms[platform];
                if (!guide) return;

                const overlay = document.createElement('div');
                overlay.className = 'fixed inset-0 z-50 flex items-center justify-center modal-bg';
                overlay.onclick = (e) => { if(e.target === overlay) overlay.remove(); };
                overlay.innerHTML = `<div class="glass rounded-2xl p-8 w-full max-w-lg mx-4 max-h-[80vh] overflow-y-auto">
                    <h3 class="text-lg font-bold text-white mb-2">${escapeHtml(guide.name)} Setup Guide</h3>
                    <p class="text-xs text-slate-400 mb-4">Free tier: ${escapeHtml(guide.free_tier)}</p>
                    <div class="space-y-3 mb-6">
                        ${guide.steps.map(s => `<div class="flex gap-3 text-xs">
                            <span class="text-blue-400 font-bold min-w-[20px]">${s.substring(0, 2)}</span>
                            <span class="text-slate-300">${escapeHtml(s.substring(3))}</span>
                        </div>`).join('')}
                    </div>
                    <div class="flex gap-3 mb-4">
                        <a href="${escapeHtml(guide.signup_url)}" target="_blank" rel="noopener" class="bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded-lg text-xs font-medium transition">Create Account &#8599;</a>
                        <a href="${escapeHtml(guide.developer_url)}" target="_blank" rel="noopener" class="bg-purple-600 hover:bg-purple-500 text-white px-4 py-2 rounded-lg text-xs font-medium transition">Developer Portal &#8599;</a>
                    </div>
                    <p class="text-[10px] text-slate-500 mb-4">After creating your account & app, click the button below to add your API credentials:</p>
                    <div class="flex gap-3">
                        <button onclick="this.closest('.fixed').remove(); showAccountModal({platform:'${platform}'})" class="bg-green-600 hover:bg-green-500 text-white px-4 py-2 rounded-lg text-xs font-medium transition">Add ${escapeHtml(guide.name)} Credentials</button>
                        <button onclick="this.closest('.fixed').remove()" class="bg-slate-700 hover:bg-slate-600 text-white px-4 py-2 rounded-lg text-xs font-medium transition">Close</button>
                    </div>
                </div>`;
                document.body.appendChild(overlay);
            } catch(e) { showToast('Error loading setup guide'); }
        }

        async function publishPostNow(postId) {
            if (!confirm('Publish this post now to connected platforms?')) return;
            const r = await fetch(`${BASE}/api/admin/social/publish`, {
                method: 'POST', headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ admin_token: TOKEN, post_id: postId })
            });
            const d = await r.json();
            if (d.success) {
                showToast('Post published successfully!');
                loadSocialPosts();
                loadPublishStatus();
            } else {
                const errors = (d.results || []).filter(r => !r.success).map(r => r.error).join('; ');
                showToast('Publish failed: ' + (errors || 'Unknown error'));
            }
        }
    </script>
</body>
</html>"""
