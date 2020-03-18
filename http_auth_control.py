import logging
import hashlib
import time

from random import randint
from http_wx_message import WeChatAuthMessage, WechatTextMessage, WechatPaymentRequest
from http_customer_manager import CustomerMaster

# Takes in dict, api key as string
# Returns a string
def get_signature(payload, api_secret_key):
    def get_combined(payload):
        elements = []
        for param, val in payload.items():
            str_entry = param + "=" + str(val) + "&"
            elements.append(str_entry)
        elements.sort() # Sort in alphabetical order

        combined = ""
        for e in elements:
            combined += e
        
        print("<SIGNATURE GET COMBINED> COMBINED str output {}".format(combined[:-1]))
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

def get_out_trade_number():
    curr_time = int(time.time())
    return "OTN" + str(curr_time)[:28]

class AuthController:
    def __init__(self):
        self.user_state_map = {} # User -> State
        self.state_user_map = {} # State -> User
        self.user_callbacks = {}
        self.cust_master = CustomerMaster()

    def _state_id_exists(self, state_id):
        return state_id in self.state_user_map.keys()

    def _add_stateid(self, user_ID, sid):
        self.user_state_map[user_ID] = sid
        self.state_user_map[sid] = user_ID

    def state_id_to_user(self, sid):
        if not self._state_id_exists(sid):
            logging.error("<state_id to user> state_id {} does not exist".format(sid))
            return False
        return self.state_user_map.get(sid)   

    # Generates a random temporary id that is used to tag open_id to a user.    
    # state is needed because the openid callback only returns openid and state.
    # The idea is that after the openid callback, you can immediately bill.
    # Bill info is tied to the conversation so you need to ID the customer to send the bill request
    def generate_state_id(self, user_ID):
        def getrandint(alphabets):
            # 6 digit number
            return alphabets + str(randint(100000,999999))

        alpha = user_ID[:3] if len(user_ID) > 2 else "uSR"
        sid = getrandint(alpha)
        while self._state_id_exists(sid):
            sid = getrandint(alpha)
        self._add_stateid(user_ID, sid)
        return sid

    def capture_open_id(self, state, openid):
        self.cust_master.log_open_id(state, openid)

    def auth_fetch_open_id(self, state_id):
        if not self._state_id_exists(state_id):
            logging.error("<AUTH FETCH OPEN ID> state_id {} does not exist".format(state_id))
            return False
        return self.cust_master.fetch_open_id(state_id)

    def stash_callback_info(self, user_ID, r_action, req_info):
        self.user_callbacks[user_ID] = (r_action, req_info)
        return

    def pop_callback_info(self, state_id):
        if not state_id in self.state_user_map.keys():
            raise Exception("State id {} does not have belong to any user".format(state_id))
        user_ID = self.state_user_map.get(state_id)
    
        if not user_ID in self.user_callbacks.keys():
            raise Exception("User {} does not have callback information".format(user_ID))
        return self.user_callbacks.get(user_ID)