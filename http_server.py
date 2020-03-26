import logging
import time

from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib import parse

from chatbot.chatbot import Chatbot # Defined in ./chatbot
from http_files_utils import get_file_as_bytes
from http_request_interpreter import RequestBoss
from http_utils import ENCODING_USED, decode_post

# ! NOTE ! http.server security is low

# A server that recieves HTTP requests from the WeChat servers and breaks down the message to be fed into the chatbot.
# Also sends messages back to the WeChat server to reply AND/OR sends a message to internal servers to trigger some action (log database info)

def start_chatbot():
    print("Starting the chatbot")
    chatbot_resource_filename = "wechat_chatbot_resource.json"
    local_chatbot = Chatbot()
    local_chatbot.start_bot(chatbot_resource_filename, backend_read=False) # Turn off backend read cuz no SQL to read
    return local_chatbot

class ChatbotServer(BaseHTTPRequestHandler):
    # This cannot be put in 
    chatbot = start_chatbot()
    rb = RequestBoss()
    
    # Expects a ResponseAction
    def _get_bot_response(self, post_info_dict):
        uid = post_info_dict.get("FromUserName", "")
        msg = post_info_dict.get("Content", "")
        logging.info("<SERVER GET BOT REPLY> USER <{}>:{}".format(uid, msg))
        return self.chatbot.get_bot_response(uid, msg)
        
    def _default_GET_response(self):
        INDEX_PAGE_PATH = "/index.html"
        # Empty path = "/"
        if len(self.path) > 1:
            # This is the default GET that will return any file as text
            filestrem = get_file_as_bytes(self.path)
            if not filestrem:
                self._set_not_found_response()
                return            

            self._set_text_response()
            self.wfile.write(filestrem) # Filestream is already encoded

        else:
            # Returns redirect to index.html
            self._set_redirect_response(INDEX_PAGE_PATH)

    def _set_not_found_response(self):
        self.send_response(404)
        self.end_headers()

    def _set_text_response(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers() # Also calls flush_headers()

    def _set_redirect_response(self, redirect_url):
        self.send_response(303) # Code: "See Other". 301 does not work, because it just changes the subdomain.
        self.send_header('Location', redirect_url)
        self.end_headers() # Also calls flush_headers()
    
    def get_encoded_xml(self, response_action, post_req_info):
        raw_xml = self.rb.interpret_post(response_action, post_req_info)
        encoded = raw_xml.encode(ENCODING_USED)
        return encoded

    def do_GET(self):
        logging.debug("GET request for {}".format(self.path).encode(ENCODING_USED))
        reply_flag, response_content = self.rb.interpret_get(self.path, self.headers)
        
        if reply_flag == "text":
            self._set_text_response()
            logging.info("GET response:\n{}".format(response_content))
            e_content = response_content.encode(ENCODING_USED)
            self.wfile.write(e_content)

        elif reply_flag == "redirect":
            logging.info("Redirecting GET request")
            self._set_redirect_response(response_content)    
        
        else:        
            logging.info("<no_action> Calling the default GET response:\n{}".format(response_content))
            self._default_GET_response()            

    def do_POST(self):
        def send_post_request(req_info, encoded_content):
            self._set_text_response()
            self.wfile.write(encoded_content)

        content_length = int(self.headers['Content-Length']) # <--- Gets the size of data
        post_data_raw = self.rfile.read(content_length) # <--- Gets the data itself
        post_req_info = decode_post(post_data_raw)

        logging.info("POST request,\nPath: %s\nHeaders:\n%s\n\nBody:\n%s\n",
                str(self.path), str(self.headers), post_req_info)

        response_action = self._get_bot_response(post_req_info)
        encoded = self.get_encoded_xml(response_action, post_req_info)
        send_post_request(post_req_info, encoded)
        

# The main function to run a server for real
def run(server_class=HTTPServer, handler_class=ChatbotServer, port=8080):
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

if __name__ == '__main__':
    from sys import argv

    if len(argv) == 2:
        run(port=int(argv[1]))
    else:
        run()
