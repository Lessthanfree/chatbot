import logging
import requests
import urllib.parse as parse

from xml.etree import ElementTree

ENCODING_USED = "utf-8"

# Class to handle the sending of simple GET and POST requests
class RequestSender:
    # Returns a Request object
    def send_GET(self, url, req_params = ""):
        param_dict = {
            "body":req_params
        }
        return requests.get(url, params=param_dict)

    # Returns a Request object
    def send_POST(self, url, data = {}):
        headers = {'Content-Type': 'text/html'}
        e_data = data.encode(ENCODING_USED)
        return requests.post(url=url, data=e_data, headers = headers)

############# HTTP Request utils #############
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

# Puts all the url query arguments into a dict
def url_path_to_dict(url_path):
    # Because parse_qs creates the values as a list
    def flatten_qd(qd):
        out = {}
        for k, v in qd.items():
            if len(v) == 1:
                out[k] = v[0] 
        return out

    query = parse.urlparse(url_path).query # In a normal http request this is the stuff after the url
    query_dict = parse.parse_qs(query)

    d = flatten_qd(query_dict)
    return d

def get_req_sender(r):
    rsp = r.get("FromUserName", False)
    if not rsp:
        raise Exception("Request {} has no FromUserName".format(r))
    return rsp

############# DATA UTILITIES #############
# Wechat can send data in the form of XML or JSON.
# Takes in a string of bytes (encoded)
# Returns a dict
def decode_post(byte_string):
    decoded_str = byte_string.decode(ENCODING_USED)
    logging.info("Decoded post:{}".format(decoded_str))
    if is_xml(decoded_str):
        return decode_post_xml(decoded_str)
    else:
        return decode_post_json(decoded_str)

def is_xml(data_string):
    if isinstance(data_string, str):
        return data_string[:5] == "<xml>"
    return False

# Return a dict of the arguments
def decode_post_xml(xml_data_string):
    def dict_from_root(root):
        d = {}
        for n in root.iter():
            k = n.tag
            v = n.text
            d[k] = v

        return d
    root = ElementTree.fromstring(xml_data_string)
    logging.info("XML root object: {}".format(root))
    data_d = dict_from_root(root)
    
    logging.info("XML decoded data: {}".format(data_d))
    return data_d

def decode_post_json(data_string):
    data_d = eval(data_string)
    print("IS dict:", isinstance(data_d, dict))
    print("IS set:", isinstance(data_d, set))
    return data_d 

