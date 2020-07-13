from http.server import BaseHTTPRequestHandler, HTTPServer
import logging

response = "TEXT RESPONSE"
class MyHttpServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers() # Also calls flush_headers()
        encoded_content = response.encode("utf-8")
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

if __name__ == "__main__":
    portused = input("Set the port number:\n")
    response = input("Set the response:\n")
    run(port=int(portused))

