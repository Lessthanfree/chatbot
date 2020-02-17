from http.server import BaseHTTPRequestHandler, HTTPServer
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

def decode_post(data):
    data_str = data.decode('utf-8')
    print("Decoded post:", data_str)
    datad = html_msg_to_dict(data_str)
    return datad

class ChatbotServer(BaseHTTPRequestHandler):
    def start_chatbot(self):
        print("Starting the chatbot")
        print("disabled for now")
        # self.chatbot = Chatbot()

    def _get_bot_reply(self, info_dict):
        uid = info_dict.get("userID")
        msg = info_dict.get("message")
        logging.info("<SERVER GET BOT REPLY> USER <{}>:{}".format(uid, msg))
        # reply_obj = self.chatbot.get_bot_reply(uid, msg)
        reply_text = "You said: <" + msg + ">"
        reply_obj = ("Reply", {"A":reply_text})
        print("<SERVER> REPLY OBJ", reply_obj)
        return reply_obj
        
    def _set_response(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def do_GET(self):
        logging.info("GET request,\nPath: %s\nHeaders:\n%s\n", str(self.path), str(self.headers))
        self._set_response()
        self.wfile.write("GET request for {}".format(self.path).encode('utf-8'))

    def do_POST(self):
        content_length = int(self.headers['Content-Length']) # <--- Gets the size of data
        post_data = self.rfile.read(content_length) # <--- Gets the data itself
        decoded = decode_post(post_data)
        logging.info("POST request,\nPath: %s\nHeaders:\n%s\n\nBody:\n%s\n",
                str(self.path), str(self.headers), decoded)

        self._set_response()
        chatbot_reply = self._get_bot_reply(decoded)
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