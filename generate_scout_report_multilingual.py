#!/usr/bin/env python3
"""
Scout Summary Report Generator - Multilingual Support (English/Spanish)
With Logo Support & Auto Date Detection
Usage: python3 generate_scout_report.py <csv> <output> [language] [logo1.png] [logo2.png]
Languages: en (English), es (Spanish/Español)
"""

import csv
import json
import re
import sys
import base64
from collections import defaultdict
from datetime import datetime
import os

# Language translations
TRANSLATIONS = {
    'en': {
        'title': 'Scout Summary Report',
        'data_collection': 'Data Collection Status',
        'total_vms': 'Total VMs',
        'success_label': 'Success',
        'failure_label': 'Failure',
        'success_distribution': 'Success Distribution',
        'success_pct_by_dc': 'Success % by Datacenter',
        'key_insights': 'Key Insights',
        'collected': 'successfully collected data',
        'no_collection': 'have no collection',
        'infrastructure': 'Infrastructure Composition',
        'servers_make_up': 'What kind of servers make up the estate?',
        'dc_distribution': 'Datacenter Distribution (Success/Failure)',
        'dc_workloads': 'Datacenter Workloads',
        'server_distribution': 'Server Distribution by Datacenter',
        'datacenter': 'Datacenter',
        'os_landscape': 'Operating System Landscape',
        'os_type_dist': 'OS Type Distribution',
        'success_failure_os_type': 'Success/Failure by OS Type',
        'os_type_rate': 'OS Type Success Rate %',
        'os_type_breakdown': 'OS Type-wise Success/Failure Breakdown',
        'operating_system': 'Operating System',
        'os_version_edition': 'OS Version & Edition Details',
        'os_breakdown': 'OS Version-wise Breakdown (with Edition Details)',
        'os_version_report': 'OS Version Wise Report',
        'breakdown_os_versions': 'Detailed breakdown by specific OS versions',
        'os_version_dist': 'OS Version Distribution',
        'success_failure_os_version': 'Success/Failure by OS Version',
        'os_version_rate': 'OS Version Success Rate %',
        'inventory_master': 'Inventory Master',
        'search_vm_ip': 'Search VM / IP...',
        'export_csv': 'Export CSV',
        'vcenter': 'vCenter',
        'vm_name': 'VM Name',
        'ip_address': 'IP Address',
        'os_name': 'OS Name',
        'start_date': 'Start Date',
        'end_date': 'End Date',
        'total_files': 'Total Files',
        'good_files': 'Good Files',
        'status': 'Status',
        'collected_vms': 'Collected VMs',
        'total_size': 'Total Size',
        'uncollected_vms': 'Uncollected VMs',
        'error_distribution': 'Error Type Distribution',
        'error_message': 'Error Message',
        'print': 'Print',
        'report_sections': 'Report Sections',
        'print_btn': 'Print',
        'success': 'Success',
        'failure': 'Failure',
    },
    'es': {
        'title': 'Informe de Resumen de Scout',
        'data_collection': 'Estado de Recopilación de Datos',
        'total_vms': 'Total de VMs',
        'success_label': 'Éxito (GOOD_FILES > 0)',
        'failure_label': 'Fallo (GOOD_FILES = 0)',
        'success_distribution': 'Distribución de Éxito',
        'success_pct_by_dc': '% de Éxito por Centro de Datos',
        'key_insights': 'Información Clave',
        'collected': 'recopilaron datos exitosamente',
        'no_collection': 'no tienen recopilación',
        'infrastructure': 'Composición de la Infraestructura',
        'servers_make_up': '¿Qué tipo de servidores conforman la infraestructura?',
        'dc_distribution': 'Distribución de Centro de Datos (Éxito/Fallo)',
        'dc_workloads': 'Cargas de Trabajo del Centro de Datos',
        'server_distribution': 'Distribución de Servidores por Centro de Datos',
        'datacenter': 'Centro de Datos',
        'os_landscape': 'Panorama del Sistema Operativo',
        'os_type_dist': 'Distribución por Tipo de SO',
        'success_failure_os_type': 'Éxito/Fallo por Tipo de SO',
        'os_type_rate': '% de Éxito por Tipo de SO',
        'os_type_breakdown': 'Desglose de Éxito/Fallo por Tipo de SO',
        'operating_system': 'Sistema Operativo',
        'os_version_edition': 'Detalles de Versión y Edición del SO',
        'os_breakdown': 'Desglose por Versión del SO (con Detalles de Edición)',
        'os_version_report': 'Informe por Versión del SO',
        'breakdown_os_versions': 'Desglose detallado por versiones específicas del SO',
        'os_version_dist': 'Distribución por Versión del SO',
        'success_failure_os_version': 'Éxito/Fallo por Versión del SO',
        'os_version_rate': '% de Éxito por Versión del SO',
        'inventory_master': 'Maestro de Inventario',
        'search_vm_ip': 'Buscar VM / IP...',
        'export_csv': 'Exportar CSV',
        'vcenter': 'vCenter',
        'vm_name': 'Nombre de VM',
        'ip_address': 'Dirección IP',
        'os_name': 'Nombre del SO',
        'start_date': 'Fecha de Inicio',
        'end_date': 'Fecha de Fin',
        'total_files': 'Total de Archivos',
        'good_files': 'Archivos Buenos',
        'status': 'Estado',
        'collected_vms': 'VMs Recopiladas',
        'total_size': 'Tamaño Total',
        'uncollected_vms': 'VMs No Recopiladas',
        'error_distribution': 'Distribución de Tipos de Error',
        'error_message': 'Mensaje de Error',
        'print': 'Imprimir',
        'report_sections': 'Secciones del Informe',
        'print_btn': '🖨️ Imprimir',
        'success': 'Éxito',
        'failure': 'Fallo',
    }
}

def get_text(lang, key):
    """Get translated text"""
    if lang not in TRANSLATIONS:
        lang = 'en'
    return TRANSLATIONS[lang].get(key, TRANSLATIONS['en'].get(key, key))

def encode_image_to_base64(image_path):
    """Convert image file to base64 string"""
    try:
        with open(image_path, 'rb') as f:
            return base64.b64encode(f.read()).decode('utf-8')
    except Exception as e:
        print(f"⚠️  Warning: Could not load image {image_path}: {e}")
        return None

def clean_os_name(os_name):
    if not os_name:
        return 'Not Found'
    cleaned = re.sub(r'\s*\(\d+\.\d+\.\d+\.\d+\)', '', os_name)
    cleaned = re.sub(r'\s*\[\d+\.\d+\.\d+\.\d+\]', '', cleaned)
    cleaned = re.sub(r'KB\d+', '', cleaned)
    return cleaned.strip()

def extract_os_type(os_name):
    if not os_name:
        return 'Unknown'
    os_lower = os_name.lower()
    if 'windows' in os_lower:
        return 'Windows'
    elif any(x in os_lower for x in ['ubuntu', 'linux', 'centos', 'debian', 'oracle', 'rhel']):
        return 'Linux/Unix'
    else:
        return 'Unknown'

def extract_windows_edition(os_name):
    os_lower = os_name.lower()
    if 'datacenter' in os_lower:
        return 'Datacenter'
    elif 'enterprise' in os_lower:
        return 'Enterprise'
    else:
        return 'Standard'

def extract_os_version(os_name):
    if not os_name:
        return 'Unknown', 'Unknown'
    os_lower = os_name.lower()
    if 'windows server 2025' in os_lower or '2025' in os_lower:
        return 'Windows Server 2025', extract_windows_edition(os_name)
    elif 'windows server 2022' in os_lower or '2022' in os_lower:
        return 'Windows Server 2022', extract_windows_edition(os_name)
    elif 'windows server 2019' in os_lower or '2019' in os_lower:
        return 'Windows Server 2019', extract_windows_edition(os_name)
    elif 'windows server 2016' in os_lower or '2016' in os_lower:
        return 'Windows Server 2016', extract_windows_edition(os_name)
    elif 'oracle linux' in os_lower:
        match = re.search(r'oracle\s+linux\s+(\d+\.\d+|\d+)', os_lower)
        return (f'Oracle Linux {match.group(1)}', 'Server') if match else ('Oracle Linux', 'Server')
    elif 'ubuntu' in os_lower:
        match = re.search(r'ubuntu\s+(\d+\.\d+|\d+)', os_lower)
        return (f'Ubuntu {match.group(1)}', 'Server') if match else ('Ubuntu', 'Server')
    elif 'centos' in os_lower:
        match = re.search(r'centos\s+(\d+)', os_lower)
        return (f'CentOS {match.group(1)}', 'Server') if match else ('CentOS', 'Server')
    elif 'debian' in os_lower:
        match = re.search(r'debian\s+(\d+)', os_lower)
        return (f'Debian {match.group(1)}', 'Server') if match else ('Debian', 'Server')
    elif 'linux' in os_lower:
        return 'Linux (Other)', 'Server'
    return 'Unknown', 'Unknown'

def main():
    if len(sys.argv) < 3:
        print("╔════════════════════════════════════════════════════════════╗")
        print("║  Scout Summary Report Generator - Multilingual Support      ║")
        print("║  Auto-detects date range from CSV data                     ║")
        print("╚════════════════════════════════════════════════════════════╝")
        print()
        print("Usage: python3 generate_scout_report.py <csv> <output> [lang] [logo1.png] [logo2.png]")
        print()
        print("Languages: en (English), es (Español)")
        print()
        print("Examples:")
        print("  python3 generate_scout_report.py confor.csv report.html")
        print("  python3 generate_scout_report.py confor.csv report.html en")
        print("  python3 generate_scout_report.py confor.csv report.html es")
        print("  python3 generate_scout_report.py confor.csv report.html es corfo.png concierto.png")
        print()
        sys.exit(1)
    
    csv_file = sys.argv[1]
    output_file = sys.argv[2]
    
    # Detect language and logo files
    lang = 'en'  # default
    logo1_file = None
    logo2_file = None
    
    # Check if arg 3 is language code or logo file
    if len(sys.argv) > 3:
        if sys.argv[3] in ['en', 'es']:
            lang = sys.argv[3]
            logo1_file = sys.argv[4] if len(sys.argv) > 4 else None
            logo2_file = sys.argv[5] if len(sys.argv) > 5 else None
        else:
            # It's a logo file
            logo1_file = sys.argv[3]
            logo2_file = sys.argv[4] if len(sys.argv) > 4 else None
    
    if not os.path.exists(csv_file):
        print(f"❌ CSV file not found: {csv_file}")
        sys.exit(1)
    
    print(f"🚀 Scout Summary Report Generator")
    print(f"📥 Input CSV: {csv_file}")
    print(f"📤 Output HTML: {output_file}")
    print(f"🌍 Language: {'Español' if lang == 'es' else 'English'}")
    
    # Load logos if provided
    logo1_base64 = None
    logo2_base64 = None
    
    if logo1_file:
        print(f"📷 Logo 1: {logo1_file}", end=" ")
        logo1_base64 = encode_image_to_base64(logo1_file)
        if logo1_base64:
            print("✅")
        else:
            print("❌")
    
    if logo2_file:
        print(f"📷 Logo 2: {logo2_file}", end=" ")
        logo2_base64 = encode_image_to_base64(logo2_file)
        if logo2_base64:
            print("✅")
        else:
            print("❌")
    
    # Load CSV
    data_list = []
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data_list.append(row)
    
    print(f"📊 Processing {len(data_list)} VMs...")
    
    # Auto-detect date range from CSV
    min_date = None
    max_date = None
    for vm in data_list:
        if vm['MIN_DATE']:
            if min_date is None or vm['MIN_DATE'] < min_date:
                min_date = vm['MIN_DATE']
        if vm['MAX_DATE']:
            if max_date is None or vm['MAX_DATE'] > max_date:
                max_date = vm['MAX_DATE']
    
    report_period = f"{min_date} to {max_date}" if min_date and max_date else "Data Collection Report"
    print(f"📅 Period: {report_period}")
    
    # Process data
    total_vms = len(data_list)
    success_vms = 0
    failure_vms = 0
    
    for vm in data_list:
        good_files = int(vm['GOOD_FILES']) if vm['GOOD_FILES'].strip() else 0
        vm['Status'] = 'Success' if good_files > 0 else 'Failure'
        vm['CleanedOS'] = clean_os_name(vm['OS_NAME'].strip())
        vm['OSType'] = extract_os_type(vm['OS_NAME'].strip())
        vm['OSVersion'], vm['OSEdition'] = extract_os_version(vm['OS_NAME'].strip())
        
        if vm['Status'] == 'Success':
            success_vms += 1
        else:
            failure_vms += 1
    
    success_pct = round(success_vms / total_vms * 100, 1) if total_vms > 0 else 0
    failure_pct = round(100 - success_pct, 1)
    
    # Build stats
    datacenter_stats = defaultdict(lambda: {'total': 0, 'success': 0, 'failure': 0})
    os_type_stats = defaultdict(lambda: {'total': 0, 'success': 0, 'failure': 0})
    os_version_stats = defaultdict(lambda: {'total': 0, 'success': 0, 'failure': 0})
    edition_stats = defaultdict(lambda: defaultdict(lambda: {'total': 0, 'success': 0, 'failure': 0}))
    error_groups = defaultdict(list)
    
    for vm in data_list:
        good_files = int(vm['GOOD_FILES']) if vm['GOOD_FILES'].strip() else 0
        is_success = good_files > 0
        
        bucket = vm['BUCKET'].strip()
        datacenter_stats[bucket]['total'] += 1
        if is_success:
            datacenter_stats[bucket]['success'] += 1
        else:
            datacenter_stats[bucket]['failure'] += 1
        
        os_type = vm['OSType']
        os_type_stats[os_type]['total'] += 1
        if is_success:
            os_type_stats[os_type]['success'] += 1
        else:
            os_type_stats[os_type]['failure'] += 1
        
        os_version = vm['OSVersion']
        os_version_stats[os_version]['total'] += 1
        if is_success:
            os_version_stats[os_version]['success'] += 1
        else:
            os_version_stats[os_version]['failure'] += 1
        
        os_edition = vm['OSEdition']
        edition_stats[os_version][os_edition]['total'] += 1
        if is_success:
            edition_stats[os_version][os_edition]['success'] += 1
        else:
            edition_stats[os_version][os_edition]['failure'] += 1
        
        if not is_success:
            error_key = vm['Comments'][:60] if vm['Comments'] else 'Unknown Error'
            error_groups[error_key].append(vm)
    
    generated_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    colors_osversion = ['#2E8B72', '#C0392B', '#0087C6', '#F39C12', '#E67E22', '#D35400', '#BDC3C7', '#9B59B6', '#1ABC9C', '#34495E', '#E74C3C', '#16A085']
    
    chart_data = {
        'total': total_vms,
        'success': success_vms,
        'failure': failure_vms,
        'success_pct': success_pct,
        'datacenters': {dc: datacenter_stats[dc] for dc in sorted(datacenter_stats.keys())},
        'os_types': {os_type: os_type_stats[os_type] for os_type in sorted(os_type_stats.keys())},
        'os_versions': {ver: os_version_stats[ver] for ver in sorted(os_version_stats.keys())},
        'os_version_colors': colors_osversion
    }
    
    data_js = json.dumps(chart_data)
    error_labels = json.dumps(list(error_groups.keys())[:6])
    error_counts = json.dumps([len(error_groups[e]) for e in list(error_groups.keys())[:6]])
    
    # Build table rows
    dc_rows = ''
    for dc in sorted(datacenter_stats.keys()):
        dc_stats = datacenter_stats[dc]
        pct = round(dc_stats['success'] / dc_stats['total'] * 100, 1) if dc_stats['total'] > 0 else 0
        dc_rows += f'''              <tr>
                <td><strong>{dc}</strong></td>
                <td>{dc_stats['total']}</td>
                <td><span class="status-ok">{dc_stats['success']}</span></td>
                <td><span class="status-fail">{dc_stats['failure']}</span></td>
                <td><strong>{pct}%</strong></td>
              </tr>
'''
    
    os_type_rows = ''
    for os_type in sorted(os_type_stats.keys()):
        os_stats = os_type_stats[os_type]
        pct = round(os_stats['success'] / os_stats['total'] * 100, 1) if os_stats['total'] > 0 else 0
        os_type_rows += f'''                <tr>
                  <td><strong>{os_type}</strong></td>
                  <td>{os_stats['total']}</td>
                  <td><span class="status-ok">{os_stats['success']}</span></td>
                  <td><span class="status-fail">{os_stats['failure']}</span></td>
                  <td><strong>{pct}%</strong></td>
                </tr>
'''
    
    os_edition_rows = ''
    for os_version in sorted(edition_stats.keys()):
        editions = edition_stats[os_version]
        version_total = sum(e['total'] for e in editions.values())
        version_success = sum(e['success'] for e in editions.values())
        version_failure = sum(e['failure'] for e in editions.values())
        version_pct = round(version_success / version_total * 100, 1) if version_total > 0 else 0
        
        os_edition_rows += f'''                <tr class="parent">
                  <td><strong>{os_version}</strong></td>
                  <td></td>
                  <td>{version_total}</td>
                  <td><span class="status-ok">{version_success}</span></td>
                  <td><span class="status-fail">{version_failure}</span></td>
                  <td><strong>{version_pct}%</strong></td>
                </tr>
'''
        
        for edition in sorted(editions.keys()):
            e_stats = editions[edition]
            pct = round(e_stats['success'] / e_stats['total'] * 100, 1) if e_stats['total'] > 0 else 0
            os_edition_rows += f'''                <tr class="child">
                  <td></td>
                  <td style="padding-left:30px;">→ {edition}</td>
                  <td>{e_stats['total']}</td>
                  <td><span class="status-ok">{e_stats['success']}</span></td>
                  <td><span class="status-fail">{e_stats['failure']}</span></td>
                  <td><strong>{pct}%</strong></td>
                </tr>
'''
    
    inv_rows = ''
    for vm in data_list:
        good_files = int(vm['GOOD_FILES']) if vm['GOOD_FILES'].strip() else 0
        is_success = good_files > 0
        status = '<span class="status-ok">✅ OK</span>' if is_success else '<span class="status-fail">❌ FAIL</span>'
        row_class = '' if is_success else 'fail'
        inv_rows += f'''              <tr class="{row_class}">
                <td>{vm['BUCKET']}</td>
                <td><strong>{vm['SERVER']}</strong></td>
                <td>{vm['Private_IP']}</td>
                <td style="font-size:9px">{vm['CleanedOS']}</td>
                <td>{vm['MIN_DATE']}</td>
                <td>{vm['MAX_DATE']}</td>
                <td>{vm['No.FILES']}</td>
                <td><strong style="color:{'#2E8B72' if good_files > 0 else '#C0392B'}">{good_files}</strong></td>
                <td>{status}</td>
              </tr>
'''
    
    coll_rows = ''
    for vm in [v for v in data_list if v['Status'] == 'Success']:
        coll_rows += f'''              <tr>
                <td>{vm['BUCKET']}</td>
                <td><strong>{vm['SERVER']}</strong></td>
                <td>{vm['Private_IP']}</td>
                <td style="font-size:9px">{vm['CleanedOS']}</td>
                <td><span class="status-ok">{vm['GOOD_FILES']}</span></td>
                <td>{vm['Total_SIZE']}</td>
              </tr>
'''
    
    uncoll_rows = ''
    for vm in [v for v in data_list if v['Status'] == 'Failure']:
        error_msg = vm['Comments'][:70] if vm['Comments'] else 'Unknown Error'
        uncoll_rows += f'''              <tr class="fail">
                <td>{vm['BUCKET']}</td>
                <td><strong>{vm['SERVER']}</strong></td>
                <td>{vm['Private_IP']}</td>
                <td style="font-size:9px">{vm['CleanedOS']}</td>
                <td><span class="status-fail">{vm['GOOD_FILES']}</span></td>
                <td style="font-size:9px;color:#C0392B">{error_msg}</td>
              </tr>
'''
    
    # Build logo HTML
    logo_html = ''
    if logo1_base64:
        logo_html += f'<img src="data:image/png;base64,{logo1_base64}" style="height:50px; margin-right:20px;" alt="Logo 1">'
    if logo2_base64:
        logo_html += f'<img src="data:image/png;base64,{logo2_base64}" style="height:50px;" alt="Logo 2">'
    
    # Build HTML with language support
    html = f'''<!DOCTYPE html>
<html lang="{'es' if lang == 'es' else 'en'}">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>{get_text(lang, 'title')}</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ font-family:'Poppins',sans-serif; background:#F0F2F5; color:#222; }}
.header {{ background:#fff; padding:20px 30px; border-bottom:1px solid #E8EAF0; display:flex; align-items:center; justify-content:space-between; }}
.header-left {{ display:flex; align-items:center; gap:20px; }}
.header-logos {{ display:flex; align-items:center; gap:10px; }}
.header-title {{ font-size:24px; font-weight:800; color:#1a3a52; }}
.header-title .orange {{ color:#F36C24; }}
.header-center {{ font-size:11px; color:#666; font-weight:600; }}
.header-right {{ display:flex; gap:12px; align-items:center; }}
.print-btn {{ background:linear-gradient(120deg,#CF00CF 0%,#4812A2 52%,#0087C6 100%); color:#fff; border:none; padding:8px 16px; border-radius:6px; cursor:pointer; font-weight:600; font-size:10px; }}
.container {{ display:flex; height:calc(100vh - 80px); overflow:hidden; }}
.sidebar {{ width:180px; background:#F8F9FC; border-right:1px solid #E8EAF0; overflow-y:auto; padding:20px 0; }}
.sidebar-section {{ padding:15px 0; }}
.sidebar-title {{ font-size:9px; font-weight:800; color:#666; text-transform:uppercase; padding:0 15px; margin-bottom:8px; }}
.sidebar-item {{ padding:10px 15px; font-size:11px; color:#555; cursor:pointer; border-left:3px solid transparent; transition:all 300ms; }}
.sidebar-item:hover {{ background:#E8ECFF; color:#4812A2; }}
.sidebar-item.active {{ border-left-color:#CF00CF; background:#F5EDFA; color:#4812A2; font-weight:600; }}
.sidebar-count {{ display:inline-block; background:#4812A2; color:#fff; border-radius:12px; padding:2px 8px; font-size:9px; margin-left:8px; }}
.main {{ flex:1; overflow-y:auto; padding:30px; }}
.section {{ background:#fff; border-radius:12px; padding:24px; margin-bottom:24px; box-shadow:0 2px 8px rgba(0,0,0,.06); display:none; }}
.section.active {{ display:block; }}
.section-title {{ font-size:16px; font-weight:700; color:#1a3a52; margin-bottom:16px; }}
.section-subtitle {{ font-size:12px; color:#999; font-style:italic; margin-bottom:16px; margin-top:-10px; }}
.section-divider {{ margin:30px 0; padding:30px 0; border-top:2px solid #E8EAF0; }}
.kpi-grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr)); gap:16px; margin-bottom:24px; }}
.kpi {{ background:linear-gradient(135deg,#F5F7FF 0%,#EAEEF8 100%); padding:18px; border-radius:10px; border-left:4px solid #4812A2; }}
.kpi-label {{ font-size:10px; font-weight:700; color:#999; text-transform:uppercase; margin-bottom:6px; }}
.kpi-value {{ font-size:28px; font-weight:800; color:#1a3a52; }}
.kpi-sub {{ font-size:10px; color:#666; margin-top:6px; }}
.chart-grid {{ display:grid; grid-template-columns:1fr 1fr; gap:24px; margin-bottom:24px; }}
.chart-grid.full {{ grid-template-columns:1fr; }}
.chart-grid.three-col {{ grid-template-columns:1fr 1fr 1fr; }}
.chart-box {{ background:#fff; padding:20px; border-radius:10px; border:1px solid #F0F0F0; }}
.chart-title {{ font-size:12px; font-weight:700; color:#1a3a52; margin-bottom:16px; text-align:center; }}
.chart-wrapper {{ position:relative; width:100%; height:300px; }}
.insight {{ background:linear-gradient(135deg,#E8F4FF 0%,#D8E9F8 100%); border-left:4px solid #0087C6; padding:16px; border-radius:8px; margin-bottom:16px; }}
.insight strong {{ color:#1a3a52; display:block; margin-bottom:6px; }}
.insight p {{ font-size:11px; color:#555; line-height:1.6; display:flex; flex-wrap:wrap; gap:8px; align-items:center; }}
.insight-value {{ display:inline-block; font-weight:600; }}
.insight-success {{ color:#2E8B72; }}
.insight-failure {{ color:#C0392B; }}
.table-box {{ margin-bottom:20px; border:1px solid #E8EAF0; border-radius:8px; overflow:hidden; }}
.table-top {{ padding:12px 16px; background:#F5F7FF; border-bottom:1px solid #E8EAF0; font-size:11px; font-weight:600; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px; }}
.stat-item {{ display:inline-flex; align-items:center; gap:6px; }}
.stat-value {{ font-weight:700; padding:2px 8px; border-radius:4px; }}
.stat-total {{ color:#1a3a52; }}
.stat-success {{ color:#2E8B72; background:#E4F3EE; }}
.stat-failure {{ color:#C0392B; background:#FBEBE8; }}
.table-scroll {{ overflow-x:auto; max-height:500px; }}
table {{ width:100%; border-collapse:collapse; font-size:10px; }}
thead tr {{ background:linear-gradient(180deg,#4812A2,#1a3a52); }}
th {{ padding:12px 10px; text-align:left; font-weight:700; color:#fff; border-right:1px solid rgba(255,255,255,.3); }}
th:last-child {{ border-right:none; }}
tbody tr {{ border-bottom:1px solid #E8EAF0; }}
tbody tr:nth-child(even) {{ background:#F8F9FC; }}
tbody tr:hover {{ background:#E8ECFF; }}
tbody tr.fail {{ background:#FFF5F5; }}
tbody tr.parent {{ background:#F0F3F8; font-weight:600; }}
tbody tr.child td:first-child {{ padding-left:40px; }}
td {{ padding:10px; border-right:1px solid #E8EAF0; }}
td:last-child {{ border-right:none; }}
.status-ok {{ display:inline-block; background:#E4F3EE; color:#2E8B72; padding:4px 10px; border-radius:6px; font-weight:600; font-size:9px; }}
.status-fail {{ display:inline-block; background:#FBEBE8; color:#C0392B; padding:4px 10px; border-radius:6px; font-weight:600; font-size:9px; }}
.btn-export {{ background:linear-gradient(120deg,#CF00CF 0%,#4812A2 52%,#0087C6 100%); color:#fff; border:none; padding:6px 12px; border-radius:6px; cursor:pointer; font-size:10px; font-weight:600; }}
.btn-search {{ padding:8px 12px; border:1px solid #E8EAF0; border-radius:6px; font-size:10px; }}
.report-title {{ font-size:14px; font-weight:700; color:#1a3a52; margin-bottom:6px; }}
.report-subtitle {{ font-size:11px; color:#999; font-style:italic; margin-bottom:20px; }}
@media print {{ .sidebar{{ display:none; }} .main{{ padding:20px; }} }}
</style>
</head>
<body>

<div class="header">
  <div class="header-left">
    <div class="header-logos">
      {logo_html}
    </div>
    <div class="header-title">Scout<span class="orange">Summary</span></div>
  </div>
  <div class="header-center">{get_text(lang, 'data_collection')} | {report_period} | Generated: {generated_date}</div>
  <div class="header-right">
    <button class="print-btn" onclick="window.print()">{get_text(lang, 'print_btn')}</button>
  </div>
</div>

<div class="container">
  <div class="sidebar">
    <div class="sidebar-section">
      <div class="sidebar-title">📊 {get_text(lang, 'report_sections')}</div>
      <div class="sidebar-item active" onclick="switchTab('summary')">📊 {get_text(lang, 'data_collection')}<span class="sidebar-count">6</span></div>
      <div class="sidebar-item" onclick="switchTab('inventory')">📋 {get_text(lang, 'inventory_master')}<span class="sidebar-count">{total_vms}</span></div>
      <div class="sidebar-item" onclick="switchTab('datacenter')">🏢 {get_text(lang, 'infrastructure')}<span class="sidebar-count">{len(datacenter_stats)}</span></div>
      <div class="sidebar-item" onclick="switchTab('os')">🖥️ {get_text(lang, 'os_landscape')}<span class="sidebar-count">{len(os_type_stats) + len(os_version_stats)}</span></div>
      <div class="sidebar-item" onclick="switchTab('collected')">✅ {get_text(lang, 'collected_vms')}<span class="sidebar-count">{success_vms}</span></div>
      <div class="sidebar-item" onclick="switchTab('uncollected')">❌ {get_text(lang, 'uncollected_vms')}<span class="sidebar-count">{failure_vms}</span></div>
    </div>
  </div>

  <div class="main">
    <!-- SUMMARY -->
    <div id="summary" class="section active">
      <div class="section-title">📊 {get_text(lang, 'data_collection')}</div>
      <div class="kpi-grid">
        <div class="kpi">
          <div class="kpi-label">{get_text(lang, 'total_vms')}</div>
          <div class="kpi-value">{total_vms}</div>
        </div>
        <div class="kpi">
          <div class="kpi-label">{get_text(lang, 'success_label')}</div>
          <div class="kpi-value" style="color:#2E8B72">{success_vms}</div>
          <div class="kpi-sub">{success_pct}%</div>
        </div>
        <div class="kpi">
          <div class="kpi-label">{get_text(lang, 'failure_label')}</div>
          <div class="kpi-value" style="color:#C0392B">{failure_vms}</div>
          <div class="kpi-sub">{failure_pct}%</div>
        </div>
      </div>

      <div class="chart-grid">
        <div class="chart-box">
          <div class="chart-title">🥧 {get_text(lang, 'success_distribution')}</div>
          <div class="chart-wrapper">
            <canvas id="overallChart"></canvas>
          </div>
        </div>
        <div class="chart-box">
          <div class="chart-title">📈 {get_text(lang, 'success_pct_by_dc')}</div>
          <div class="chart-wrapper">
            <canvas id="dcRateChart"></canvas>
          </div>
        </div>
      </div>

      <div class="insight">
        <strong>💡 {get_text(lang, 'key_insights')}</strong>
        <p><span class="insight-value insight-success">✅ {success_vms} VMs</span> {get_text(lang, 'collected')} ({success_pct}%) | <span class="insight-value insight-failure">❌ {failure_vms} VMs</span> {get_text(lang, 'no_collection')} ({failure_pct}%)</p>
      </div>
    </div>

    <!-- DATACENTER -->
    <div id="datacenter" class="section">
      <div class="section-title">🏢 {get_text(lang, 'infrastructure')}</div>
      <div class="section-subtitle">{get_text(lang, 'servers_make_up')}</div>

      <div class="chart-grid full">
        <div class="chart-box">
          <div class="chart-title">{get_text(lang, 'dc_distribution')}</div>
          <div class="chart-wrapper">
            <canvas id="dcCompositionChart"></canvas>
          </div>
        </div>
      </div>

      <div class="section-title" style="margin-top:20px; font-size:14px;">{get_text(lang, 'dc_workloads')}</div>
      <div class="table-box">
        <div class="table-top">{get_text(lang, 'server_distribution')}</div>
        <div class="table-scroll">
          <table>
            <thead>
              <tr>
                <th>{get_text(lang, 'datacenter')}</th>
                <th>{get_text(lang, 'total_vms')}</th>
                <th>{get_text(lang, 'success')}</th>
                <th>{get_text(lang, 'failure')}</th>
                <th>{get_text(lang, 'success_pct_by_dc')}</th>
              </tr>
            </thead>
            <tbody>
{dc_rows}
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- OS ANALYSIS -->
    <div id="os" class="section">
      <div class="section-title">🖥️ {get_text(lang, 'os_landscape')}</div>

      <div style="margin-bottom:40px;">
        <h3 style="font-size:14px; font-weight:700; color:#1a3a52; margin-bottom:16px;">{get_text(lang, 'os_type_dist')}</h3>
        <div class="chart-grid three-col">
          <div class="chart-box">
            <div class="chart-title">{get_text(lang, 'os_type_dist')}</div>
            <div class="chart-wrapper">
              <canvas id="osTypeDistChart"></canvas>
            </div>
          </div>
          <div class="chart-box">
            <div class="chart-title">{get_text(lang, 'success_failure_os_type')}</div>
            <div class="chart-wrapper">
              <canvas id="osTypeBreakdownChart"></canvas>
            </div>
          </div>
          <div class="chart-box">
            <div class="chart-title">{get_text(lang, 'os_type_rate')}</div>
            <div class="chart-wrapper">
              <canvas id="osTypeRateChart"></canvas>
            </div>
          </div>
        </div>

        <div class="table-box" style="margin-top:20px;">
          <div class="table-top">{get_text(lang, 'os_type_breakdown')}</div>
          <div class="table-scroll">
            <table>
              <thead>
                <tr>
                  <th>{get_text(lang, 'operating_system')}</th>
                  <th>{get_text(lang, 'total_vms')}</th>
                  <th>{get_text(lang, 'success')}</th>
                  <th>{get_text(lang, 'failure')}</th>
                  <th>{get_text(lang, 'success_pct_by_dc')}</th>
                </tr>
              </thead>
              <tbody>
{os_type_rows}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <div class="section-divider"></div>

      <div style="margin-bottom:40px;">
        <h3 style="font-size:14px; font-weight:700; color:#1a3a52; margin-bottom:16px;">{get_text(lang, 'os_version_edition')}</h3>
        <div class="table-box">
          <div class="table-top">{get_text(lang, 'os_breakdown')}</div>
          <div class="table-scroll">
            <table>
              <thead>
                <tr>
                  <th>{get_text(lang, 'operating_system')}</th>
                  <th>{get_text(lang, 'status')}</th>
                  <th>{get_text(lang, 'total_vms')}</th>
                  <th>{get_text(lang, 'success')}</th>
                  <th>{get_text(lang, 'failure')}</th>
                  <th>{get_text(lang, 'success_pct_by_dc')}</th>
                </tr>
              </thead>
              <tbody>
{os_edition_rows}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <div class="section-divider"></div>

      <div>
        <div class="report-title">💻 {get_text(lang, 'os_version_report')}</div>
        <div class="report-subtitle">{get_text(lang, 'breakdown_os_versions')}</div>
        
        <div class="chart-grid three-col">
          <div class="chart-box">
            <div class="chart-title">{get_text(lang, 'os_version_dist')}</div>
            <div class="chart-wrapper">
              <canvas id="osVersionDistChart"></canvas>
            </div>
          </div>
          <div class="chart-box">
            <div class="chart-title">{get_text(lang, 'success_failure_os_version')}</div>
            <div class="chart-wrapper">
              <canvas id="osVersionBreakdownChart"></canvas>
            </div>
          </div>
          <div class="chart-box">
            <div class="chart-title">{get_text(lang, 'os_version_rate')}</div>
            <div class="chart-wrapper">
              <canvas id="osVersionRateChart"></canvas>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- INVENTORY -->
    <div id="inventory" class="section">
      <div class="section-title">📋 {get_text(lang, 'inventory_master')}</div>

      <div class="table-box">
        <div class="table-top">
          <div>
            <span class="stat-item">{get_text(lang, 'total_vms')}: <span class="stat-value stat-total">{total_vms}</span></span>
            <span class="stat-item">{get_text(lang, 'success')}: <span class="stat-value stat-success">{success_vms}</span></span>
            <span class="stat-item">{get_text(lang, 'failure')}: <span class="stat-value stat-failure">{failure_vms}</span></span>
          </div>
          <div>
            <input type="text" id="searchInv" class="btn-search" placeholder="🔍 {get_text(lang, 'search_vm_ip')}">
            <button class="btn-export" onclick="exportInventory()">{get_text(lang, 'export_csv')}</button>
          </div>
        </div>
        <div class="table-scroll">
          <table id="invTable">
            <thead>
              <tr>
                <th>{get_text(lang, 'vcenter')}</th>
                <th>{get_text(lang, 'vm_name')}</th>
                <th>{get_text(lang, 'ip_address')}</th>
                <th>{get_text(lang, 'os_name')}</th>
                <th>{get_text(lang, 'start_date')}</th>
                <th>{get_text(lang, 'end_date')}</th>
                <th>{get_text(lang, 'total_files')}</th>
                <th>{get_text(lang, 'good_files')}</th>
                <th>{get_text(lang, 'status')}</th>
              </tr>
            </thead>
            <tbody>
{inv_rows}
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- COLLECTED -->
    <div id="collected" class="section">
      <div class="section-title">✅ {get_text(lang, 'collected_vms')}</div>

      <div class="table-box">
        <div class="table-top">{get_text(lang, 'collected_vms')}: <span class="stat-value stat-success">{success_vms}</span></div>
        <div class="table-scroll">
          <table>
            <thead>
              <tr>
                <th>{get_text(lang, 'vcenter')}</th>
                <th>{get_text(lang, 'vm_name')}</th>
                <th>{get_text(lang, 'ip_address')}</th>
                <th>{get_text(lang, 'os_name')}</th>
                <th>{get_text(lang, 'good_files')}</th>
                <th>{get_text(lang, 'total_size')}</th>
              </tr>
            </thead>
            <tbody>
{coll_rows}
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- UNCOLLECTED -->
    <div id="uncollected" class="section">
      <div class="section-title">❌ {get_text(lang, 'uncollected_vms')}</div>

      <div class="chart-grid full">
        <div class="chart-box">
          <div class="chart-title">{get_text(lang, 'error_distribution')}</div>
          <div class="chart-wrapper">
            <canvas id="errorChart"></canvas>
          </div>
        </div>
      </div>

      <div class="table-box">
        <div class="table-top">{get_text(lang, 'uncollected_vms')}: <span class="stat-value stat-failure">{failure_vms}</span></div>
        <div class="table-scroll">
          <table>
            <thead>
              <tr>
                <th>{get_text(lang, 'vcenter')}</th>
                <th>{get_text(lang, 'vm_name')}</th>
                <th>{get_text(lang, 'ip_address')}</th>
                <th>{get_text(lang, 'os_name')}</th>
                <th>{get_text(lang, 'good_files')}</th>
                <th>{get_text(lang, 'error_message')}</th>
              </tr>
            </thead>
            <tbody>
{uncoll_rows}
            </tbody>
          </table>
        </div>
      </div>
    </div>

  </div>
</div>

<script>
const appData = {data_js};
const errorLabels = {error_labels};
const errorCounts = {error_counts};
let activeCharts = {{}};

function switchTab(tabName) {{
  document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
  document.querySelectorAll('.sidebar-item').forEach(s => s.classList.remove('active'));
  
  document.getElementById(tabName).classList.add('active');
  event.target.closest('.sidebar-item').classList.add('active');
  
  Object.keys(activeCharts).forEach(k => {{
    if (activeCharts[k]) activeCharts[k].destroy();
  }});
  activeCharts = {{}};
  
  setTimeout(() => {{
    if (tabName === 'summary') initSummaryCharts();
    else if (tabName === 'datacenter') initDcCharts();
    else if (tabName === 'os') initOsCharts();
    else if (tabName === 'uncollected') initErrorChart();
  }}, 100);
}}

function filterInventory() {{
  const input = document.getElementById('searchInv').value.toUpperCase();
  const table = document.getElementById('invTable');
  const rows = table.getElementsByTagName('tr');
  for (let i = 1; i < rows.length; i++) {{
    const text = rows[i].textContent.toUpperCase();
    rows[i].style.display = text.indexOf(input) > -1 ? '' : 'none';
  }}
}}

document.getElementById('searchInv').addEventListener('keyup', filterInventory);

function exportInventory() {{
  const table = document.getElementById('invTable');
  let csv = [];
  for (let i = 0; i < table.rows.length; i++) {{
    let row = [];
    for (let j = 0; j < table.rows[i].cells.length; j++) {{
      row.push('"' + table.rows[i].cells[j].textContent.replace(/"/g, '""') + '"');
    }}
    csv.push(row.join(','));
  }}
  const link = document.createElement('a');
  link.href = 'data:text/csv,' + encodeURIComponent(csv.join('\\n'));
  link.download = 'inventory_export.csv';
  link.click();
}}

function initSummaryCharts() {{
  try {{
    const ctx1 = document.getElementById('overallChart');
    activeCharts.overall = new Chart(ctx1, {{
      type: 'doughnut',
      data: {{
        labels: ['{get_text(lang, 'success')}', '{get_text(lang, 'failure')}'],
        datasets: [{{
          data: [appData.success, appData.failure],
          backgroundColor: ['#2E8B72', '#C0392B'],
          borderColor: '#fff',
          borderWidth: 2
        }}]
      }},
      options: {{ responsive: true, maintainAspectRatio: false, plugins: {{ legend: {{ position: 'bottom' }} }} }}
    }});

    const ctx2 = document.getElementById('dcRateChart');
    const dcNames = Object.keys(appData.datacenters);
    const dcPcts = dcNames.map(dc => (appData.datacenters[dc].success / appData.datacenters[dc].total * 100).toFixed(1));
    
    activeCharts.dcRate = new Chart(ctx2, {{
      type: 'line',
      data: {{
        labels: dcNames,
        datasets: [{{
          label: '{get_text(lang, 'success_pct_by_dc')}',
          data: dcPcts,
          borderColor: '#0087C6',
          backgroundColor: 'rgba(0,135,198,0.1)',
          tension: 0.4,
          fill: true,
          pointRadius: 5
        }}]
      }},
      options: {{ responsive: true, maintainAspectRatio: false, scales: {{ y: {{ max: 100 }} }} }}
    }});
  }} catch(e) {{ console.log('Summary error:', e); }}
}}

function initDcCharts() {{
  try {{
    const ctx = document.getElementById('dcCompositionChart');
    const dcNames = Object.keys(appData.datacenters);
    activeCharts.dcComp = new Chart(ctx, {{
      type: 'bar',
      data: {{
        labels: dcNames,
        datasets: [
          {{ label: '{get_text(lang, 'success')}', data: dcNames.map(dc => appData.datacenters[dc].success), backgroundColor: '#2E8B72' }},
          {{ label: '{get_text(lang, 'failure')}', data: dcNames.map(dc => appData.datacenters[dc].failure), backgroundColor: '#C0392B' }}
        ]
      }},
      options: {{ responsive: true, maintainAspectRatio: false, scales: {{ y: {{ beginAtZero: true }} }}, plugins: {{ legend: {{ position: 'top' }} }} }}
    }});
  }} catch(e) {{ console.log('DC error:', e); }}
}}

function initOsCharts() {{
  try {{
    const ctx1 = document.getElementById('osTypeDistChart');
    activeCharts.osTypeDist = new Chart(ctx1, {{
      type: 'doughnut',
      data: {{
        labels: Object.keys(appData.os_types),
        datasets: [{{
          data: Object.keys(appData.os_types).map(t => appData.os_types[t].total),
          backgroundColor: ['#2E8B72', '#C0392B', '#0087C6']
        }}]
      }},
      options: {{ responsive: true, maintainAspectRatio: false, plugins: {{ legend: {{ position: 'bottom' }} }} }}
    }});

    const ctx2 = document.getElementById('osTypeBreakdownChart');
    activeCharts.osTypeBreak = new Chart(ctx2, {{
      type: 'bar',
      data: {{
        labels: Object.keys(appData.os_types),
        datasets: [
          {{ label: '{get_text(lang, 'success')}', data: Object.keys(appData.os_types).map(t => appData.os_types[t].success), backgroundColor: '#2E8B72' }},
          {{ label: '{get_text(lang, 'failure')}', data: Object.keys(appData.os_types).map(t => appData.os_types[t].failure), backgroundColor: '#C0392B' }}
        ]
      }},
      options: {{ responsive: true, maintainAspectRatio: false }}
    }});

    const ctx3 = document.getElementById('osTypeRateChart');
    activeCharts.osTypeRate = new Chart(ctx3, {{
      type: 'line',
      data: {{
        labels: Object.keys(appData.os_types),
        datasets: [{{
          label: '{get_text(lang, 'os_type_rate')}',
          data: Object.keys(appData.os_types).map(t => (appData.os_types[t].success / appData.os_types[t].total * 100).toFixed(1)),
          borderColor: '#0087C6',
          backgroundColor: 'rgba(0,135,198,0.1)',
          tension: 0.4,
          fill: true,
          pointRadius: 5
        }}]
      }},
      options: {{ responsive: true, maintainAspectRatio: false, scales: {{ y: {{ max: 100 }} }} }}
    }});

    const ctx4 = document.getElementById('osVersionDistChart');
    activeCharts.osVersionDist = new Chart(ctx4, {{
      type: 'doughnut',
      data: {{
        labels: Object.keys(appData.os_versions),
        datasets: [{{
          data: Object.keys(appData.os_versions).map(v => appData.os_versions[v].total),
          backgroundColor: appData.os_version_colors
        }}]
      }},
      options: {{ responsive: true, maintainAspectRatio: false, plugins: {{ legend: {{ position: 'bottom' }} }} }}
    }});

    const ctx5 = document.getElementById('osVersionBreakdownChart');
    activeCharts.osVersionBreak = new Chart(ctx5, {{
      type: 'bar',
      data: {{
        labels: Object.keys(appData.os_versions),
        datasets: [
          {{ label: '{get_text(lang, 'success')}', data: Object.keys(appData.os_versions).map(v => appData.os_versions[v].success), backgroundColor: '#2E8B72' }},
          {{ label: '{get_text(lang, 'failure')}', data: Object.keys(appData.os_versions).map(v => appData.os_versions[v].failure), backgroundColor: '#C0392B' }}
        ]
      }},
      options: {{ responsive: true, maintainAspectRatio: false }}
    }});

    const ctx6 = document.getElementById('osVersionRateChart');
    activeCharts.osVersionRate = new Chart(ctx6, {{
      type: 'line',
      data: {{
        labels: Object.keys(appData.os_versions),
        datasets: [{{
          label: '{get_text(lang, 'os_version_rate')}',
          data: Object.keys(appData.os_versions).map(v => (appData.os_versions[v].success / appData.os_versions[v].total * 100).toFixed(1)),
          borderColor: '#0087C6',
          backgroundColor: 'rgba(0,135,198,0.1)',
          tension: 0.4,
          fill: true,
          pointRadius: 5
        }}]
      }},
      options: {{ responsive: true, maintainAspectRatio: false, scales: {{ y: {{ max: 100 }} }} }}
    }});
  }} catch(e) {{ console.log('OS error:', e); }}
}}

function initErrorChart() {{
  try {{
    const ctx = document.getElementById('errorChart');
    activeCharts.error = new Chart(ctx, {{
      type: 'doughnut',
      data: {{
        labels: errorLabels,
        datasets: [{{
          data: errorCounts,
          backgroundColor: ['#C0392B', '#E74C3C', '#F39C12', '#E67E22', '#D35400', '#BDC3C7']
        }}]
      }},
      options: {{ responsive: true, maintainAspectRatio: false, plugins: {{ legend: {{ position: 'bottom' }} }} }}
    }});
  }} catch(e) {{ console.log('Error chart:', e); }}
}}

window.addEventListener('load', () => {{ setTimeout(initSummaryCharts, 500); }});
</script>

</body>
</html>
'''
    
    # Write output
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"")
    print(f"✅ Report generated successfully!")
    print(f"📁 Location: {output_file}")
    print(f"✅ {success_vms} VMs successful ({success_pct}%)")
    print(f"✅ {failure_vms} VMs failed ({failure_pct}%)")

if __name__ == '__main__':
    main()
