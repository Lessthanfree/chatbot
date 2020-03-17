import logging
import time

from chatbot import Chatbot
from http_auth_control import AuthController
from http.server import BaseHTTPRequestHandler, HTTPServer
from http_utils import decode_post, ENCODING_USED
from http_wx_auth import OpenIDMasterManager
from http_request_interpreter import RequestBoss
from urllib import parse

# ! NOTE ! http.server security is low

# A server that recieves HTTP requests from the WeChat servers and breaks down the message to be fed into the chatbot.
# Also sends messages back to the WeChat server to reply AND/OR sends a message to internal servers to trigger some action (log database info)

def start_chatbot():
    print("Starting the chatbot")
    chatbot_resource_filename = "wechat_chatbot_resource.json"
    chatbot = Chatbot()
    chatbot.start_bot(chatbot_resource_filename, backend_read=False) # Turn off backend read cuz no SQL to read
    return chatbot

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
        
    def _set_response(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers() # Also calls flush_headers()
    
    def get_encoded_xml(self, response_action, og_request_info):
        raw_xml = self.rb.get_response_xml(response_action, og_request_info)
        encoded = raw_xml.encode(ENCODING_USED)
        return encoded

    def do_GET(self):
        logging.info("GET request for {}".format(self.path).encode(ENCODING_USED))
        reply_flag, response_content = self.rb.interpret_get(self.path, self.headers)
        if reply_flag:
            self._set_response()
            logging.info("GET response:\n{}".format(response_content))
            response_content.encode(ENCODING_USED)
            self.wfile.write(response_content)

    def do_POST(self):
        def send_post_request(req_info, encoded_content):
            self._set_response()
            self.wfile.write(encoded_content)

        content_length = int(self.headers['Content-Length']) # <--- Gets the size of data
        post_data_raw = self.rfile.read(content_length) # <--- Gets the data itself
        og_request_info = decode_post(post_data_raw)

        logging.info("POST request,\nPath: %s\nHeaders:\n%s\n\nBody:\n%s\n",
                str(self.path), str(self.headers), og_request_info)

        response_action = self._get_bot_response(og_request_info)
        encoded = self.get_encoded_xml(response_action, og_request_info)
        send_post_request(og_request_info, encoded)
        
def run(server_class=HTTPServer, handler_class=ChatbotServer, port=8080):
    logging.basicConfig(level=logging.INFO)
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    logging.info('Starting httpd on {}...\n'.format(server_address))
    try:
        print("Serving forever...")
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    logging.info('Stopping httpd...\n')

if __name__ == '__main__':
    from sys import argv

    if len(argv) == 2:
        run(port=int(argv[1]))
    else:
        run()