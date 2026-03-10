#!/usr/bin/env python3
"""Sentence practice server for Hebrew vocabulary."""

import json
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from generator import generate_batch

PORT = 7749


class Handler(BaseHTTPRequestHandler):

    _STATIC = {
        '.html': 'text/html',
        '.js': 'text/javascript',
        '.json': 'application/json',
    }

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path in ('/', '/index.html'):
            self._serve_file('index.html', 'text/html')
        elif parsed.path == '/api/sentences':
            params = parse_qs(parsed.query)
            n = int(params.get('n', [20])[0])
            result = generate_batch(n)
            body = json.dumps(result, ensure_ascii=False).encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(body)
        else:
            # Serve static files (.js, .json)
            name = parsed.path.lstrip('/')
            ext = os.path.splitext(name)[1]
            if ext in self._STATIC:
                self._serve_file(name, self._STATIC[ext])
            else:
                self.send_response(404)
                self.end_headers()

    def _serve_file(self, name, ctype):
        base = os.path.dirname(os.path.abspath(__file__))
        try:
            with open(os.path.join(base, name), 'rb') as f:
                data = f.read()
            self.send_response(200)
            self.send_header('Content-Type', f'{ctype}; charset=utf-8')
            self.end_headers()
            self.wfile.write(data)
        except FileNotFoundError:
            self.send_response(404)
            self.end_headers()

    def log_message(self, fmt, *args):
        pass


if __name__ == '__main__':
    srv = HTTPServer(('localhost', PORT), Handler)
    print(f'http://localhost:{PORT}')
    srv.serve_forever()
