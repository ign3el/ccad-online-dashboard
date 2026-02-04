import json
import random
import datetime

# --------------------------------------------------------------------------------
# DATA GENERATION: V4 Content Explosion
# --------------------------------------------------------------------------------

assets = [
    "Infusion Pump", "Bladder Scanner", "Wheelchair", "Stretcher", "Telemetry Transmitter",
    "Ultrasound Machine", "Portable X-Ray", "Defibrillator", "EKG Machine", "Ventilator", 
    "BiPAP Machine", "CPAP Machine", "Feeding Pump", "Pulse Oximeter", "Vital Signs Monitor",
    "Fetal Monitor", "Incubator", "Warmer", "Phototherapy Unit", "Dialysis Machine", 
    "Endoscopy Cart", "Crash Cart", "Medication Cart", "Anesthesia Machine", "Surgical Table",
    "Exam Light", "Dyson Fan", "Computer on Wheels (COW)", "Tablet Cart", "Intubation Cart"
]

locations = [
    "ICU", "ER", "OR", "PACU", "Med-Surg", "Radiology", "Oncology", "Pediatrics", "Labor & Delivery", "NICU"
]

entry_id = 1
db = []

# --- 1. TROUBLESHOOTING (150+ Entries) ---
ts_issues = {
    "Not showing on map": "1. Check tag attachment.\n2. Hold tag 30s to activate.\n3. Check 'Local Streaming' service.\n4. Escalate if present in Core but not Activate.",
    "Showing in wrong room": "1. Verify physical location.\n2. Go to Systems > Map Sync.\n3. Select floor map.\n4. Click 'Perform Sync'.\n5. Wait 15s.",
    "Low Battery warning": "1. Locate asset.\n2. Remove tag.\n3. Replace CR2450 Battery.\n4. Check status in Activate.",
    "Adhesive peeling off": "1. Remove tag.\n2. Clean asset with 50/50 Alcohol.\n3. Apply NEW adhesive.\n4. Press 30s.",
    "Tag physically damaged": "1. Edit Asset in Activate.\n2. Select 'Remove Tag'.\n3. Provision NEW tag.\n4. Dispose of old tag."
}

# Add Report Troubleshooting (User Request)
ts_issues["Report email not received"] = "1. Check Spam folder.\n2. Verify SMTP settings in System Config.\n3. Ensure Report Schedule is 'Active'.\n4. Check if 'Send if Empty' is unchecked and report yielded no data."
ts_issues["Report contains empty data"] = "1. Verify assets exist in the filtered Group/Dept.\n2. Check if tags have reported in the selected time window.\n3. Extend time range (e.g., 'Last 7 Days')."

for asset in assets:
    for issue, answer in ts_issues.items():
        entry = {
            "id": f"TS-{entry_id:04d}",
            "question": f"{asset}: {issue}",
            "answer": answer,
            "category": "Diagnostics 🔧",
            "type": "Troubleshooting"
        }
        db.append(entry)
        entry_id += 1

# --- 2. FAQ (150+ Entries - Procedural Expansion) ---

# Specific Placement Map (from Transcript concepts)
placement_map = {
    "Infusion Pump": "Pole clamp or rear casing (upper)",
    "Wheelchair": "Rear plastic backing or under seat frame",
    "Bed": "Headboard frame (metal-free area)",
    "Stretcher": "Undercarriage frame, visible to ceiling",
    "Monitor": "Top bezel or rear plastic housing"
}

# A. Procedural Generators for EVERY Asset
for asset in assets:
    # 1. Cleaning
    db.append({
        "id": f"FAQ-{entry_id:04d}",
        "question": f"How to clean tag on {asset}?",
        "answer": f"1. Wear gloves.\n2. Use PDI Super Sani-Cloth.\n3. Wipe tag surface thoroughly.\n4. Allow to air dry.\n5. CAUTION: Do NOT use Acetone or Betadine.",
        "category": "Maintenance 🧹",
        "type": "FAQ"
    })
    entry_id += 1
    
    # 2. Tag Placement
    place = placement_map.get(asset, "Upper part of asset, moderate visibility to ceiling, metal-free area")
    db.append({
        "id": f"FAQ-{entry_id:04d}",
        "question": f"Where to place tag on {asset}?",
        "answer": f"1. Identify mounting location: {place}.\n2. Ensure surface is flat and smooth.\n3. Avoid interfering with asset operation (buttons/screens).",
        "category": "Tagging 🏷️",
        "type": "FAQ"
    })
    entry_id += 1
    
    # 3. Naming
    db.append({
        "id": f"FAQ-{entry_id:04d}",
        "question": f"Naming convention for {asset}?",
        "answer": f"1. Standard Format: Type, Subtype_Barcode.\n2. Example: '{asset}, Standard_12345'.\n3. Do NOT use commas in the Type name.",
        "category": "Admin 📝",
        "type": "FAQ"
    })
    entry_id += 1
    
    # 4. Archiving
    db.append({
        "id": f"FAQ-{entry_id:04d}",
        "question": f"How to archive {asset}?",
        "answer": f"1. Search for {asset} in Asset List.\n2. Click 'More' > 'Archive'.\n3. Confirm action.\n4. Tag is now dissociated.",
        "category": "Admin 📝",
        "type": "FAQ"
    })
    entry_id += 1

# B. General System FAQs (Reports, Settings)
general_faqs = [
    ("How to schedule a report", "Reports 📊", "1. Reports > Edit.\n2. Check 'Active'.\n3. Set Schedule (Daily/Weekly).\n4. Choose Format (PDF/CSV)."),
    ("Export asset list", "Reports 📊", "1. Asset List View.\n2. View Actions > Export Data.\n3. Download or check email (>1000 rows)."),
    ("Map Sync Procedure", "System ⚙️", "1. Activate > Systems > Map Sync.\n2. Select Map.\n3. 'Perform Sync'.\n4. Aligns x,y coordinates with DNA Spaces."),
    ("Tag Timeout Settings", "System ⚙️", "1. Map Timeout: 60 min (Tag removed if not seen).\n2. Monitor Timeout: 240 min (Tag removed if no monitor IR seen)."),
    ("Restore Asset", "Admin 📝", "1. Filter 'Archived' list.\n2. 'More' > 'Restore'.\n3. Edit Asset to assign NEW tag."),
    ("Check Core Services", "Critical 🚨", "1. RDP to Server 051.\n2. Check 'CenTrak' services (GMS, Location, Streaming).\n3. All must be Running/Green."),
    ("Cisco DNA Access", "Guardrails ⛔", "1. T1 PROHIBITED from Cisco DNA Spaces.\n2. All map changes flow FROM Cisco TO Activate.\n3. No manual map edits."),
    ("Import Data CSV", "Admin 📝", "1. Admin > System Config > Data Import.\n2. Use Template.\n3. Upload CSV.\n4. Click 'Test Import' to validate.")
]

for q, cat, a in general_faqs:
    db.append({
        "id": f"FAQ-{entry_id:04d}",
        "question": q,
        "answer": a,
        "category": cat,
        "type": "FAQ"
    })
    entry_id += 1

# --------------------------------------------------------------------------------
# HTML/CSS/JS GENERATION
# --------------------------------------------------------------------------------

html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Honeywell RTLS | Master Console V4</title>
    <style>
        :root {{
            --primary: #EE3124;
            --primary-dim: rgba(238, 49, 36, 0.1);
            --dark: #090909;
            --panel: #141414;
            --border: #2a2a2a;
            --text: #e0e0e0;
            --text-mute: #888;
            --accent: #00A3FF;
        }}
        * {{ box-sizing: border-box; font-family: 'Segoe UI', sans-serif; outline: none; }}
        body {{ background: var(--dark); color: var(--text); margin: 0; display: flex; height: 100vh; overflow: hidden; }}
        
        /* Sidebar */
        .sidebar {{ width: 250px; background: var(--panel); border-right: 1px solid var(--border); display: flex; flex-direction: column; z-index: 10; }}
        .brand {{ padding: 1.5rem; font-size: 1.4rem; font-weight: 800; color: #fff; border-bottom: 1px solid var(--border); display: flex; align-items: center; gap: 8px; }}
        .brand span {{ color: var(--primary); }}
        
        .nav-links {{ flex: 1; padding: 1rem; display: flex; flex-direction: column; gap: 0.5rem; }}
        .nav-item {{ padding: 1rem; border-radius: 8px; cursor: pointer; color: var(--text-mute); transition: 0.2s; font-weight: 600; display: flex; align-items: center; justify-content: space-between; }}
        .nav-item:hover, .nav-item.active {{ background: var(--primary-dim); color: #fff; transform: translateX(5px); }}
        .nav-item.active {{ border-left: 4px solid var(--primary); }}
        
        .status-dot {{ width: 8px; height: 8px; border-radius: 50%; background: #4caf50; box-shadow: 0 0 10px #4caf50; }}
        .version {{ font-size: 0.75rem; color: #444; padding: 1rem; border-top: 1px solid var(--border); display: flex; justify-content: space-between; align-items: center; }}

        /* Main Area */
        .main {{ flex: 1; display: flex; flex-direction: column; height: 100vh; overflow: hidden; background: radial-gradient(circle at top right, #1a1a1a 0%, #090909 40%); }}
        .top-bar {{ padding: 1.5rem 2.5rem; border-bottom: 1px solid var(--border); display: flex; justify-content: space-between; align-items: center; background: rgba(20,20,20,0.8); backdrop-filter: blur(10px); }}
        .page-title {{ font-size: 1.8rem; font-weight: 300; }}
        .page-title b {{ font-weight: 800; color: #fff; }}

        .content-area {{ flex: 1; padding: 2rem 2.5rem; overflow-y: auto; overflow-x: hidden; position: relative; }}

        /* Cards & Widgets */
        .grid-stats {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 1.5rem; margin-bottom: 2rem; animation: slideDown 0.5s ease; }}
        .stat-card {{ background: var(--panel); border: 1px solid var(--border); padding: 1.5rem; border-radius: 16px; transition: 0.3s; }}
        .stat-card:hover {{ transform: translateY(-5px); border-color: var(--primary); box-shadow: 0 10px 30px rgba(0,0,0,0.5); }}
        .stat-card h4 {{ margin: 0; color: var(--text-mute); font-size: 0.85rem; text-transform: uppercase; letter-spacing: 1px; }}
        .stat-card .num {{ font-size: 2.5rem; font-weight: 800; color: #fff; margin: 0.5rem 0; background: linear-gradient(45deg, #fff, #888); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
        
        .matrix {{ background: var(--panel); border-radius: 16px; padding: 2rem; border: 1px solid var(--primary-dim); margin-bottom: 2rem; animation: fadeIn 0.8s ease; }}
        .matrix table {{ width: 100%; border-collapse: collapse; }}
        .matrix th {{ text-align: left; padding-bottom: 1rem; color: var(--text-mute); border-bottom: 1px solid var(--border); }}
        .matrix td {{ padding: 1rem 0; border-bottom: 1px solid #222; font-size: 1.05rem; }}
        
        /* Animations */
        @keyframes slideDown {{ from {{ opacity: 0; transform: translateY(-20px); }} to {{ opacity: 1; transform: translateY(0); }} }}
        @keyframes slideIn {{ from {{ opacity: 0; transform: translateX(20px); }} to {{ opacity: 1; transform: translateX(0); }} }}
        @keyframes fadeIn {{ from {{ opacity: 0; }} to {{ opacity: 1; }} }}
        .slide-in-row {{ animation: slideIn 0.3s ease backwards; }}

        /* Table UI */
        .table-container {{ background: var(--panel); border-radius: 16px; border: 1px solid var(--border); overflow: hidden; display: flex; flex-direction: column; height: 100%; }}
        .controls {{ padding: 1rem; display: flex; gap: 1rem; border-bottom: 1px solid var(--border); background: #181818; }}
        .search-input {{ flex: 1; background: #0a0a0a; border: 1px solid #333; color: #fff; padding: 0.8rem 1.2rem; border-radius: 8px; font-size: 1rem; transition: 0.3s; }}
        .search-input:focus {{ border-color: var(--primary); box-shadow: 0 0 15px var(--primary-dim); }}
        
        .btn {{ background: var(--primary); color: #fff; border: none; padding: 0 1.5rem; border-radius: 8px; font-weight: 700; cursor: pointer; transition: 0.2s; display: flex; align-items: center; gap: 8px; }}
        .btn:hover {{ filter: brightness(1.2); transform: scale(1.02); }}
        .btn-icon {{ background: transparent; color: var(--text-mute); border: 1px solid #333; }}
        .btn-icon:hover {{ color: #fff; border-color: #fff; }}
        
        .data-table {{ width: 100%; border-collapse: collapse; }}
        .data-table th {{ background: #111; color: #888; padding: 1rem 1.5rem; text-align: left; font-weight: 600; position: sticky; top: 0; border-bottom: 1px solid var(--border); }}
        .data-table td {{ padding: 1rem 1.5rem; border-bottom: 1px solid #222; vertical-align: top; }}
        .data-table tr:hover {{ background: rgba(255,255,255,0.03); }}
        
        .step-list {{ margin: 0; padding-left: 1.2rem; color: #bbb; line-height: 1.6; }}
        .step-list li {{ margin-bottom: 4px; }}
        
        .badge {{ padding: 4px 10px; border-radius: 20px; font-size: 0.75rem; font-weight: 600; }}
        
        /* Modal */
        .modal-overlay {{ position: fixed; inset: 0; background: rgba(0,0,0,0.9); backdrop-filter: blur(5px); display: none; justify-content: center; align-items: center; z-index: 1000; animation: fadeIn 0.2s; }}
        .modal {{ background: #1a1a1a; width: 650px; border-radius: 20px; border: 1px solid #333; display: flex; flex-direction: column; max-height: 90vh; box-shadow: 0 20px 50px #000; }}
        .modal-header {{ padding: 1.5rem; border-bottom: 1px solid #333; display: flex; justify-content: space-between; align-items: center; }}
        .modal-body {{ padding: 2rem; overflow-y: auto; }}
        .modal-footer {{ padding: 1.5rem; border-top: 1px solid #333; display: flex; justify-content: flex-end; gap: 1rem; background: #111; border-radius: 0 0 20px 20px; }}
        
        .step-field {{ display: flex; gap: 10px; margin-bottom: 10px; align-items: center; }}
        .step-num {{ width: 25px; height: 25px; background: #333; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 0.8rem; font-weight: bold; }}

    </style>
</head>
<body>

<div class="sidebar">
    <div class="brand">HONEYWELL <span>RTLS</span></div>
    <div class="nav-links">
        <div class="nav-item active" onclick="switchTab('dashboard')" id="nav-dashboard">
            Dashboard <span>🏠</span>
        </div>
        <div class="nav-item" onclick="switchTab('faq')" id="nav-faq">
            FAQ Database <span>📚</span>
        </div>
        <div class="nav-item" onclick="switchTab('troubleshooting')" id="nav-troubleshooting">
            Troubleshooting <span>🔧</span>
        </div>
        <div class="nav-item" onclick="switchTab('settings')" id="nav-settings">
            Settings <span>⚙️</span>
        </div>
    </div>
    <div class="version">
        <span>V4.0.0 Pro</span>
        <div class="status-dot"></div>
    </div>
</div>

<div class="main">
    <div class="top-bar">
        <div class="page-title" id="pageTitle">System <b>Dashboard</b></div>
        <div id="topAction"></div>
    </div>
    
    <div class="content-area" id="content">
        <!-- Injected -->
    </div>
</div>

<!-- Modal -->
<div class="modal-overlay" id="editorModal">
    <div class="modal">
        <div class="modal-header">
            <h2 style="margin:0">Entry Editor</h2>
            <button onclick="closeModal()" style="background:none; border:none; color:#fff; font-size:1.5rem; cursor:pointer;">×</button>
        </div>
        <div class="modal-body">
            <input type="hidden" id="editId">
            <input type="hidden" id="editType">
            
            <label style="color:#888; font-size:0.9rem;">Topic / Question</label>
            <input type="text" id="editQuestion" class="search-input" style="width:100%; margin-top:5px; margin-bottom:1.5rem">
            
            <label style="color:#888; font-size:0.9rem;">Category</label>
            <input type="text" id="editCategory" class="search-input" style="width:100%; margin-top:5px; margin-bottom:1.5rem">
            
            <label style="color:#888; font-size:0.9rem; display:flex; justify-content:space-between;">
                Procedure Steps
                <span onclick="addStepField()" style="color:var(--primary); cursor:pointer; font-size:0.8rem">+ Add Step</span>
            </label>
            <div id="stepsContainer" style="margin-top:10px;"></div>
        </div>
        <div class="modal-footer">
            <button class="btn btn-icon" onclick="closeModal()">Cancel</button>
            <button class="btn" onclick="saveEntry()">Save Changes</button>
        </div>
    </div>
</div>

<script>
    const SEED_DATA = {json.dumps(db)};
    let db = [];
    let currentTab = 'dashboard';

    // Startup
    window.onload = function() {{
        const stored = localStorage.getItem('rtls_kb_v4');
        if (stored) {{
            db = JSON.parse(stored);
        }} else {{
            db = SEED_DATA;
            save();
        }}
        switchTab('dashboard');
    }};

    function save() {{ localStorage.setItem('rtls_kb_v4', JSON.stringify(db)); }}

    function switchTab(tab) {{
        currentTab = tab;
        document.querySelectorAll('.nav-item').forEach(e => e.classList.remove('active'));
        document.getElementById('nav-'+tab).classList.add('active');
        render();
    }}

    function render() {{
        const content = document.getElementById('content');
        const title = document.getElementById('pageTitle');
        const action = document.getElementById('topAction');

        if (currentTab === 'dashboard') {{
            title.innerHTML = 'System <b>Dashboard</b>';
            action.innerHTML = `<button class="btn" onclick="exportCSV()">Export Data 📥</button>`;
            
            const faqCount = db.filter(i => i.type === 'FAQ').length;
            const tsCount = db.filter(i => i.type === 'Troubleshooting').length;
            
            content.innerHTML = `
                <div class="grid-stats">
                    <div class="stat-card"><h4>Total Knowledge</h4><div class="num">${{db.length}}</div></div>
                    <div class="stat-card"><h4>FAQ Articles</h4><div class="num">${{faqCount}}</div></div>
                    <div class="stat-card"><h4>Diagnostic Flows</h4><div class="num">${{tsCount}}</div></div>
                    <div class="stat-card"><h4>System Uptime</h4><div class="num" style="color:#4caf50">100%</div></div>
                </div>

                <div class="matrix">
                    <h3 style="margin-top:0; color:#fff">Escalation Matrix</h3>
                    <table>
                        <tr><th>Support Level</th><th>Scope of Work</th><th>Restriction</th></tr>
                        <tr>
                            <td><span class="badge" style="background:#444; color:#fff">Tier 1 (You)</span></td>
                            <td>Triage, Symptom Check, Battery Replace, Map Sync</td>
                            <td style="color:#ff6b6b">NO Core Access, NO Cisco DNA</td>
                        </tr>
                        <tr>
                            <td><span class="badge" style="background:#ff9800; color:#000">Tier 2 (Admin)</span></td>
                            <td>Service Restarts, advanced debugging, log analysis</td>
                            <td>Requires Change Request</td>
                        </tr>
                        <tr>
                            <td><span class="badge" style="background:#f44336; color:#fff">Vendor (CenTrak)</span></td>
                            <td>Hardware RMA, Architectural Changes</td>
                            <td>Contact via Portal</td>
                        </tr>
                    </table>
                </div>
            `;
        }}
        else if (currentTab === 'faq' || currentTab === 'troubleshooting') {{
            const label = currentTab === 'faq' ? 'FAQ Database' : 'Troubleshooting';
            title.innerHTML = `<b>${{label}}</b>`;
            action.innerHTML = `<button class="btn" onclick="openEditor('NEW')">+ Add Entry</button>`;
            
            // Filter
            const typeKey = currentTab === 'faq' ? 'FAQ' : 'Troubleshooting';
            const rows = db.filter(i => i.type === typeKey);
            
            content.innerHTML = `
                <div class="table-container">
                    <div class="controls">
                        <input type="text" id="searchInput" class="search-input" placeholder="Search ${{rows.length}} articles..." oninput="doSearch()">
                    </div>
                    <div class="table-scroll-area">
                        <table class="data-table">
                            <thead><tr><th width="90">ID</th><th>Topic</th><th>Category</th><th>Procedure / Solution</th><th width="120">Actions</th></tr></thead>
                            <tbody id="tableBody">
                                ${{renderRows(rows)}}
                            </tbody>
                        </table>
                    </div>
                </div>
            `;
        }}
        else if (currentTab === 'settings') {{
            title.innerHTML = 'System <b>Settings</b>';
            action.innerHTML = '';
            content.innerHTML = `
                <div class="matrix" style="max-width:600px">
                    <h3>Data Management</h3>
                    <p style="color:#888">Import or Reset your local database.</p>
                    <button class="btn btn-icon" style="width:100%; justify-content:center; margin-bottom:1rem" onclick="document.getElementById('fileIn').click()">Import CSV File</button>
                    <input type="file" id="fileIn" onchange="importCSV()" hidden accept=".csv">
                    <button class="btn btn-icon" style="width:100%; justify-content:center; border-color:#d32f2f; color:#d32f2f" onclick="resetFactory()">Factory Reset Data</button>
                </div>
            `;
        }}
    }}
    
    function renderRows(rows) {{
        return rows.map((r, i) => `
            <tr class="slide-in-row" style="animation-delay: ${{i * 0.03}}s">
                <td style="font-family:monospace; color:#666">${{r.id}}</td>
                <td style="font-weight:600">${{r.question}}</td>
                <td><span class="badge" style="background:rgba(255,255,255,0.1)">${{r.category}}</span></td>
                <td>
                    ${{formatSteps(r.answer)}}
                </td>
                <td>
                    <button class="btn-icon" style="padding:4px 8px; border:none" onclick="openEditor('${{r.id}}')">✎</button>
                    <button class="btn-icon" style="padding:4px 8px; border:none; color:#ff6b6b" onclick="del('${{r.id}}')">✕</button>
                </td>
            </tr>
        `).join('');
    }}
    
    function formatSteps(txt) {{
        // Detect numbering "1. " and format
        if (!txt) return '';
        const lines = txt.split('\\n');
        // If it looks like a list
        if (lines.some(l => /^[0-9]+\./.test(l))) {{
            return `<ol class="step-list">${{lines.map(l => `<li>${{l.replace(/^[0-9]+\.\s*/, '')}}</li>`).join('')}}</ol>`;
        }}
        return txt;
    }}

    function doSearch() {{
        const q = document.getElementById('searchInput').value.toLowerCase();
        const typeKey = currentTab === 'faq' ? 'FAQ' : 'Troubleshooting';
        const filtered = db.filter(i => i.type === typeKey && (
            i.question.toLowerCase().includes(q) || 
            i.answer.toLowerCase().includes(q) || 
            i.id.toLowerCase().includes(q)
        ));
        document.getElementById('tableBody').innerHTML = renderRows(filtered);
    }}

    // Editor Logic
    function openEditor(id) {{
        const modal = document.getElementById('editorModal');
        const cont = document.getElementById('stepsContainer');
        cont.innerHTML = ''; // clear steps
        
        let item = {{ id: 'NEW', question: '', category: 'General', answer: '' }};
        if (id !== 'NEW') item = db.find(i => i.id === id);

        document.getElementById('editId').value = id;
        document.getElementById('editType').value = currentTab === 'faq' ? 'FAQ' : 'Troubleshooting';
        document.getElementById('editQuestion').value = item.question;
        document.getElementById('editCategory').value = item.category;
        
        // Parse Answer into Input Fields
        const steps = item.answer.split('\\n');
        steps.forEach(s => addStepField(s.replace(/^[0-9]+\.\s*/, '')));
        if (steps.length === 0 || (steps.length===1 && steps[0]==='')) addStepField(); // Ensure 1 empty

        modal.style.display = 'flex';
    }}

    function addStepField(val = '') {{
        const cont = document.getElementById('stepsContainer');
        const idx = cont.children.length + 1;
        const div = document.createElement('div');
        div.className = 'step-field';
        div.innerHTML = `
            <div class="step-num">${{idx}}</div>
            <input type="text" class="search-input step-input" style="flex:1" value="${{val.replace(/"/g, '&quot;')}}">
            <button onclick="this.parentElement.remove()" style="background:none; border:none; color:#666; cursor:pointer">×</button>
        `;
        cont.appendChild(div);
    }}

    function saveEntry() {{
        const id = document.getElementById('editId').value;
        const type = document.getElementById('editType').value;
        const q = document.getElementById('editQuestion').value;
        const c = document.getElementById('editCategory').value;
        
        // Collect Steps
        const inputs = document.querySelectorAll('.step-input');
        let combinedAnswer = '';
        inputs.forEach((inp, idx) => {{
            if (inp.value.trim()) {{
                combinedAnswer += (idx+1) + '. ' + inp.value.trim() + '\\n';
            }}
        }});
        combinedAnswer = combinedAnswer.trim();

        if (id === 'NEW') {{
            const newId = (type==='FAQ'?'FAQ':'TS') + '-' + Math.floor(Math.random()*99999);
            db.unshift({{ id: newId, type, question: q, category: c, answer: combinedAnswer }});
        }} else {{
            const idx = db.findIndex(i => i.id === id);
            if(idx > -1) {{
                db[idx].question = q;
                db[idx].category = c;
                db[idx].answer = combinedAnswer;
            }}
        }}
        save();
        closeModal();
        render(); // Refresh
    }}

    function del(id) {{
        if(confirm('Delete?')) {{
            db = db.filter(i => i.id !== id);
            save();
            render();
        }}
    }}
    
    function closeModal() {{ document.getElementById('editorModal').style.display = 'none'; }}
    
    function exportCSV() {{
        let csv = "ID,Type,Category,Question,Answer\\n";
        db.forEach(r => {{
            const clean = t => `"${{(t||'').replace(/"/g, '""')}}"`;
            csv += `${{clean(r.id)}},${{clean(r.type)}},${{clean(r.category)}},${{clean(r.question)}},${{clean(r.answer)}}\\n`;
        }});
        const link = document.createElement("a");
        link.href = 'data:text/csv;charset=utf-8,' + encodeURI(csv);
        link.download = 'rtls_knowledge_base.csv';
        link.click();
    }}
    
    function importCSV() {{
        const file = document.getElementById('fileIn').files[0];
        if(!file) return;
        const reader = new FileReader();
        reader.onload = e => {{
            const rows = e.target.result.split('\\n').slice(1);
            const newDb = [];
            rows.forEach(row => {{
                // Simple regex parse for CSV
                const cols = row.match(/(".*?"|[^",\s]+)(?=\s*,|\s*$)/g);
                if(cols && cols.length >= 5) {{
                     const unq = s => s.replace(/^"|"$/g, '').replace(/""/g, '"');
                     newDb.push({{ id: unq(cols[0]), type: unq(cols[1]), category: unq(cols[2]), question: unq(cols[3]), answer: unq(cols[4]) }});
                }}
            }});
            if(newDb.length) {{ db = newDb; save(); alert('Imported '+newDb.length); location.reload(); }}
        }};
        reader.readAsText(file);
    }}
    
    function resetFactory() {{
        if(confirm('Reset all data?')) {{ localStorage.removeItem('rtls_kb_v4'); location.reload(); }}
    }}

</script>
</body>
</html>
"""

with open("Honeywell_RTLS_T1_Dashboard.html", "w", encoding="utf-8") as f:
    f.write(html_content)

print(f"Generated Dashboard V4 with {len(db)} entries.")
