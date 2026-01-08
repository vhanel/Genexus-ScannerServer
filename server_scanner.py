import requests
import urllib3
import re

# Desabilita warnings de SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def identify_server(url):
    """
    Identifica o servidor web fazendo uma requisição HTTP e analisando os headers

    Args:
        url: URL do site a ser analisado

    Returns:
        dict: Informações sobre o servidor identificado
    """
    try:
        # Adiciona esquema http:// se não estiver presente
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url

        # Headers para simular um navegador real
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }

        # Faz a requisição HTTP com timeout (conexão: 2s, leitura: 3s)
        response = requests.get(url, timeout=(2, 3), allow_redirects=True, headers=headers, verify=False)

        # Verifica se o status code indica sucesso (2xx ou 3xx)
        if response.status_code >= 400:
            return {
                'success': False,
                'error': f'URL retornou status code {response.status_code}',
                'status_code': response.status_code
            }

        # Obtém o header 'Server'
        server_header = response.headers.get('Server', 'Não identificado')

        # Identifica o tipo de servidor baseado no header
        server_type = identify_server_type(server_header, response.headers)

        # Verifica se é um site Genexus
        is_genexus = check_genexus(url, response)

        return {
            'success': True,
            'server_header': server_header,
            'server_type': server_type,
            'status_code': response.status_code,
            'url_final': response.url,
            'headers': dict(response.headers),
            'is_genexus': is_genexus
        }

    except requests.exceptions.Timeout:
        return {
            'success': False,
            'error': 'Connection timeout - server took too long to respond'
        }
    except requests.exceptions.ConnectionError as e:
        return {
            'success': False,
            'error': f'Connection error - unable to reach server'
        }
    except requests.exceptions.RequestException as e:
        return {
            'success': False,
            'error': f'Request error: {str(e)}'
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'Unexpected error: {str(e)}'
        }


def identify_server_type(server_header, headers):
    """
    Identifica o tipo de servidor baseado no header e outros indicadores
    
    Args:
        server_header: Valor do header 'Server'
        headers: Todos os headers da resposta
        
    Returns:
        str: Tipo de servidor identificado
    """
    server_lower = server_header.lower()
    
    # Verifica IIS
    if 'iis' in server_lower or 'microsoft' in server_lower:
        return 'Microsoft IIS'
    
    # Verifica Apache
    elif 'apache' in server_lower:
        if 'tomcat' in server_lower:
            return 'Apache Tomcat'
        else:
            return 'Apache'
    
    # Verifica Nginx
    elif 'nginx' in server_lower:
        return 'Nginx'
    
    # Verifica Tomcat standalone
    elif 'tomcat' in server_lower:
        return 'Apache Tomcat'
    
    # Verifica outros servidores comuns
    elif 'cloudflare' in server_lower:
        return 'Cloudflare (Proxy/CDN)'
    elif 'litespeed' in server_lower:
        return 'LiteSpeed'
    elif 'caddy' in server_lower:
        return 'Caddy'
    elif 'gunicorn' in server_lower:
        return 'Gunicorn'
    elif 'werkzeug' in server_lower:
        return 'Werkzeug (Flask Development Server)'
    
    # Verifica headers adicionais para identificação
    if 'X-Powered-By' in headers:
        powered_by = headers['X-Powered-By'].lower()
        if 'asp.net' in powered_by:
            return 'Microsoft IIS (ASP.NET)'
        elif 'php' in powered_by:
            return f"{server_header} (PHP)"
    
    # Se não identificou, retorna o header original
    if server_header != 'Não identificado':
        return server_header
    else:
        return 'Servidor não identificado (header oculto)'


def check_genexus(url, response=None):
    """
    Verifica se o site é um aplicativo Genexus procurando por gxgral.js

    Args:
        url: URL base do site
        response: Resposta HTTP já obtida (opcional)

    Returns:
        bool: True se for Genexus, False caso contrário
    """
    try:
        # Headers para simular um navegador real
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        }

        # Se não temos a resposta, faz a requisição
        if response is None:
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url

            response = requests.get(url, timeout=(2, 3), allow_redirects=True, headers=headers, verify=False)

        # Verifica se a resposta é HTML
        content_type = response.headers.get('Content-Type', '').lower()

        if 'text/html' in content_type:
            # Procura por gxgral.js no conteúdo HTML
            html_content = response.text

            # Padrões para encontrar gxgral.js
            patterns = [
                r'gxgral\.js',
                r'src=["\'].*?gxgral\.js.*?["\']',
                r'<script.*?gxgral\.js.*?</script>',
            ]

            for pattern in patterns:
                if re.search(pattern, html_content, re.IGNORECASE):
                    print(f"[DEBUG] Genexus detectado: gxgral.js encontrado no HTML")
                    return True

        # Verifica se o arquivo gxgral.js existe diretamente na raiz
        base_url = response.url if response else url

        # Remove path da URL para pegar apenas a raiz
        from urllib.parse import urlparse, urljoin
        parsed = urlparse(base_url)
        root_url = f"{parsed.scheme}://{parsed.netloc}/"

        # Testa se gxgral.js existe na raiz
        gxgral_url = urljoin(root_url, 'gxgral.js')

        try:
            gxgral_response = requests.head(gxgral_url, timeout=(2, 3), headers=headers, verify=False, allow_redirects=True)
            if gxgral_response.status_code == 200:
                print(f"[DEBUG] Genexus detectado: gxgral.js encontrado em {gxgral_url}")
                return True
        except:
            pass

        return False

    except Exception as e:
        print(f"[DEBUG] Erro ao verificar Genexus: {str(e)}")
        return False

