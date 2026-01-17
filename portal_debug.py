import http.server
import socketserver
import socket
import os
import re
import qrcode
import sys
import urllib.parse
import math

# --- Config ---
PORT = 8000
UPLOAD_DIR = "received_files"
HTML_FILE = "index.html"

if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

def convert_size(size_bytes):
    if size_bytes == 0: return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return "%s %s" % (s, size_name[i])

class PortalHandler(http.server.SimpleHTTPRequestHandler):
    
    def get_file_list_html(self):
        """Generates the HTML list items."""
        print(f"[*] Generating file list from: {UPLOAD_DIR}") # DEBUG
        try:
            files = sorted(os.listdir(UPLOAD_DIR))
        except Exception as e:
            print(f"[!] Error reading directory: {e}")
            return "<p>Error reading directory</p>"

        if not files:
            print("[*] Directory is empty.") # DEBUG
            return "<div class='empty-state'><p>No files shared yet.</p></div>"
        
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
                <div class="icon-download">{download_icon}</div>
            </a>
            """
        html_list += "</div>"
        return html_list

    def do_GET(self):
        if self.path == '/':
            print(f"[*] Request received for Index Page") # DEBUG
            try:
                # 1. Read HTML
                if not os.path.exists(HTML_FILE):
                    print(f"[!] ERROR: Could not find {HTML_FILE} in {os.getcwd()}")
                    self.send_response(404)
                    self.end_headers()
                    self.wfile.write(b"Error: index.html missing!")
                    return

                with open(HTML_FILE, 'r', encoding='utf-8') as f:
                    html_content = f.read()
                
                # 2. Check for Tag
                tag = ''
                if tag not in html_content:
                    print(f"[!] CRITICAL ERROR: The tag {tag} was NOT found in index.html")
                    print("[!] Please check your HTML file.")
                else:
                    print(f"[*] Success: Found injection tag.")
                
                # 3. Generate and Inject
                file_list_content = self.get_file_list_html()
                final_html = html_content.replace(tag, file_list_content)
                
                self.send_response(200)
                self.send_header("Content-type", "text/html")
                # TELL BROWSER NOT TO CACHE
                self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
                self.send_header("Pragma", "no-cache")
                self.send_header("Expires", "0")
                self.end_headers()
                self.wfile.write(final_html.encode('utf-8'))
                
            except Exception as e:
                print(f"[!] Server Error: {e}")
        else:
            super().do_GET()

    def do_POST(self):
        # (Same upload code as before)
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
    print(f"\n --- PORTAL DEBUG MODE ---")
    print(f" [*] Server:   {URL}")
    print(f" [*] HTML File: {os.path.abspath(HTML_FILE)}")
    
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