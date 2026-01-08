from flask import Flask, request, jsonify, render_template
import uuid
from server_scanner import identify_server
from file_checker import check_exposed_files
from scan_logger import save_scan_result, get_scan_statistics


def write_log(message):
    """
    Imprime mensagem de debug no terminal
    """
    print(f"[DEBUG] {message}")


app = Flask(__name__)

@app.route('/')
def index():
    """
    Página inicial com a interface web
    """
    return render_template('index.html')

@app.route('/ScanApp', methods=['GET'])
def scan_app():
    """
    Endpoint ScanApp que aceita uma URL como parâmetro e retorna JSON com ID e Description
    Verifica o servidor web e arquivos expostos

    Exemplo de uso: GET /ScanApp?url=https://example.com
    """
    # Obtém o parâmetro 'url' da query string
    url = request.args.get('url')
    write_log(f"ScanApp chamado para {url}")
    # Valida se o parâmetro foi fornecido
    if not url:
        return jsonify({
            'error': 'O parâmetro "url" é obrigatório'
        }), 400

    # Identifica o servidor
    server_info = identify_server(url)

    # Verifica arquivos expostos
    files_info = check_exposed_files(url)

    # Gera um ID único para este scan
    scan_id = str(uuid.uuid4())

    # Monta a descrição baseada no resultado
    description_parts = []

    if server_info['success']:
        server_desc = f"Servidor: {server_info['server_type']}"
        if server_info.get('is_genexus'):
            server_desc += " (Genexus)"
        description_parts.append(server_desc)
    else:
        description_parts.append(f"Servidor: Erro ao identificar")

    if files_info['success']:
        if files_info['found_count'] > 0:
            description_parts.append(f"{files_info['found_count']} arquivo(s) exposto(s)")
        else:
            description_parts.append("Nenhum arquivo exposto")

    description = "Scan completo realizado. " + " | ".join(description_parts)

    # Salva o resultado do scan em JSON
    files_found_count = files_info.get('found_count', 0) if files_info.get('success') else 0
    save_scan_result(url, files_found_count, server_info, files_info)

    # Retorna o JSON completo
    response = {
        'ID': scan_id,
        'Description': description,
        'URL': url,
        'ServerInfo': server_info,
        'FilesInfo': files_info
    }

    return jsonify(response), 200


@app.route('/stats', methods=['GET'])
def get_stats():
    """
    Endpoint para obter estatísticas dos scans realizados
    """
    stats = get_scan_statistics()
    return jsonify(stats), 200


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

