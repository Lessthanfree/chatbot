import hashlib
import logging
import time
import urllib
import wechat_dev as wd

from http_utils import RequestSender, ENCODING_USED

# Manages the Managers
class CustomerMaster:
    def __init__(self):
        self.managers = {}

    def spawn_manager(self, state_id):
        self.managers[state_id] = CustomerManager()
        return self.managers[state_id]

    def _state_exists(self, state_id):
        if not state_id in self.managers.keys():
            return False
        return True

    def log_open_id(self, state_id, openid):
        if self._state_exists(state_id):
            logging.error("Manager {} already exists. Overwriting".format(state_id))
        curr_mgr = self.spawn_manager(state_id)
        curr_mgr.set_open_id(openid)
        return

    def fetch_open_id(self, state_id):
        if self._state_exists(state_id):
            curr_manager = self.managers.get(state_id)
            open_id = curr_manager.get_open_id()
            return open_id
        logging.error("Tried to fetch OpenID but Manager with state <{}> not found".format(state_id))
        return False

# Manages customer details.
# Including OpenID and username.
class CustomerManager:
    openid_req_url = "https://api.weixin.qq.com/sns/oauth2/access_token?appid={app_id}&secret={secret}&code={code}&grant_type=authorization_code"
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
        open_id_req_info = {} # TODO
        self.openid_req_url.format(**open_id_req_info)
        response = self.sender.send_GET(self.openid_req_url) # Response 
        response_contents = response.content.decode(ENCODING_USED)
        print("<OPENID REPLY>", response_contents)
        return

    def get_open_id(self):
        return self.openid

    def set_open_id(self, openid):
        self.openid = openid