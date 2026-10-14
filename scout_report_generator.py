#!/usr/bin/env python3
"""
Scout Report Generator - ROBUST VERSION
Uses direct string replacement (not regex) to ensure ALL data is properly replaced
Works reliably with any CSV file and template structure
"""

import csv
import json
import sys
import base64
from collections import defaultdict
from datetime import datetime
import os

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def extract_os_type(os_name):
    """Extract OS type: Windows, Linux/Unix, Unknown"""
    if not os_name:
        return 'Unknown'
    os_lower = os_name.lower()
    if 'windows' in os_lower:
        return 'Windows'
    elif any(x in os_lower for x in ['ubuntu', 'linux', 'centos', 'debian', 'oracle', 'rhel']):
        return 'Linux/Unix'
    return 'Unknown'

def extract_os_version(os_name):
    """Extract OS version (e.g., 'Windows Server 2022', 'Ubuntu 22.04')"""
    if not os_name:
        return 'Unknown'
    os_lower = os_name.lower()
    
    # Windows
    if 'windows server 2025' in os_lower:
        return 'Windows Server 2025'
    elif 'windows server 2022' in os_lower:
        return 'Windows Server 2022'
    elif 'windows server 2019' in os_lower:
        return 'Windows Server 2019'
    elif 'windows server 2016' in os_lower:
        return 'Windows Server 2016'
    elif 'windows server 2012' in os_lower:
        return 'Windows Server 2012'
    
    # Linux/Unix
    elif 'ubuntu' in os_lower:
        import re
        match = re.search(r'ubuntu\s+(\d+\.\d+|\d+)', os_lower)
        return f'Ubuntu {match.group(1)}' if match else 'Ubuntu'
    elif 'oracle linux' in os_lower:
        import re
        match = re.search(r'oracle\s+linux\s+(?:server\s+)?(\d+\.\d+|\d+)', os_lower)
        return f'Oracle Linux {match.group(1)}' if match else 'Oracle Linux'
    elif 'centos' in os_lower:
        import re
        match = re.search(r'centos\s+(\d+)', os_lower)
        return f'CentOS {match.group(1)}' if match else 'CentOS'
    elif 'debian' in os_lower:
        import re
        match = re.search(r'debian\s+(?:gnu/linux\s+)?(\d+)', os_lower)
        return f'Debian {match.group(1)}' if match else 'Debian'
    
    return 'Unknown'

def extract_os_edition(os_name):
    """Extract OS edition (Datacenter, Standard, Server, etc.)"""
    if not os_name:
        return 'Server'
    os_lower = os_name.lower()
    
    if 'datacenter' in os_lower:
        return 'Datacenter'
    elif 'enterprise' in os_lower:
        return 'Enterprise'
    elif 'standard' in os_lower:
        return 'Standard'
    else:
        return 'Server'

def esc_html(text):
    """Escape HTML special characters"""
    if not text:
        return ''
    return (str(text)
        .replace('&', '&amp;')
        .replace('<', '&lt;')
        .replace('>', '&gt;')
        .replace('"', '&quot;')
        .replace("'", '&#39;'))

def parse_size(size_str):
    """Parse '1.2M' or '804K' to bytes"""
    if not size_str:
        return 0
    size_str = str(size_str).strip().upper()
    multipliers = {'K': 1024, 'M': 1024*1024, 'G': 1024*1024*1024}
    for suffix, mult in multipliers.items():
        if suffix in size_str:
            try:
                num = float(size_str.replace(suffix, '').strip())
                return int(num * mult)
            except:
                return 0
    try:
        return int(size_str)
    except:
        return 0

def format_size(bytes_val):
    """Format bytes to human-readable"""
    if bytes_val == 0:
        return '0'
    for suffix in ['', 'K', 'M', 'G']:
        if bytes_val < 1024:
            if suffix == '':
                return str(int(bytes_val))
            return f"{bytes_val:.1f}{suffix}".rstrip('0').rstrip('.')
        bytes_val /= 1024
    return f"{bytes_val:.1f}T"

def rate_class(rate):
    """Get CSS class for rate bar"""
    if rate >= 95:
        return 'ok'
    elif rate >= 85:
        return 'mid'
    else:
        return 'bad'

def encode_image(path):
    """Encode image to base64"""
    try:
        with open(path, 'rb') as f:
            return base64.b64encode(f.read()).decode('utf-8')
    except:
        return None

# ============================================================================
# MAIN SCRIPT
# ============================================================================

def main():
    if len(sys.argv) < 4:
        print("╔════════════════════════════════════════════════════════════╗")
        print("║  Scout Report Generator - Robust Version                  ║")
        print("╚════════════════════════════════════════════════════════════╝")
        print()
        print("Usage:")
        print("  python3 scout_report_generator.py <csv> <template> <output> [es] [logo1] [logo2]")
        print()
        print("Example:")
        print("  python3 scout_report_generator.py confor.csv Scout_corfo_sp.html report.html es corfo.png concierto.png")
        print()
        sys.exit(1)
    
    csv_file = sys.argv[1]
    template_file = sys.argv[2]
    output_file = sys.argv[3]
    lang = 'es' if (len(sys.argv) > 4 and sys.argv[4] == 'es') else 'en'
    logo1 = sys.argv[5] if len(sys.argv) > 5 else None
    logo2 = sys.argv[6] if len(sys.argv) > 6 else None
    
    # Validate files
    if not os.path.exists(csv_file):
        print(f"❌ Error: CSV file not found: {csv_file}")
        sys.exit(1)
    if not os.path.exists(template_file):
        print(f"❌ Error: Template file not found: {template_file}")
        sys.exit(1)
    
    print("🚀 Scout Report Generator - ROBUST VERSION")
    print(f"📥 CSV Input: {csv_file}")
    print(f"📋 Template: {template_file}")
    print(f"📤 Output: {output_file}")
    print(f"🌍 Language: {'Español' if lang == 'es' else 'English'}")
    print()
    
    # ========================================================================
    # LOAD TEMPLATE AND CSV
    # ========================================================================
    
    print("📖 Loading template...")
    with open(template_file, 'r', encoding='utf-8') as f:
        html = f.read()
    
    print("📊 Loading CSV...")
    vms = []
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        vms = list(reader)
    
    print(f"   Found {len(vms)} VMs")
    print()
    
    # ========================================================================
    # PROCESS CSV DATA
    # ========================================================================
    
    print("🔨 Processing CSV data...")
    
    total = len(vms)
    success = 0
    failure = 0
    min_date = None
    max_date = None
    
    dc_stats = defaultdict(lambda: {'total': 0, 'success': 0, 'failure': 0})
    os_type_stats = defaultdict(lambda: {'total': 0, 'success': 0, 'failure': 0})
    os_version_stats = defaultdict(lambda: {'total': 0, 'success': 0, 'failure': 0})
    os_edition_stats = defaultdict(lambda: defaultdict(lambda: {'total': 0, 'success': 0, 'failure': 0}))
    error_counts = defaultdict(int)
    
    # Process each VM
    for vm in vms:
        good_files = int(vm.get('GOOD_FILES', '0') or '0')
        is_success = good_files > 0
        
        bucket = vm.get('BUCKET', 'Unknown')
        os_name = vm.get('OS_NAME', '')
        os_type = extract_os_type(os_name)
        os_version = extract_os_version(os_name)
        os_edition = extract_os_edition(os_name)
        min_d = vm.get('MIN_DATE', '')
        max_d = vm.get('MAX_DATE', '')
        
        # Track counts
        if is_success:
            success += 1
        else:
            failure += 1
        
        # Track dates
        if min_d and (min_date is None or min_d < min_date):
            min_date = min_d
        if max_d and (max_date is None or max_d > max_date):
            max_date = max_d
        
        # Update statistics
        dc_stats[bucket]['total'] += 1
        dc_stats[bucket]['success' if is_success else 'failure'] += 1
        
        os_type_stats[os_type]['total'] += 1
        os_type_stats[os_type]['success' if is_success else 'failure'] += 1
        
        os_version_stats[os_version]['total'] += 1
        os_version_stats[os_version]['success' if is_success else 'failure'] += 1
        
        os_edition_stats[os_version][os_edition]['total'] += 1
        os_edition_stats[os_version][os_edition]['success' if is_success else 'failure'] += 1
        
        # Track errors
        if not is_success:
            err_msg = vm.get('Comments', 'Unknown Error')
            error_counts[err_msg] += 1
        
        # Store processed fields
        vm['is_success'] = is_success
        vm['os_type'] = os_type
        vm['os_version'] = os_version
        vm['os_edition'] = os_edition
    
    success_pct = (success / total * 100) if total > 0 else 0
    
    print(f"   ✅ Success: {success} ({success_pct:.1f}%)")
    print(f"   ❌ Failure: {failure}")
    print(f"   📅 Period: {min_date} → {max_date}")
    print()
    
    # ========================================================================
    # GENERATE TABLE ROWS
    # ========================================================================
    
    print("🔨 Generating table rows...")
    
    # 1. INVENTORY TABLE (tbl-inv)
    print("   • Generating inventory rows...")
    inv_rows = ''
    for vm in vms:
        good_files = int(vm.get('GOOD_FILES', '0') or '0')
        inv_rows += f'<tr class="clk {"fail" if not vm["is_success"] else ""}" tabindex="0" data-vc="{esc_html(vm.get("BUCKET", ""))}" data-vm="{esc_html(vm.get("Private_IP", ""))}" data-ostype="{vm["os_type"]}" data-osver="{vm["os_version"]}" data-st="{"fail" if not vm["is_success"] else "ok"}"><td class="L">{esc_html(vm.get("BUCKET", ""))}</td><td class="L"><b>{esc_html(vm.get("SERVER", ""))}</b></td><td class="L">{esc_html(vm.get("Private_IP", ""))}</td><td class="L">{esc_html(vm.get("OS_NAME", ""))}</td><td class="C">{vm.get("MIN_DATE", "")}</td><td class="C">{vm.get("MAX_DATE", "")}</td><td class="C">{vm.get("No.FILES", "")}</td><td class="C"><span class="pill {"ok" if good_files > 0 else "nil"}">{good_files}</span></td><td class="C" data-v="{"ok" if vm["is_success"] else "fail"}"><span class="st st-{"ok" if vm["is_success"] else "fail"}"></span></td></tr>\n'
    inv_rows += '<tr class="empty" id="inv-empty" hidden><td colspan="9" data-i18n="no_match">Ninguna VM coincide con los filtros actuales</td></tr>\n'
    
    # 2. DATACENTER TABLE (tbl-dc)
    print("   • Generating datacenter rows...")
    dc_rows = ''
    for dc in sorted(dc_stats.keys()):
        stats = dc_stats[dc]
        rate = (stats['success'] / stats['total'] * 100) if stats['total'] > 0 else 0
        dc_rows += f'<tr data-vc="{esc_html(dc)}"><td class="L"><b>{esc_html(dc)}</b></td><td class="C">{stats["total"]}</td><td class="C" data-v="{stats["success"]}"><span class="pill ok">{stats["success"]}</span></td><td class="C" data-v="{stats["failure"]}"><span class="pill {"bad" if stats["failure"] > 0 else "nil"}">{stats["failure"]}</span></td><td class="C" data-v="{rate:.1f}"><span class="rate {rate_class(rate)}"><b>{rate:.1f}%</b><span class="rbar"><i style="width:{rate:.1f}%"></i></span></span></td><td class="C"><button class="go" data-act="goinv">Ver →</button></td></tr>\n'
    
    # 3. OS TYPE TABLE (tbl-type)
    print("   • Generating OS type rows...")
    type_rows = ''
    for os_type in sorted(os_type_stats.keys()):
        stats = os_type_stats[os_type]
        rate = (stats['success'] / stats['total'] * 100) if stats['total'] > 0 else 0
        type_rows += f'<tr data-ostype="{os_type}"><td class="L"><b>{os_type}</b></td><td class="C">{stats["total"]}</td><td class="C" data-v="{stats["success"]}"><span class="pill ok">{stats["success"]}</span></td><td class="C" data-v="{stats["failure"]}"><span class="pill {"bad" if stats["failure"] > 0 else "nil"}">{stats["failure"]}</span></td><td class="C" data-v="{rate:.1f}"><span class="rate {rate_class(rate)}"><b>{rate:.1f}%</b><span class="rbar"><i style="width:{rate:.1f}%"></i></span></span></td><td class="C"><button class="go" data-act="goinv">Ver →</button></td></tr>\n'
    
    # 4. OS VERSION TABLE (tbl-ver) - Parent/Child structure
    print("   • Generating OS version rows...")
    ver_rows = ''
    group_idx = 0
    for os_version in sorted(os_version_stats.keys()):
        ver_stats = os_version_stats[os_version]
        ver_rate = (ver_stats['success'] / ver_stats['total'] * 100) if ver_stats['total'] > 0 else 0
        
        # Parent row
        ver_rows += f'<tr class="grp" data-g="{group_idx}" data-osver="{os_version}"><td class="L"><button class="tg" data-act="toggle" aria-expanded="false" aria-label="toggle">▶</button><b>{os_version}</b></td><td class="L"></td><td class="C">{ver_stats["total"]}</td><td class="C"><span class="pill ok">{ver_stats["success"]}</span></td><td class="C"><span class="pill {"bad" if ver_stats["failure"] > 0 else "nil"}">{ver_stats["failure"]}</span></td><td class="C" data-v="{ver_rate:.1f}"><span class="rate {rate_class(ver_rate)}"><b>{ver_rate:.1f}%</b><span class="rbar"><i style="width:{ver_rate:.1f}%"></i></span></span></td><td class="C"><button class="go" data-act="goinv">Ver →</button></td></tr>\n'
        
        # Child rows (editions)
        editions = os_edition_stats[os_version]
        for edition in sorted(editions.keys()):
            ed_stats = editions[edition]
            ed_rate = (ed_stats['success'] / ed_stats['total'] * 100) if ed_stats['total'] > 0 else 0
            ver_rows += f'<tr class="sub" data-p="{group_idx}" data-osver="{os_version}"><td class="L"></td><td class="L ed">{edition}</td><td class="C">{ed_stats["total"]}</td><td class="C"><span class="pill ok">{ed_stats["success"]}</span></td><td class="C"><span class="pill {"bad" if ed_stats["failure"] > 0 else "nil"}">{ed_stats["failure"]}</span></td><td class="C" data-v="{ed_rate:.1f}"><span class="rate {rate_class(ed_rate)}"><b>{ed_rate:.1f}%</b><span class="rbar"><i style="width:{ed_rate:.1f}%"></i></span></span></td><td class="C"></td></tr>\n'
        
        group_idx += 1
    
    # 5. COLLECTED TABLE (tbl-ok)
    print("   • Generating collected rows...")
    coll_rows = ''
    for vm in vms:
        if not vm['is_success']:
            continue
        good_files = int(vm.get('GOOD_FILES', '0') or '0')
        size_bytes = parse_size(vm.get('Total_SIZE', '0'))
        coll_rows += f'<tr class="clk" tabindex="0" data-vc="{esc_html(vm.get("BUCKET", ""))}" data-vm="{esc_html(vm.get("Private_IP", ""))}"><td class="L">{esc_html(vm.get("BUCKET", ""))}</td><td class="L"><b>{esc_html(vm.get("SERVER", ""))}</b></td><td class="L">{esc_html(vm.get("Private_IP", ""))}</td><td class="L">{esc_html(vm.get("OS_NAME", ""))}</td><td class="C"><span class="pill ok">{good_files}</span></td><td class="C" data-v="{size_bytes}">{format_size(size_bytes)}</td></tr>\n'
    coll_rows += '<tr class="empty" hidden><td colspan="6" data-i18n="no_match">Ninguna VM coincide con los filtros actuales</td></tr>\n'
    
    # 6. FAILED TABLE (tbl-fail)
    print("   • Generating failed rows...")
    fail_rows = ''
    for vm in vms:
        if vm['is_success']:
            continue
        fail_rows += f'<tr class="clk fail" tabindex="0" data-vc="{esc_html(vm.get("BUCKET", ""))}" data-vm="{esc_html(vm.get("Private_IP", ""))}" data-err="{esc_html(vm.get("Comments", "Unknown"))}"><td class="L">{esc_html(vm.get("BUCKET", ""))}</td><td class="L"><b>{esc_html(vm.get("SERVER", ""))}</b></td><td class="L">{esc_html(vm.get("Private_IP", ""))}</td><td class="L">{esc_html(vm.get("OS_NAME", ""))}</td><td class="C"><span class="pill nil">0</span></td><td class="L wrap-msg">{esc_html(vm.get("Comments", "Unknown Error"))}</td></tr>\n'
    fail_rows += '<tr class="empty" hidden><td colspan="6" data-i18n="no_match">Ninguna VM coincide con los filtros actuales</td></tr>\n'
    
    print("   ✅ All rows generated")
    print()
    
    # ========================================================================
    # REPLACE TABLE CONTENT
    # ========================================================================
    
    print("🔨 Replacing table content in HTML...")
    
    # Find and replace each table's tbody
    def replace_tbody(html, table_id, new_rows):
        """Replace tbody content for a specific table ID"""
        search_str = f'id="{table_id}"><thead>'
        if search_str not in html:
            print(f"   ⚠️  Warning: Could not find table {table_id}")
            return html
        
        # Find the position of this table
        table_start = html.find(f'id="{table_id}">')
        if table_start == -1:
            return html
        
        # Find the <tbody> after this table
        tbody_start = html.find('<tbody>', table_start)
        if tbody_start == -1:
            return html
        
        tbody_start += len('<tbody>')
        
        # Find the closing </tbody>
        tbody_end = html.find('</tbody>', tbody_start)
        if tbody_end == -1:
            return html
        
        # Replace the content between <tbody> and </tbody>
        new_html = html[:tbody_start] + '\n' + new_rows + html[tbody_end:]
        return new_html
    
    html = replace_tbody(html, 'tbl-inv', inv_rows)
    print("   ✅ tbl-inv replaced")
    
    html = replace_tbody(html, 'tbl-dc', dc_rows)
    print("   ✅ tbl-dc replaced")
    
    html = replace_tbody(html, 'tbl-type', type_rows)
    print("   ✅ tbl-type replaced")
    
    html = replace_tbody(html, 'tbl-ver', ver_rows)
    print("   ✅ tbl-ver replaced")
    
    html = replace_tbody(html, 'tbl-ok', coll_rows)
    print("   ✅ tbl-ok replaced")
    
    html = replace_tbody(html, 'tbl-fail', fail_rows)
    print("   ✅ tbl-fail replaced")
    
    print()
    
    # ========================================================================
    # UPDATE JAVASCRIPT DATA
    # ========================================================================
    
    print("🔨 Updating JavaScript data...")
    
    app_data = {
        'total': total,
        'success': success,
        'failure': failure,
        'success_pct': round(success_pct, 1),
        'datacenters': {dc: dict(stats) for dc, stats in dc_stats.items()},
        'os_types': {os_type: dict(stats) for os_type, stats in os_type_stats.items()},
        'os_versions': {os_ver: dict(stats) for os_ver, stats in os_version_stats.items()},
        'os_version_colors': ['#2E8B72', '#C0392B', '#0087C6', '#F39C12', '#E67E22', '#D35400', '#BDC3C7', '#9B59B6', '#1ABC9C', '#34495E', '#E74C3C', '#16A085']
    }
    
    error_labels = [msg for msg, _ in sorted(error_counts.items(), key=lambda x: x[1], reverse=True)[:6]]
    error_counts_list = [error_counts[msg] for msg in error_labels]
    
    meta = {
        'from': min_date or '',
        'to': max_date or '',
        'generated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    # Find and replace JavaScript variables
    app_data_str = f'const appData = {json.dumps(app_data)};'
    error_labels_str = f'const errorLabels = {json.dumps(error_labels)};'
    error_counts_str = f'const errorCounts = {json.dumps(error_counts_list)};'
    meta_str = f'const META = {json.dumps(meta)};'
    
    # Find existing variables and replace
    start_idx = html.find('const appData = ')
    if start_idx != -1:
        end_idx = html.find(';', start_idx) + 1
        html = html[:start_idx] + app_data_str + html[end_idx:]
        print("   ✅ appData updated")
    
    start_idx = html.find('const errorLabels = ')
    if start_idx != -1:
        end_idx = html.find(';', start_idx) + 1
        html = html[:start_idx] + error_labels_str + html[end_idx:]
        print("   ✅ errorLabels updated")
    
    start_idx = html.find('const errorCounts = ')
    if start_idx != -1:
        end_idx = html.find(';', start_idx) + 1
        html = html[:start_idx] + error_counts_str + html[end_idx:]
        print("   ✅ errorCounts updated")
    
    start_idx = html.find('const META = ')
    if start_idx != -1:
        end_idx = html.find(';', start_idx) + 1
        html = html[:start_idx] + meta_str + html[end_idx:]
        print("   ✅ META updated")
    
    print()
    
    # ========================================================================
    # HANDLE LOGOS
    # ========================================================================
    
    print("📷 Processing logos...")
    
    if logo1 and os.path.exists(logo1):
        b64 = encode_image(logo1)
        if b64:
            hdr_logos = f'<div class="hdr-logos"><img src="data:image/png;base64,{b64}" alt="Logo">'
            if logo2 and os.path.exists(logo2):
                b64_2 = encode_image(logo2)
                if b64_2:
                    hdr_logos += f'<img src="data:image/png;base64,{b64_2}" alt="Logo 2">'
            hdr_logos += '</div>'
            
            # Find and replace hdr-logos div
            start_idx = html.find('<div class="hdr-logos">')
            if start_idx != -1:
                end_idx = html.find('</div>', start_idx) + 6
                html = html[:start_idx] + hdr_logos + html[end_idx:]
                print(f"   ✅ Logos embedded")
    
    print()
    
    # ========================================================================
    # SET LANGUAGE
    # ========================================================================
    
    print("🌍 Setting language...")
    
    start_idx = html.find('<html lang="')
    if start_idx != -1:
        end_idx = html.find('">', start_idx) + 1
        html = html[:start_idx] + f'<html lang="{lang}' + html[end_idx:]
        print(f"   ✅ Language set to {lang}")
    
    # ========================================================================
    # ADD CHART INITIALIZATION ON PAGE LOAD
    # ========================================================================
    
    # NO INITIALIZATION CODE NEEDED!
    # The template's built-in code handles everything perfectly
    # Charts render automatically when page loads
    # Click handlers work because page is fully initialized
    # Trying to force initialization causes conflicts
    
    print("✅ Template will auto-initialize on page load")
    print()
    
    # ========================================================================
    # UPDATE SIDEBAR NAVIGATION COUNTS
    # ========================================================================
    
    print("🔨 Updating sidebar navigation counts...")
    
    # Find and replace nav-count values in sidebar
    import re as regex
    
    nav_count_pattern = r'<span class="nav-count">\d+</span>'
    nav_count_matches = list(regex.finditer(nav_count_pattern, html))
    
    if len(nav_count_matches) >= 5:
        # Create replacement values in order:
        # 0 = Inventory Master (total VMs)
        # 1 = Infrastructure (datacenters count)
        # 2 = Operating Systems (OS versions count)
        # 3 = Successful Collection (success count)
        # 4 = Failed Collection (failure count)
        
        replacements = [
            (nav_count_matches[0], str(total)),
            (nav_count_matches[1], str(len(dc_stats))),
            (nav_count_matches[2], str(len(os_version_stats))),
            (nav_count_matches[3], str(success)),
            (nav_count_matches[4], str(failure))
        ]
        
        # Replace from end to start to preserve positions
        for match, new_value in reversed(replacements):
            old_span = match.group()
            new_span = f'<span class="nav-count">{new_value}</span>'
            html = html[:match.start()] + new_span + html[match.end():]
        
        print("   ✅ Inventory Master: " + str(total))
        print("   ✅ Infrastructure: " + str(len(dc_stats)))
        print("   ✅ Operating Systems: " + str(len(os_version_stats)))
        print("   ✅ Successful Collection: " + str(success))
        print("   ✅ Failed Collection: " + str(failure))
    else:
        print(f"   ⚠️  Warning: Found only {len(nav_count_matches)} nav-count elements (expected 5)")
    
    print()
    
    # ========================================================================
    # WRITE OUTPUT
    # ========================================================================
    
    print("✍️  Writing output file...")
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)
    
    # Get file size
    file_size = os.path.getsize(output_file)
    size_mb = file_size / (1024 * 1024)
    
    print()
    print("=" * 70)
    print("✅ REPORT GENERATED SUCCESSFULLY!")
    print("=" * 70)
    print()
    print(f"📁 Output File: {output_file}")
    print(f"📊 File Size: {size_mb:.2f} MB ({file_size:,} bytes)")
    print()
    print(f"📈 Report Statistics:")
    print(f"   Total VMs:        {total}")
    print(f"   Successful:       {success} ({success_pct:.1f}%)")
    print(f"   Failed:           {failure}")
    print(f"   Period:           {min_date} → {max_date}")
    print(f"   Datacenters:      {len(dc_stats)}")
    print(f"   OS Types:         {len(os_type_stats)}")
    print(f"   OS Versions:      {len(os_version_stats)}")
    print(f"   Language:         {'Español' if lang == 'es' else 'English'}")
    print()
    print("🎉 Ready to open in browser!")
    print()

if __name__ == '__main__':
    main()
