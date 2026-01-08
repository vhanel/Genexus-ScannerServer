import json
import os
from datetime import datetime

# Diretório para armazenar os dados
DATA_DIR = 'data'

# Garante que o diretório existe
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)


def save_scan_result(url, files_found_count, server_info, files_info):
    """
    Salva o resultado do scan em arquivos JSON separados

    Args:
        url: URL escaneada
        files_found_count: Quantidade de arquivos encontrados
        server_info: Informações do servidor
        files_info: Informações dos arquivos
    """
    # Prepara os dados do scan
    scan_data = {
        'timestamp': datetime.now().isoformat(),
        'url': url,
        'files_found_count': files_found_count,
        'server_type': server_info.get('server_type', 'Unknown') if server_info.get('success') else 'Error',
        'scan_successful': server_info.get('success', False),
        'is_genexus': server_info.get('is_genexus', False) if server_info.get('success') else False
    }

    # Adiciona lista de arquivos encontrados se houver (apenas os nomes)
    if files_found_count > 0 and files_info.get('success'):
        scan_data['found_files'] = [
            f['filename']
            for f in files_info.get('found_files', [])
        ]

    # Define qual arquivo usar baseado na quantidade de arquivos encontrados
    if files_found_count > 0:
        filename = os.path.join(DATA_DIR, 'scans_with_findings.json')
    else:
        filename = os.path.join(DATA_DIR, 'scans_without_findings.json')

    # Lê o arquivo existente ou cria uma lista vazia
    if os.path.exists(filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                scans = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            scans = []
    else:
        scans = []

    # Adiciona o novo scan
    scans.append(scan_data)

    # Salva de volta no arquivo
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(scans, f, indent=2, ensure_ascii=False)

    print(f"[LOG] Scan salvo em {filename}: {url} - {files_found_count} arquivo(s) encontrado(s)")


def get_scan_statistics():
    """
    Retorna estatísticas dos scans realizados

    Returns:
        dict: Estatísticas dos scans
    """
    stats = {
        'total_scans': 0,
        'scans_with_findings': 0,
        'scans_without_findings': 0,
        'total_files_found': 0
    }

    # Conta scans com findings
    filename_with = os.path.join(DATA_DIR, 'scans_with_findings.json')
    if os.path.exists(filename_with):
        try:
            with open(filename_with, 'r', encoding='utf-8') as f:
                scans_with = json.load(f)
                stats['scans_with_findings'] = len(scans_with)
                stats['total_files_found'] = sum(s.get('files_found_count', 0) for s in scans_with)
        except:
            pass

    # Conta scans sem findings
    filename_without = os.path.join(DATA_DIR, 'scans_without_findings.json')
    if os.path.exists(filename_without):
        try:
            with open(filename_without, 'r', encoding='utf-8') as f:
                scans_without = json.load(f)
                stats['scans_without_findings'] = len(scans_without)
        except:
            pass

    stats['total_scans'] = stats['scans_with_findings'] + stats['scans_without_findings']

    return stats

