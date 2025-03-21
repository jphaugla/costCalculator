import http.server
import socketserver
import argparse
import os

#  Change the working directory to the location of AuroraDynamic.html
os.chdir("../")
# Parse command-line arguments
parser = argparse.ArgumentParser(description="Simple HTTP Server with CORS support")
parser.add_argument("--port", type=int, default=8000, help="Specify the port number (default: 8000)")
args = parser.parse_args()

PORT = args.port

class CORSRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        super().end_headers()

if __name__ == '__main__':
    with socketserver.TCPServer(("", PORT), CORSRequestHandler) as httpd:
        print(f"Serving at port {PORT}")
        httpd.serve_forever()

