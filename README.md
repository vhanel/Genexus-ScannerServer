# ScannerServer

**ScannerServer** is a lightweight Python-based web vulnerability scanner that analyzes websites for security issues. It identifies web server types and detects exposed sensitive files through a simple RESTful API interface.

## 🚀 Features

- **Server Identification**: Detects web server types (Apache, Nginx, IIS, etc.) by analyzing HTTP headers
- **Exposed File Detection**: Checks for sensitive files like config files, backups, and credentials
- **Comprehensive File Database**: Includes checks for .NET, Java/Spring Boot, and generic dangerous files
- **REST API**: Simple endpoint for scanning any target URL
- **Detailed Scan Results**: Returns server info, found files count, and complete scan metadata

## 🛠️ Technologies Used

- Python 3.11+
- Flask
- Requests
- Docker (optional for containerized setup)

## ⚙️ How It Works

1. Send a POST request to `/ScanApp` with a target URL parameter
2. The scanner performs:
   - HTTP header analysis to identify the web server
   - Systematic checks for exposed sensitive files from the database
3. Returns a JSON response with:
   - Scan ID and timestamp
   - Server identification results
   - List of exposed files found
   - Complete scan metadata

## ▶️ Running the Project

### With Python

```bash
pip install -r requirements.txt
python app.py
```

The server will start on: [http://localhost:5000](http://localhost:5000)

### With Docker (optional)

If you're using Docker, you can build and run containers with your `Dockerfile` and `docker-compose.yml`.

```bash
docker build -t scanner-server .
docker run -p 5000:5000 scanner-server
```

## 🧪 Example Usage

### Using cURL

```bash
curl -X POST http://localhost:5000/ScanApp \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/login.aspx"}'
```

### Example Response

```json
{
  "scan_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2025-12-12T10:30:00",
  "target_url": "https://example.com/login.aspx",
  "server_info": {
    "server_type": "nginx",
    "version": "1.18.0"
  },
  "exposed_files": {
    "count": 2,
    "files": [
      "/web.config",
      "/.env"
    ]
  },
  "scan_duration": "5.2s"
}
```

## 🔒 Security Note

This tool is intended for **authorized security testing only**. Always ensure you have permission to scan the target website. Unauthorized scanning may be illegal.

## 📌 Future Plans

- Support for additional vulnerability checks (XSS, SQL injection, etc.)
- Rate limiting and concurrent scanning
- Export results to PDF/HTML reports
- Web UI for easier interaction
- Database storage for scan history
- Authentication and API keys

## 📄 License

Apache 2.0 – see the `LICENSE` file for details.

