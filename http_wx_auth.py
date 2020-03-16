import hashlib
import requests
import time
import wechat_dev as wd

from http_utils import RequestSender, ENCODING_USED

# Takes in dict, api key as string
# Returns a string
def get_signature(payload, api_secret_key):
    def get_combined(payload):
        elements = []
        for param, val in payload.items():
            str_entry = param + "=" + val + "&"
            elements.append(str_entry)
        elements.sort() # Sort in alphabetical order

        combined = ""
        for e in elements:
            combined += e
        
        print("<GET COMBINED> COMBINED str output {}".format(combined[:-1]))
        return combined[:-1] # Remove the last "&"

    def calculate_signature(payload_str, api_key):
        temp_str = payload_str + "&key=" + api_key # Adding api_key to the string to be hashed
        
        # Hash using MD5
        hashed = hashlib.md5(temp_str.encode())
        signature = hashed.hexdigest().upper()
        print("SIGNATURE {}".format(signature))
        return signature

    payload_str = get_combined(payload)
    return calculate_signature(payload_str, api_secret_key)

# Manages the Managers
class OpenIDMasterManager:
    def __init__(self):
        self.managers = {}

    def get_open_id(self, user_id):
        return 1

class OpenIDManager:
    def __init__(self):
        self.code_timer = 0
        self.code_recv_time = 0
        self.sender = RequestSender()
        self.req_details = {
            "app_id": wd.get_wechat_app_id(),
            "secret": wd.get_secret_key(),
        }

    def has_valid_code(self):
        curr_time = time.time()
        return (curr_time - self.code_recv_time > self.code_timer)

    def request_openid(self):
        open_id_req_url = "https://api.weixin.qq.com/sns/oauth2/access_token?appid={app_id}&secret={secret}&code={code}&grant_type=authorization_code".format(**open_id_req_info)
        response = self.sender.send_GET(open_id_req_url) # Response 
        response_contents = response.content.decode(ENCODING_USED)
        print("<OPENID REPLY>", response_contents)
        return

    def get_open_id(self):
        return 1

# Open ID
def get_open_id():
    return "id1234141"