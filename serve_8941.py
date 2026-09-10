"""Threaded preview server for 说文解字·汉字通 on http://127.0.0.1:8941
Serves the project dir. Threading so the browser can pull index.html (13.6MB)
+ dataset.bin (9.6MB) + stroke_data.json (21MB) concurrently without the
single-threaded server stalling/emptying dataset.bin (which broke the evolution
charts by making CDS_READER null).
"""
import os
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)


class Handler(SimpleHTTPRequestHandler):
    def end_headers(self):
        # always fresh: user rebuilds index.html and must see it on refresh
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    httpd = ThreadingHTTPServer(("127.0.0.1", 8941), Handler)
    print("serving", ROOT, "on http://127.0.0.1:8941")
    httpd.serve_forever()
