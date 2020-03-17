import logging

from random import randint
from http_wx_message import WeChatAuthMessage, WechatTextMessage, WechatPaymentRequest
from http_customer_manager import CustomerMaster

class AuthController:
    def __init__(self):
        self.active_stateids = {}
        self.user_state_map = {} # User -> State
        self.state_user_map = {} # State -> User
        self.user_callbacks = {}
        self.cust_master = CustomerMaster()

    def _add_stateid(self, user_ID, sid):
        self.active_stateids[sid] = 1
        self.user_state_map[user_ID] = sid
        self.state_user_map[sid] = user_ID

    def state_id_to_user(self, sid):
        

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
        while sid in self.active_stateids:
            sid = getrandint(alpha)
        self._add_stateid(user_ID, sid)
        return sid

    def capture_open_id(self, state, openid):
        self.cust_master.log_open_id(state, openid)

    def auth_fetch_open_id(self, user_ID):
        user_state = self.user_state_map.get(user_ID, False)
        if not user_state:
            logging.error("<AUTH FETCH OPEN ID> {} has no open ID".format(user_ID))
            return False
        return self.cust_master.fetch_open_id(user_state)

    def stash_callback_info(self, user_ID, req_info):
        self.user_callbacks[user_ID] = req_info
        return

    def pop_callback_info(self, state_id):
        if not state_id in self.state_user_map.keys():
            raise Exception("State id {} does not have belong to any user".format(state_id))
    
        user_ID = self.state_user_map.get(state_id)
    
        if not user_ID in self.user_callbacks.keys():
            raise Exception("User {} does not have callback information".format(user_ID))
        return self.user_callbacks.get(user_ID)