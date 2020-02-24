from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib import parse
# from chatbot import Chatbot
import logging

# A server that recieves HTTP requests from the WeChat servers and breaks down the message to be fed into the chatbot.
# Also sends messages back to the WeChat server to reply AND/OR sends a message to internal servers to trigger some action (log database info)

# Converts "A=B&C=D" to {'A':B, 'C':D}
def html_msg_to_dict(hmsg):
    hmsg = "'" + hmsg
    hmsg = hmsg.replace("&", "', '")
    hmsg = hmsg.replace("=", "' :'")
    hmsg = hmsg + "'"
    hmsg_str = "{" + hmsg + "}"
    c_dict = eval(hmsg_str)
    print("CDICT", c_dict)
    return c_dict

def decode_post_json(data):
    decoded_str = data.decode('utf-8')
    print("Decoded post:", decoded_str)
    data_d = eval(decoded_str)
    print("IS dict:", isinstance(data_d, dict))
    print("IS set:", isinstance(data_d, set))
    return data_d

class ChatbotServer(BaseHTTPRequestHandler):
    def start_chatbot(self):
        print("Starting the chatbot")
        print("disabled for now")
        # self.chatbot = Chatbot()

    def _get_bot_reply(self, info_dict):
        uid = info_dict.get("FromUserName", "")
        msg = info_dict.get("Content", "")
        logging.info("<SERVER GET BOT REPLY> USER <{}>:{}".format(uid, msg))
        # reply_obj = self.chatbot.get_bot_reply(uid, msg)
        reply_text = "You said: <" + msg + ">"
        reply_obj = (reply_text, {"A":50.0})
        print("<SERVER> REPLY OBJ", reply_obj)
        return reply_obj
        
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
        print("gud FINAL DICT", d)
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
            auth_code = echostr.encode("utf-8")
            self.wfile.write(auth_code)

        req_dict = self._get_url_dict()
        logging.info("GET request,\nPath: %s\nHeaders:\n%s\n", str(req_dict), str(self.headers))
        
        if is_from_wechat(req_dict):
            logging.info("GET request is from WeChat!")
            send_wechat_auth(req_dict)
            return

        
        self._set_response()
        http_get_response = "GET request for {}".format(self.path).encode('utf-8')
        logging.info("GET response:\n{}".format(http_get_response))
        self.wfile.write(http_get_response)

    def do_POST(self):
        content_length = int(self.headers['Content-Length']) # <--- Gets the size of data
        post_data = self.rfile.read(content_length) # <--- Gets the data itself
        decoded = decode_post_json(post_data)
        logging.info("POST request,\nPath: %s\nHeaders:\n%s\n\nBody:\n%s\n",
                str(self.path), str(self.headers), decoded)

        self._set_response()
        chatbot_reply, breakdown = self._get_bot_reply(decoded)
        self.wfile.write("POST REPLY: {}".format(chatbot_reply).encode('utf-8'))

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