#!/usr/bin/env python3
"""
Scout Summary Report Generator - FINAL VERSION
Reads CSV data and populates Scout_corfo_sp.html template completely
All data replaced from CSV - 100% working version
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
    if not os_name:
        return 'Unknown'
    os_lower = os_name.lower()
    if 'windows' in os_lower:
        return 'Windows'
    elif any(x in os_lower for x in ['ubuntu', 'linux', 'centos', 'debian', 'oracle', 'rhel']):
        return 'Linux/Unix'
    return 'Unknown'

def extract_os_version(os_name):
    if not os_name:
        return 'Unknown'
    os_lower = os_name.lower()
    
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
    if not text:
        return ''
    return (str(text)
        .replace('&', '&amp;')
        .replace('<', '&lt;')
        .replace('>', '&gt;')
        .replace('"', '&quot;')
        .replace("'", '&#39;'))

def parse_size(size_str):
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
    if rate >= 95:
        return 'ok'
    elif rate >= 85:
        return 'mid'
    else:
        return 'bad'

def encode_image(path):
    try:
        with open(path, 'rb') as f:
            return base64.b64encode(f.read()).decode('utf-8')
    except:
        return None

# ============================================================================
# MAIN
# ============================================================================

def main():
    if len(sys.argv) < 4:
        print("Scout Report Generator")
        print("Usage: python3 scout_report_final.py <csv> <template> <output> [es] [logo1] [logo2]")
        sys.exit(1)
    
    csv_file = sys.argv[1]
    template_file = sys.argv[2]
    output_file = sys.argv[3]
    lang = 'es' if (len(sys.argv) > 4 and sys.argv[4] == 'es') else 'en'
    logo1 = sys.argv[5] if len(sys.argv) > 5 else None
    logo2 = sys.argv[6] if len(sys.argv) > 6 else None
    
    if not os.path.exists(csv_file) or not os.path.exists(template_file):
        print("❌ Files not found")
        sys.exit(1)
    
    print(f"📥 Reading CSV: {csv_file}")
    print(f"📋 Template: {template_file}")
    
    # Load files
    with open(template_file, 'r', encoding='utf-8') as f:
        html = f.read()
    
    vms = []
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        vms = list(reader)
    
    print(f"📊 Processing {len(vms)} VMs...")
    
    # Process data
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
        
        if is_success:
            success += 1
        else:
            failure += 1
        
        if min_d and (min_date is None or min_d < min_date):
            min_date = min_d
        if max_d and (max_date is None or max_d > max_date):
            max_date = max_d
        
        dc_stats[bucket]['total'] += 1
        dc_stats[bucket]['success' if is_success else 'failure'] += 1
        
        os_type_stats[os_type]['total'] += 1
        os_type_stats[os_type]['success' if is_success else 'failure'] += 1
        
        os_version_stats[os_version]['total'] += 1
        os_version_stats[os_version]['success' if is_success else 'failure'] += 1
        
        os_edition_stats[os_version][os_edition]['total'] += 1
        os_edition_stats[os_version][os_edition]['success' if is_success else 'failure'] += 1
        
        if not is_success:
            err_msg = vm.get('Comments', 'Unknown Error')
            error_counts[err_msg] += 1
        
        vm['is_success'] = is_success
        vm['os_type'] = os_type
        vm['os_version'] = os_version
        vm['os_edition'] = os_edition
    
    success_pct = (success / total * 100) if total > 0 else 0
    
    print(f"✅ Success: {success} ({success_pct:.1f}%)")
    print(f"❌ Failure: {failure}")
    
    # Generate tables
    print("🔨 Generating tables...")
    
    inv_rows = ''
    for vm in vms:
        good_files = int(vm.get('GOOD_FILES', '0') or '0')
        inv_rows += f'<tr class="clk {"fail" if not vm["is_success"] else ""}" tabindex="0" data-vc="{esc_html(vm.get("BUCKET", ""))}" data-vm="{esc_html(vm.get("Private_IP", ""))}" data-ostype="{vm["os_type"]}" data-osver="{vm["os_version"]}" data-st="{"fail" if not vm["is_success"] else "ok"}"><td class="L">{esc_html(vm.get("BUCKET", ""))}</td><td class="L"><b>{esc_html(vm.get("SERVER", ""))}</b></td><td class="L">{esc_html(vm.get("Private_IP", ""))}</td><td class="L">{esc_html(vm.get("OS_NAME", ""))}</td><td class="C">{vm.get("MIN_DATE", "")}</td><td class="C">{vm.get("MAX_DATE", "")}</td><td class="C">{vm.get("No.FILES", "")}</td><td class="C"><span class="pill {"ok" if good_files > 0 else "nil"}">{good_files}</span></td><td class="C" data-v="{"ok" if vm["is_success"] else "fail"}"><span class="st st-{"ok" if vm["is_success"] else "fail"}"></span></td></tr>\n'
    inv_rows += '<tr class="empty" id="inv-empty" hidden><td colspan="9" data-i18n="no_match">No VMs match the current filters</td></tr>\n'
    
    dc_rows = ''
    for dc in sorted(dc_stats.keys()):
        stats = dc_stats[dc]
        rate = (stats['success'] / stats['total'] * 100) if stats['total'] > 0 else 0
        dc_rows += f'<tr data-vc="{esc_html(dc)}"><td class="L"><b>{esc_html(dc)}</b></td><td class="C">{stats["total"]}</td><td class="C" data-v="{stats["success"]}"><span class="pill ok">{stats["success"]}</span></td><td class="C" data-v="{stats["failure"]}"><span class="pill {"bad" if stats["failure"] > 0 else "nil"}">{stats["failure"]}</span></td><td class="C" data-v="{rate:.1f}"><span class="rate {rate_class(rate)}"><b>{rate:.1f}%</b><span class="rbar"><i style="width:{rate:.1f}%"></i></span></span></td><td class="C"><button class="go" data-act="goinv">Ver →</button></td></tr>\n'
    
    type_rows = ''
    for os_type in sorted(os_type_stats.keys()):
        stats = os_type_stats[os_type]
        rate = (stats['success'] / stats['total'] * 100) if stats['total'] > 0 else 0
        type_rows += f'<tr data-ostype="{os_type}"><td class="L"><b>{os_type}</b></td><td class="C">{stats["total"]}</td><td class="C" data-v="{stats["success"]}"><span class="pill ok">{stats["success"]}</span></td><td class="C" data-v="{stats["failure"]}"><span class="pill {"bad" if stats["failure"] > 0 else "nil"}">{stats["failure"]}</span></td><td class="C" data-v="{rate:.1f}"><span class="rate {rate_class(rate)}"><b>{rate:.1f}%</b><span class="rbar"><i style="width:{rate:.1f}%"></i></span></span></td><td class="C"><button class="go" data-act="goinv">Ver →</button></td></tr>\n'
    
    ver_rows = ''
    group_idx = 0
    for os_version in sorted(os_version_stats.keys()):
        ver_stats = os_version_stats[os_version]
        ver_rate = (ver_stats['success'] / ver_stats['total'] * 100) if ver_stats['total'] > 0 else 0
        ver_rows += f'<tr class="grp" data-g="{group_idx}" data-osver="{os_version}"><td class="L"><button class="tg" data-act="toggle" aria-expanded="false" aria-label="toggle">▶</button><b>{os_version}</b></td><td class="L"></td><td class="C">{ver_stats["total"]}</td><td class="C"><span class="pill ok">{ver_stats["success"]}</span></td><td class="C"><span class="pill {"bad" if ver_stats["failure"] > 0 else "nil"}">{ver_stats["failure"]}</span></td><td class="C" data-v="{ver_rate:.1f}"><span class="rate {rate_class(ver_rate)}"><b>{ver_rate:.1f}%</b><span class="rbar"><i style="width:{ver_rate:.1f}%"></i></span></span></td><td class="C"><button class="go" data-act="goinv">Ver →</button></td></tr>\n'
        editions = os_edition_stats[os_version]
        for edition in sorted(editions.keys()):
            ed_stats = editions[edition]
            ed_rate = (ed_stats['success'] / ed_stats['total'] * 100) if ed_stats['total'] > 0 else 0
            ver_rows += f'<tr class="sub" data-p="{group_idx}" data-osver="{os_version}"><td class="L"></td><td class="L ed">{edition}</td><td class="C">{ed_stats["total"]}</td><td class="C"><span class="pill ok">{ed_stats["success"]}</span></td><td class="C"><span class="pill {"bad" if ed_stats["failure"] > 0 else "nil"}">{ed_stats["failure"]}</span></td><td class="C" data-v="{ed_rate:.1f}"><span class="rate {rate_class(ed_rate)}"><b>{ed_rate:.1f}%</b><span class="rbar"><i style="width:{ed_rate:.1f}%"></i></span></span></td><td class="C"></td></tr>\n'
        group_idx += 1
    
    coll_rows = ''
    for vm in vms:
        if not vm['is_success']:
            continue
        good_files = int(vm.get('GOOD_FILES', '0') or '0')
        size_bytes = parse_size(vm.get('Total_SIZE', '0'))
        coll_rows += f'<tr class="clk" tabindex="0" data-vc="{esc_html(vm.get("BUCKET", ""))}" data-vm="{esc_html(vm.get("Private_IP", ""))}"><td class="L">{esc_html(vm.get("BUCKET", ""))}</td><td class="L"><b>{esc_html(vm.get("SERVER", ""))}</b></td><td class="L">{esc_html(vm.get("Private_IP", ""))}</td><td class="L">{esc_html(vm.get("OS_NAME", ""))}</td><td class="C"><span class="pill ok">{good_files}</span></td><td class="C" data-v="{size_bytes}">{format_size(size_bytes)}</td></tr>\n'
    coll_rows += '<tr class="empty" hidden><td colspan="6" data-i18n="no_match">No VMs match the current filters</td></tr>\n'
    
    fail_rows = ''
    for vm in vms:
        if vm['is_success']:
            continue
        fail_rows += f'<tr class="clk fail" tabindex="0" data-vc="{esc_html(vm.get("BUCKET", ""))}" data-vm="{esc_html(vm.get("Private_IP", ""))}" data-err="{esc_html(vm.get("Comments", "Unknown"))}"><td class="L">{esc_html(vm.get("BUCKET", ""))}</td><td class="L"><b>{esc_html(vm.get("SERVER", ""))}</b></td><td class="L">{esc_html(vm.get("Private_IP", ""))}</td><td class="L">{esc_html(vm.get("OS_NAME", ""))}</td><td class="C"><span class="pill nil">0</span></td><td class="L wrap-msg">{esc_html(vm.get("Comments", "Unknown Error"))}</td></tr>\n'
    fail_rows += '<tr class="empty" hidden><td colspan="6" data-i18n="no_match">No VMs match the current filters</td></tr>\n'
    
    # Replace tables
    def replace_tbody(html, table_id, new_rows):
        import re
        pattern = rf'(<table\b[^>]*\bid="{re.escape(table_id)}"[^>]*>.*?<tbody>).*?(</tbody>)'
        return re.sub(
            pattern,
            lambda match: f'{match.group(1)}\n{new_rows}{match.group(2)}',
            html,
            count=1,
            flags=re.DOTALL,
        )
    
    html = replace_tbody(html, 'tbl-inv', inv_rows)
    html = replace_tbody(html, 'tbl-dc', dc_rows)
    html = replace_tbody(html, 'tbl-type', type_rows)
    html = replace_tbody(html, 'tbl-ver', ver_rows)
    html = replace_tbody(html, 'tbl-ok', coll_rows)
    html = replace_tbody(html, 'tbl-fail', fail_rows)
    
    # Update JavaScript data
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
    
    import re
    html = re.sub(r'const appData = \{.*?\};', f'const appData = {json.dumps(app_data)};', html, flags=re.DOTALL)
    html = re.sub(r'const errorLabels = \[.*?\];', f'const errorLabels = {json.dumps(error_labels)};', html, flags=re.DOTALL)
    html = re.sub(r'const errorCounts = \[.*?\];', f'const errorCounts = {json.dumps(error_counts_list)};', html, flags=re.DOTALL)
    html = re.sub(r'const META = \{.*?\};', f'const META = {json.dumps(meta)};', html, flags=re.DOTALL)
    
    # Update nav counts
    nav_count_pattern = r'<span class="nav-count">\d+</span>'
    nav_count_matches = list(re.finditer(nav_count_pattern, html))
    
    if len(nav_count_matches) >= 5:
        replacements = [
            (nav_count_matches[0], str(total)),
            (nav_count_matches[1], str(len(dc_stats))),
            (nav_count_matches[2], str(len(os_version_stats))),
            (nav_count_matches[3], str(success)),
            (nav_count_matches[4], str(failure))
        ]
        for match, new_value in reversed(replacements):
            html = html[:match.start()] + f'<span class="nav-count">{new_value}</span>' + html[match.end():]
    
    # Logos
    if logo1 and os.path.exists(logo1):
        b64 = encode_image(logo1)
        if b64:
            hdr_logos = f'<div class="hdr-logos"><img src="data:image/png;base64,{b64}" alt="Logo">'
            if logo2 and os.path.exists(logo2):
                b64_2 = encode_image(logo2)
                if b64_2:
                    hdr_logos += f'<img src="data:image/png;base64,{b64_2}" alt="Logo 2">'
            hdr_logos += '</div>'
            start_idx = html.find('<div class="hdr-logos">')
            if start_idx != -1:
                end_idx = html.find('</div>', start_idx) + 6
                html = html[:start_idx] + hdr_logos + html[end_idx:]
    
    # Language
    html = re.sub(r'<html lang="[a-z]{2}">', f'<html lang="{lang}">', html)
    
    # Write output
    print("✍️  Writing output...")
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print()
    print("=" * 70)
    print("✅ REPORT GENERATED SUCCESSFULLY!")
    print("=" * 70)
    print()
    print(f"📁 Output: {output_file}")
    print(f"📊 Data:")
    print(f"   Total: {total} VMs")
    print(f"   Success: {success} ({success_pct:.1f}%)")
    print(f"   Failure: {failure}")
    print()

if __name__ == '__main__':
    main()
