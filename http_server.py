import logging
import time

from http.server import BaseHTTPRequestHandler, HTTPServer
from http_utils import decode_post
from urllib import parse
from chatbot import Chatbot


# ! NOTE ! http.server security is low

# A server that recieves HTTP requests from the WeChat servers and breaks down the message to be fed into the chatbot.
# Also sends messages back to the WeChat server to reply AND/OR sends a message to internal servers to trigger some action (log database info)

ENCODING_USED = "utf-8"

class ChatbotServer(BaseHTTPRequestHandler):
    # This cannot be put in 
    chatbot_started = False
    def start_chatbot(self):
        print("Starting the chatbot")
        chatbot_resource_filename = "wechat_chatbot_resource.json"
        # print("disabled for now")
        self.chatbot = Chatbot()
        self.chatbot.start_bot(chatbot_resource_filename, backend_read=False)
        self.chatbot_started = True

    def format_reply_xml(self, msg_info, content):
        reply = (
            "<xml>"
            "<ToUserName><![CDATA[%s]]></ToUserName>"
            "<FromUserName><![CDATA[%s]]></FromUserName>"
            "<CreateTime>%s</CreateTime>"
            "<MsgType><![CDATA[text]]></MsgType>"
            "<Content><![CDATA[%s]]></Content>"
            "</xml>"
        ) % (
        msg_info['FromUserName'], 
        msg_info['ToUserName'],
        time.gmtime(),
        content
        )
        # Because its a reply, the from and to are swapped
        return reply.encode(ENCODING_USED)

    def _get_bot_reply(self, info_dict):
        if not self.chatbot_started:
            self.start_chatbot()
        uid = info_dict.get("FromUserName", "")
        msg = info_dict.get("Content", "")
        logging.info("<SERVER GET BOT REPLY> USER <{}>:{}".format(uid, msg))
        reply_text = self.chatbot.get_bot_reply(uid, msg)
        return reply_text
        
    def _set_response(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers() # Also calls flush_headers()

    # Puts all the url query arguments into a dict
    def _get_url_dict(self):
        # Because parse_qs creates the values as a list
        def flatten_qd(qd):
            out = {}
            for k, v in qd.items():
                if len(v) == 1:
                    out[k] = v[0] 
            return out

        query = parse.urlparse(self.path).query # In a normal http request this is the stuff after the url
        query_dict = parse.parse_qs(query)

        d = flatten_qd(query_dict)
        return d
    
    def do_GET(self):
        def is_from_wechat(req_dict):
            wx_req_comp = ["signature", "timestamp", "nonce", "echostr"]
            rd_keys = req_dict.keys()
            for c in wx_req_comp:
                if not c in rd_keys:
                    logging.info("GET is not from WeChat. {} is missing".format(c))
                    return False
            return True
            
        def send_wechat_auth(req_dict):
            # isolate echostr
            echostr = req_dict.get("echostr")
            print("Sending auth code: {}".format(echostr))
            self._set_response()
            auth_code = echostr.encode(ENCODING_USED)
            self.wfile.write(auth_code)

        req_dict = self._get_url_dict()
        logging.info("GET request,\nPath: %s\nHeaders:\n%s\n", str(req_dict), str(self.headers))
        
        if is_from_wechat(req_dict):
            logging.info("GET request is from WeChat!")
            send_wechat_auth(req_dict)
            return

        
        self._set_response()
        http_get_response = "GET request for {}".format(self.path).encode(ENCODING_USED)
        logging.info("GET response:\n{}".format(http_get_response))
        self.wfile.write(http_get_response)

    def do_POST(self):
        content_length = int(self.headers['Content-Length']) # <--- Gets the size of data
        post_data_raw = self.rfile.read(content_length) # <--- Gets the data itself
        request_info = decode_post(post_data_raw)

        logging.info("POST request,\nPath: %s\nHeaders:\n%s\n\nBody:\n%s\n",
                str(self.path), str(self.headers), request_info)

        self._set_response()
        chatbot_reply_str = self._get_bot_reply(request_info)
        post_reply = self.format_reply_xml(request_info, chatbot_reply_str)
        logging.info("POST reponse:\n{}".format(chatbot_reply_str))
        self.wfile.write(post_reply)

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