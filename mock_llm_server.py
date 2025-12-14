from http.server import BaseHTTPRequestHandler, HTTPServer
import json

class MockLLMHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        # 1. Read the request body
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        print(f"\n[Klyve Request Received]\n{post_data.decode('utf-8')}\n")

        # 2. Prepare a fake OpenAI-style response
        response = {
            "choices": [
                {
                    "message": {
                        "content": "Success! Klyve connected to the mock server."
                    }
                }
            ]
        }

        # 3. Send response
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(response).encode('utf-8'))

if __name__ == '__main__':
    server_address = ('localhost', 1234)
    print("Starting Mock LLM Server on http://localhost:1234...")
    httpd = HTTPServer(server_address, MockLLMHandler)
    httpd.serve_forever()