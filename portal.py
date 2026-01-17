import http.server
import socketserver
import socket
import os
import re
import qrcode
import sys
import urllib.parse
import math

# --- Configuration ---
PORT = 8000
UPLOAD_DIR = "received_files"

if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

def convert_size(size_bytes):
    if size_bytes == 0: return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return "%s %s" % (s, size_name[i])

# --- THE SCI-FI UI (Embedded directly to prevent errors) ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Portal Beam</title>
    <style>
        :root {
            --bg: #0b0b0f;
            --card-bg: rgba(23, 23, 29, 0.95);
            --primary: #0affff;
            --secondary: #7000ff;
            --text: #ffffff;
            --text-muted: #8b8b95;
            --font-main: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        }
        body {
            font-family: var(--font-main);
            background-color: var(--bg);
            color: var(--text);
            margin: 0;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            overflow-x: hidden;
            background-image: 
                linear-gradient(rgba(10, 255, 255, 0.03) 1px, transparent 1px),
                linear-gradient(90deg, rgba(10, 255, 255, 0.03) 1px, transparent 1px);
            background-size: 40px 40px;
            animation: gridMove 20s linear infinite;
        }
        @keyframes gridMove { 0% { background-position: 0 0; } 100% { background-position: 40px 40px; } }
        @keyframes scanline { 0% { transform: translateY(-100%); } 100% { transform: translateY(100%); } }
        @keyframes fadeInUp { from { opacity: 0; transform: translateY(30px); } to { opacity: 1; transform: translateY(0); } }
        
        .container { width: 90%; max-width: 480px; position: relative; }
        h1 {
            text-align: center; font-weight: 800; font-size: 3rem; margin-bottom: 40px;
            background: linear-gradient(135deg, var(--primary), #ffffff);
            -webkit-background-clip: text; background-clip: text; -webkit-text-fill-color: transparent;
            text-shadow: 0 0 30px rgba(10, 255, 255, 0.3); animation: fadeInUp 0.8s ease-out;
        }
        .card {
            background: var(--card-bg); backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px);
            border-radius: 24px; padding: 30px; margin-bottom: 25px;
            border: 1px solid rgba(255, 255, 255, 0.08); box-shadow: 0 20px 50px rgba(0,0,0,0.5);
            position: relative; overflow: hidden; animation: fadeInUp 0.8s ease-out 0.2s backwards;
        }
        .card::after {
            content: ''; position: absolute; top: 0; left: 0; right: 0; bottom: 0;
            background: linear-gradient(to bottom, transparent, rgba(10, 255, 255, 0.03), transparent);
            transform: translateY(-100%); animation: scanline 6s linear infinite; pointer-events: none;
        }
        .card-header {
            font-size: 0.9rem; text-transform: uppercase; letter-spacing: 2px; color: var(--text-muted);
            margin-bottom: 20px; display: flex; align-items: center; gap: 10px;
        }
        .accent-dot { width: 8px; height: 8px; background: var(--primary); border-radius: 50%; box-shadow: 0 0 10px var(--primary); }
        
        .upload-zone {
            border: 2px dashed rgba(255,255,255,0.1); border-radius: 16px; padding: 40px 20px;
            text-align: center; cursor: pointer; transition: 0.3s; position: relative; background: rgba(0,0,0,0.2);
        }
        .upload-zone input { position: absolute; width: 100%; height: 100%; top: 0; left: 0; opacity: 0; cursor: pointer; }
        .zone-icon { font-size: 2.5rem; margin-bottom: 15px; filter: drop-shadow(0 0 15px rgba(10, 255, 255, 0.4)); }
        .zone-text { font-size: 0.95rem; color: var(--text-muted); }
        #file-display {
            margin-top: 15px; padding: 12px; background: rgba(10, 255, 255, 0.1);
            border: 1px solid rgba(10, 255, 255, 0.3); border-radius: 8px; color: var(--primary); display: none;
        }
        .btn {
            width: 100%; background: var(--primary); color: #000; padding: 18px; border: none;
            border-radius: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: 1px;
            cursor: pointer; margin-top: 25px; transition: 0.3s;
            clip-path: polygon(10px 0, 100% 0, 100% calc(100% - 10px), calc(100% - 10px) 100%, 0 100%, 0 10px);
        }
        .btn:hover { box-shadow: 0 0 30px rgba(10, 255, 255, 0.4); transform: translateY(-2px); }
        
        .file-list { display: flex; flex-direction: column; gap: 12px; }
        .file-item {
            display: flex; justify-content: space-between; align-items: center; background: rgba(255,255,255,0.03);
            padding: 16px; border-radius: 12px; text-decoration: none; color: var(--text); border-left: 3px solid transparent; transition: 0.2s;
        }
        .file-item:hover { background: rgba(255,255,255,0.06); border-left: 3px solid var(--primary); padding-left: 20px; }
        .file-name { font-weight: 500; }
        .file-size { font-size: 0.8rem; color: var(--text-muted); }
        .download-icon { color: var(--text-muted); }
        .file-item:hover .download-icon { color: var(--primary); }
        .empty-state { text-align: center; color: var(--text-muted); padding: 30px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>PORTAL</h1>
        <div class="card">
            <div class="card-header"><div class="accent-dot"></div> UPLINK TERMINAL</div>
            <form action="/upload" method="post" enctype="multipart/form-data">
                <div class="upload-zone" id="drop-zone">
                    <div class="zone-icon">📡</div>
                    <div class="zone-text" id="zone-text">Initiate File Sequence</div>
                    <input type="file" name="file" id="file-input" required>
                </div>
                <div id="file-display">No Data Selected</div>
                <button type="submit" class="btn">ENGAGE TRANSFER</button>
            </form>
        </div>
        <div class="card">
            <div class="card-header"><div class="accent-dot" style="background:var(--secondary); box-shadow:0 0 10px var(--secondary);"></div> SECURE STORAGE</div>
            
            {file_list}
            
        </div>
    </div>
    <script>
        const fileInput = document.getElementById('file-input');
        const fileDisplay = document.getElementById('file-display');
        const zoneText = document.getElementById('zone-text');
        const dropZone = document.getElementById('drop-zone');
        
        fileInput.addEventListener('change', function() {
            if (this.files && this.files.length > 0) {
                fileDisplay.style.display = 'block';
                fileDisplay.textContent = "BUFFER: " + this.files[0].name;
                dropZone.style.borderColor = 'var(--primary)';
                dropZone.style.background = 'rgba(10, 255, 255, 0.05)';
                zoneText.textContent = "Target Acquired";
            }
        });
    </script>
</body>
</html>
"""

class PortalHandler(http.server.SimpleHTTPRequestHandler):
    
    def get_file_list_html(self):
        """Generates the HTML list items."""
        try:
            files = sorted(os.listdir(UPLOAD_DIR))
        except Exception:
            return "<div class='empty-state'>Error reading storage.</div>"

        if not files:
            return "<div class='empty-state'>// NO DATA FRAGMENTS FOUND //</div>"
        
        html_list = "<div class='file-list'>"
        for f in files:
            if f.startswith('.'): continue
            
            filepath = os.path.join(UPLOAD_DIR, f)
            filesize = convert_size(os.path.getsize(filepath))
            safe_filename = urllib.parse.quote(f)
            
            download_icon = """<svg width="24" height="24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>"""

            html_list += f"""
            <a href='/{UPLOAD_DIR}/{safe_filename}' download class="file-item">
                <div class="file-info">
                    <div class="file-name">{f}</div>
                    <div class="file-size">{filesize}</div>
                </div>
                <div class="download-icon">{download_icon}</div>
            </a>
            """
        html_list += "</div>"
        return html_list

    def do_GET(self):
        if self.path == '/':
            # Generate the list
            list_content = self.get_file_list_html()
            
            # Inject it directly into the variable using standard Python formatting
            final_html = HTML_TEMPLATE.replace("{file_list}", list_content)
            
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(final_html.encode('utf-8'))
        else:
            super().do_GET()

    def do_POST(self):
        if self.path == '/upload':
            try:
                content_type = self.headers['Content-Type']
                if not content_type: return
                boundary = content_type.split("=")[1].encode()
                remain_bytes = int(self.headers['Content-Length'])
                line = self.rfile.readline()
                remain_bytes -= len(line)
                if not boundary in line: return
                line = self.rfile.readline()
                remain_bytes -= len(line)
                filename = re.findall(r'filename="(.+)"', line.decode('utf-8'))[0]
                if not filename: return
                filename = os.path.basename(filename)
                path = os.path.join(UPLOAD_DIR, filename)
                line = self.rfile.readline(); remain_bytes -= len(line)
                line = self.rfile.readline(); remain_bytes -= len(line)
                with open(path, 'wb') as out:
                    pre_line = self.rfile.readline()
                    remain_bytes -= len(pre_line)
                    while remain_bytes > 0:
                        line = self.rfile.readline()
                        remain_bytes -= len(line)
                        if boundary in line:
                            pre_line = pre_line[0:-1] 
                            if pre_line.endswith(b'\r'): pre_line = pre_line[0:-1]
                            out.write(pre_line)
                            break
                        else:
                            out.write(pre_line)
                            pre_line = line
                self.send_response(303)
                self.send_header("Location", "/")
                self.end_headers()
                print(f"[*] Received: {filename}")
            except Exception as e:
                print(f"[!] Error: {e}")

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

def main():
    IP = get_local_ip()
    URL = f"http://{IP}:{PORT}"
    
    print(f"\n --- PORTAL V4 (Single File) ---")
    print(f" [*] Server:   {URL}")
    print(f" [*] Storage:  {os.path.abspath(UPLOAD_DIR)}")
    
    qr = qrcode.QRCode()
    qr.add_data(URL)
    qr.make(fit=True)
    qr.print_ascii(invert=True)

    try:
        socketserver.TCPServer.allow_reuse_address = True
        with socketserver.TCPServer(("", PORT), PortalHandler) as httpd:
            print(f"\n[*] Listening... (Ctrl+C to stop)")
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[*] Portal closing.")

if __name__ == "__main__":
    main()