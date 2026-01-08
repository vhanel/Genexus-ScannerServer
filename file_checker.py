import requests
from urllib.parse import urljoin, urlparse
import os
import urllib3
from concurrent.futures import ThreadPoolExecutor, as_completed

# Desabilita warnings de SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Número máximo de threads simultâneas
MAX_WORKERS = 10


def write_log(message):
    """
    Imprime mensagem de debug no terminal
    """
    print(f"[DEBUG] {message}")


def load_sensitive_files(file_path='sensitive_files.txt'):
    """
    Carrega a lista de arquivos sensíveis de um arquivo txt

    Suporta marcação [GXGRAL_RELATED] para arquivos que devem ser buscados
    automaticamente quando gxgral.js for encontrado.

    Args:
        file_path: Caminho do arquivo txt com a lista de arquivos

    Returns:
        tuple: (lista de arquivos sensíveis, lista de arquivos relacionados ao gxgral.js)
    """
    try:
        # Obtém o diretório do script atual
        script_dir = os.path.dirname(os.path.abspath(__file__))
        full_path = os.path.join(script_dir, file_path)

        files = []
        gxgral_related = []

        # Lê o arquivo e processa cada linha
        with open(full_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()

                # Ignora linhas vazias e comentários
                if not line or line.startswith('#'):
                    continue

                # Verifica se tem a marcação [GXGRAL_RELATED]
                if '[GXGRAL_RELATED]' in line:
                    # Remove a marcação e pega o nome do arquivo
                    filename = line.replace('[GXGRAL_RELATED]', '').strip()
                    files.append(filename)
                    gxgral_related.append(filename)
                else:
                    files.append(line)

        return files, gxgral_related
    except FileNotFoundError:
        print(f"Aviso: Arquivo {file_path} não encontrado. Usando lista padrão vazia.")
        return [], []
    except Exception as e:
        print(f"Erro ao carregar arquivo {file_path}: {str(e)}. Usando lista padrão vazia.")
        return [], []


# Carrega a lista de arquivos sensíveis do arquivo txt
# SENSITIVE_FILES: todos os arquivos a serem verificados
# GXGRAL_RELATED_FILES: arquivos marcados com [GXGRAL_RELATED] que serão buscados
#                       automaticamente quando gxgral.js for encontrado
SENSITIVE_FILES, GXGRAL_RELATED_FILES = load_sensitive_files()


def check_exposed_files(url, custom_files=None, timeout=3):
    """
    Verifica se arquivos sensíveis estão expostos na URL fornecida

    Args:
        url: URL base do site a ser verificado
        custom_files: Lista opcional de arquivos customizados para verificar
        timeout: Timeout para cada requisição (padrão: 3 segundos)

    Returns:
        dict: Informações sobre os arquivos encontrados
    """
    try:
        # Adiciona esquema http:// se não estiver presente
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url

        # Extrai o diretório base da URL (sem o arquivo)
        parsed_url = urlparse(url)
        path = parsed_url.path

        # Se a URL termina com /, usa como está
        # Se não, remove o arquivo do caminho (ex: /backoffice/login.aspx -> /backoffice/)
        if not path.endswith('/'):
            path = '/'.join(path.split('/')[:-1]) + '/'

        # A "raiz" é o diretório da URL fornecida
        root_url = f"{parsed_url.scheme}://{parsed_url.netloc}{path}"

        write_log(f"URL fornecida: {url}")
        write_log(f"Verificando arquivos em: {root_url}")

        # Define quais arquivos verificar
        files_to_check = custom_files if custom_files else SENSITIVE_FILES

        # Faz uma requisição de baseline para detectar falsos positivos
        baseline_url = urljoin(root_url, 'nonexistent-file-test-12345.xyz')
        baseline = get_baseline_response(baseline_url, timeout)

        found_files = []
        not_found_files = []
        error_files = []
        gxgral_locations = []  # Armazena os diretórios onde gxgral.js foi encontrado
        checked_urls = set()  # Armazena todas as URLs já verificadas

        # Verifica arquivos em paralelo usando threads
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            # Cria um dicionário de futures para rastrear cada tarefa
            future_to_info = {}
            for filename in files_to_check:
                file_url = urljoin(root_url, filename)
                future = executor.submit(check_single_file, file_url, timeout, baseline)
                future_to_info[future] = {'filename': filename, 'url': file_url}
                checked_urls.add(file_url)  # Marca como verificado

            # Processa os resultados conforme são completados
            for future in as_completed(future_to_info):
                info = future_to_info[future]
                filename = info['filename']
                file_url = info['url']

                try:
                    result = future.result()

                    if result['found']:
                        found_files.append(result)

                        # Se encontrou gxgral.js, armazena o diretório para busca adicional
                        if filename == 'gxgral.js':
                            parsed = urlparse(file_url)
                            dir_path = '/'.join(parsed.path.split('/')[:-1]) + '/'
                            gxgral_dir = f"{parsed.scheme}://{parsed.netloc}{dir_path}"

                            # Adiciona o diretório para busca adicional
                            if gxgral_dir not in gxgral_locations:
                                gxgral_locations.append(gxgral_dir)
                                write_log(f"gxgral.js encontrado em: {gxgral_dir}")
                                write_log(f"Verificando arquivos Genexus adicionais neste diretório...")

                    elif result['error']:
                        error_files.append(result)
                    else:
                        not_found_files.append(filename)

                except Exception as e:
                    write_log(f"Erro ao verificar {filename}: {str(e)}")
                    error_files.append({
                        'found': False,
                        'error': True,
                        'filename': filename,
                        'url': file_url,
                        'error_message': str(e)
                    })

        # Se encontrou gxgral.js em algum diretório, verifica arquivos Genexus adicionais
        if gxgral_locations:
            write_log(f"Iniciando busca adicional de arquivos Genexus em {len(gxgral_locations)} localização(ões)...")

            with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
                future_to_info = {}

                for gxgral_dir in gxgral_locations:
                    for genexus_file in GXGRAL_RELATED_FILES:
                        # Pula gxgral.js pois já foi verificado
                        if genexus_file == 'gxgral.js':
                            continue

                        file_url = urljoin(gxgral_dir, genexus_file)

                        # Verifica se já não foi checado (evita duplicatas)
                        if file_url not in checked_urls:
                            future = executor.submit(check_single_file, file_url, timeout, baseline)
                            future_to_info[future] = {'filename': genexus_file, 'url': file_url}
                            checked_urls.add(file_url)  # Marca como verificado

                # Processa os resultados da busca adicional
                for future in as_completed(future_to_info):
                    info = future_to_info[future]
                    filename = info['filename']
                    file_url = info['url']

                    try:
                        result = future.result()

                        if result['found']:
                            found_files.append(result)
                            write_log(f"Arquivo Genexus adicional encontrado: {filename}")

                    except Exception as e:
                        write_log(f"Erro ao verificar arquivo Genexus adicional {filename}: {str(e)}")

        return {
            'success': True,
            'base_url': url,
            'root_url': root_url,
            'total_checked': len(files_to_check),
            'found_count': len(found_files),
            'not_found_count': len(not_found_files),
            'error_count': len(error_files),
            'found_files': found_files,
            'not_found_files': not_found_files,
            'error_files': error_files
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': f'Erro ao verificar arquivos: {str(e)}'
        }


def get_baseline_response(baseline_url, timeout=3):
    """
    Obtém uma resposta baseline para detectar falsos positivos
    Faz requisição para um arquivo que certamente não existe

    Args:
        baseline_url: URL de um arquivo inexistente
        timeout: Timeout para a requisição

    Returns:
        dict: Informações sobre a resposta baseline (tamanho, content-type, etc)
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }

    try:
        response = requests.get(baseline_url, timeout=(2, timeout), allow_redirects=True, headers=headers, verify=False)

        # Se retornou 200 para arquivo inexistente, o site redireciona 404s
        if response.status_code == 200:
            content_length = len(response.content) if response.content else 0
            return {
                'has_custom_404': True,
                'status_code': response.status_code,
                'content_length': content_length,
                'content_type': response.headers.get('Content-Type', ''),
                'content_sample': response.content[:100] if response.content else b''
            }
        else:
            return {
                'has_custom_404': False,
                'status_code': response.status_code
            }
    except:
        return {
            'has_custom_404': False,
            'status_code': None
        }


def check_single_file(file_url, timeout=3, baseline=None):
    """
    Verifica se um único arquivo está acessível

    Args:
        file_url: URL completa do arquivo
        timeout: Timeout para a requisição

    Returns:
        dict: Informações sobre o arquivo
    """
    filename = file_url.split('/')[-1]

    # Headers para simular um navegador real
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }

    try:
        # Faz requisição GET para poder verificar o conteúdo
        response = requests.get(file_url, timeout=(2, timeout), allow_redirects=True, headers=headers, verify=False)

        # Considera encontrado se status for 200
        if response.status_code == 200:
            content_type = response.headers.get('Content-Type', 'unknown')
            content_length = len(response.content) if response.content else 0

            # Verifica se é um falso positivo
            is_false_positive = False

            if baseline and baseline.get('has_custom_404'):
                # Compara com a resposta baseline
                baseline_length = baseline.get('content_length', 0)
                baseline_type = baseline.get('content_type', '')

                # Se o tamanho for muito similar ao baseline (±10%), provavelmente é falso positivo
                if baseline_length > 0:
                    size_diff = abs(content_length - baseline_length) / baseline_length
                    if size_diff < 0.1:  # Menos de 10% de diferença
                        is_false_positive = True
                        write_log(f"Arquivo {filename} parece ser falso positivo (tamanho similar ao 404 customizado)")

                # Se o content-type for HTML e o arquivo não deveria ser HTML, é suspeito
                if 'text/html' in content_type.lower():
                    # Arquivos que não deveriam ser HTML
                    non_html_extensions = ['.json', '.xml', '.config', '.txt', '.env', '.yml', '.yaml',
                                          '.properties', '.sql', '.bak', '.backup', '.old', '.copy']
                    if any(filename.lower().endswith(ext) for ext in non_html_extensions):
                        is_false_positive = True
                        write_log(f"Arquivo {filename} parece ser falso positivo (HTML retornado para arquivo não-HTML)")

            if is_false_positive:
                write_log(f"Arquivo {filename} não encontrado (falso positivo detectado). Status code: {response.status_code}")
                return {
                    'found': False,
                    'error': False,
                    'filename': filename,
                    'url': file_url,
                    'status_code': response.status_code
                }

            write_log(f"Arquivo {filename} encontrado. Status code: {response.status_code}")

            return {
                'found': True,
                'error': False,
                'filename': filename,
                'url': file_url,
                'status_code': response.status_code,
                'content_type': content_type,
                'content_length': content_length,
                'headers': dict(response.headers)
            }
        else:
            write_log(f"Arquivo {filename} não encontrado. Status code: {response.status_code}")
            return {
                'found': False,
                'error': False,
                'filename': filename,
                'url': file_url,
                'status_code': response.status_code
            }
            
    except requests.exceptions.Timeout:
        return {
            'found': False,
            'error': True,
            'filename': filename,
            'url': file_url,
            'error_message': 'Timeout'
        }
    except requests.exceptions.ConnectionError:
        return {
            'found': False,
            'error': True,
            'filename': filename,
            'url': file_url,
            'error_message': 'Erro de conexão'
        }
    except requests.exceptions.RequestException as e:
        return {
            'found': False,
            'error': True,
            'filename': filename,
            'url': file_url,
            'error_message': str(e)
        }




