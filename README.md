# ScannerServer

**ScannerServer** is a lightweight Python-based web vulnerability scanner that analyzes websites for security issues. It identifies web server types and detects exposed sensitive files through a simple web interface and RESTful API.

## Features

- **Web Interface**: User-friendly web UI for easy scanning and result visualization
- **Server Identification**: Detects web server types (Apache, Nginx, IIS, etc.) by analyzing HTTP headers
- **Genexus Detection**: Automatically identifies Genexus applications by detecting gxgral.js
- **Exposed File Detection**: Checks for sensitive files like config files, backups, and credentials
- **Comprehensive File Database**: Includes checks for .NET, Java/Spring Boot, Genexus, and generic dangerous files
- **Smart Genexus Scanning**: When gxgral.js is found, automatically searches for related Genexus files
- **REST API**: Simple endpoint for scanning any target URL
- **Scan Statistics**: Track and view statistics of all scans performed
- **Detailed Scan Results**: Returns server info, found files count, and complete scan metadata

## Technologies Used

- Python 3.11+
- Flask
- Requests
- Docker (optional for containerized setup)

## How It Works

### Web Interface
1. Access the web interface at `http://localhost:5000`
2. Enter the target URL in the input field
3. Click "Scan" to start the analysis
4. View detailed results including:
   - Server type and headers
   - Genexus detection status
   - List of exposed files found
   - Complete scan metadata

### API
1. Send a POST request to `/ScanApp` with a target URL parameter
2. The scanner performs:
   - HTTP header analysis to identify the web server
   - Genexus detection by searching for gxgral.js
   - Systematic checks for exposed sensitive files from the database
   - Additional Genexus file checks if gxgral.js is found
3. Returns a JSON response with:
   - Scan ID and description
   - Server identification results
   - Genexus detection status
   - List of exposed files found
   - Complete scan metadata

## Running the Project

### With Python

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
python app.py
```

The server will start on: **[http://localhost:5000](http://localhost:5000)**

### With Docker (optional)

If you're using Docker, you can build and run containers with your `Dockerfile` and `docker-compose.yml`.

```bash
docker build -t scanner-server .
docker run -p 5000:5000 scanner-server
```

## Accessing the Application

### Web Interface
Once the server is running, open your browser and navigate to:

**[http://localhost:5000](http://localhost:5000)**

The web interface provides:
- Simple URL input field for scanning
- Real-time scan results display
- Server information and Genexus detection
- List of exposed files with details
- Scan statistics dashboard

### API Endpoints

- **POST `/ScanApp`** - Perform a security scan
- **GET `/stats`** - Get scan statistics

## Example Usage

### Using the Web Interface

1. Open your browser and go to `http://localhost:5000`
2. Enter a URL (e.g., `https://example.com/login.aspx`)
3. Click the "Scan" button
4. View the results displayed on the page

### Using cURL (API)

```bash
curl -X POST http://localhost:5000/ScanApp \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/login.aspx"}'
```

### Example API Response

```json
{
  "ID": "550e8400-e29b-41d4-a716-446655440000",
  "Description": "Scan completo realizado. Servidor: Microsoft IIS (Genexus) | 3 arquivo(s) exposto(s)",
  "URL": "https://example.com/login.aspx",
  "ServerInfo": {
    "success": true,
    "server_header": "Microsoft-IIS/10.0",
    "server_type": "Microsoft IIS",
    "status_code": 200,
    "url_final": "https://example.com/login.aspx",
    "is_genexus": true
  },
  "FilesInfo": {
    "success": true,
    "base_url": "https://example.com/login.aspx",
    "total_checked": 50,
    "found_count": 3,
    "found_files": [
      {
        "found": true,
        "filename": "gxgral.js",
        "url": "https://example.com/gxgral.js",
        "status_code": 200
      }
    ]
  }
}
```

### Getting Scan Statistics

```bash
curl http://localhost:5000/stats
```

## Scan Statistics

The application tracks all scans performed and provides statistics through:
- **Web Interface**: View statistics dashboard at the bottom of the main page
- **API Endpoint**: GET `/stats` returns JSON with scan statistics

Statistics include:
- Total number of scans performed
- Total files found across all scans
- Most scanned domains
- Scan history with timestamps

## Security Note

This tool is intended for **authorized security testing only**. Always ensure you have permission to scan the target website. Unauthorized scanning may be illegal.

## Future Plans

- Support for additional vulnerability checks (XSS, SQL injection, etc.)
- Rate limiting and concurrent scanning
- Export results to PDF/HTML reports
- Enhanced Genexus detection (identify .NET vs Java versions)
- Database storage for scan history
- Authentication and API keys
- Scheduled scanning capabilities

## License

Apache 2.0 – see the `LICENSE` file for details.
