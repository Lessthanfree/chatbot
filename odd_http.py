from http.server import BaseHTTPRequestHandler, HTTPServer
import logging

class MyHttpServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers() # Also calls flush_headers()
        encoded_content = "TEXT RESPONSE".encode("utf-8")
        self.wfile.write(encoded_content)

def run(server_class=HTTPServer, handler_class=MyHttpServer, port=8080):
    logging_level = logging.INFO # Others include logging.DEBUG, logging.WARNING 

    logging.basicConfig(level=logging_level)
    server_address = ('0.0.0.0', port)
    httpd = server_class(server_address, handler_class)
    logging.info('Starting http server on {}...\n'.format(server_address))
    try:
        print("Serving forever on localhost:{}...".format(port))
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    logging.critical('Stopping http server...\n')

run()