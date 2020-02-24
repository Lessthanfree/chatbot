from xml.etree import ElementTree
import logging

# Wechat can send data in the form of XML or JSON
def decode_post(data):
    decoded_str = data.decode('utf-8')
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
