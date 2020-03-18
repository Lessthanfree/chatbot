import logging
import wechat_dev as wd

from http_auth_control import AuthController
from http_wx_message import WeChatAuthMessage, WechatTextMessage, WechatPaymentRequest
from http_utils import RequestSender, ENCODING_USED, url_path_to_dict, get_req_sender


# Called boss because it tells other people what to do. 
# Don't want to name it 'Manager'
class RequestBoss:
    def __init__(self):
        self.auth_ctrl = AuthController()
        self.sender = RequestSender()

    # The follow up is 
    # Not A message to the user WechatTextMessage
    # A WeChatPayment Request !
    def send_auth_followup_message(self, state_id):
        # Sender sends a POST request to WeChat
        # Uses info captured previously for auth message.
        r_action, og_req_info = self.auth_ctrl.pop_callback_info(state_id)
        print(og_req_info)
        open_id = self.auth_ctrl.auth_fetch_open_id(state_id)
        wx_pay_req = WechatPaymentRequest(r_action, og_req_info, open_id)
        wx_response = wx_pay_req.get_wx_pay_request() # Includes sending a request to Wechat servers
        return wx_response

    def _capture_info_for_callback(self, user_ID, r_action, request_info):
        self.auth_ctrl.stash_callback_info(user_ID, r_action, request_info)

    def interpret_get(self, path, headers):
        def is_from_wechat(req_dict):
            wx_req_comp = ["signature", "timestamp", "nonce", "echostr"]
            rd_keys = req_dict.keys()
            for c in wx_req_comp:
                if not c in rd_keys:
                    logging.info("GET is not WeChat Auth. {} is missing".format(c))
                    return False
            return True

        def is_openid_callback(path):
            first_subdomain = path.split("/")[1]
            return wd.get_openid_subdomain() in first_subdomain
            
        def capture_openid(req_dict):
            logging.info("GET is WX OpenID callback")
            open_id = req_dict.get("code", False)
            state_id = req_dict.get("state", False)
            if not open_id:
                logging.error("<CAPTURE OPENID> code not found in GET request")
            if not state_id:
                logging.error("<CAPTURE OPENID> state not found in GET request")
            
            if open_id and state_id:
                self.auth_ctrl.capture_open_id(state_id, open_id)
                self.send_auth_followup_message(state_id) # Triggers sending the POST request to Wechat

        def get_wechat_echo_auth(req_dict):
            # isolate echostr
            echostr = req_dict.get("echostr")
            logging.info("<DO GET> GET request is WeChat Auth. Sending reply")
            print("Sending auth code: {}".format(echostr))
            return echostr

        request_dict = url_path_to_dict(path)
        logging.info("GET request,\nPath: %s\nHeaders:\n%s\n", str(request_dict), str(headers))
        
        if is_from_wechat(request_dict):
            return "normal", get_wechat_echo_auth(request_dict)

        elif is_openid_callback(path):
            capture_openid(request_dict)
            return "normal", ""
        elif "redir" in path:
            return ("redirect", "You should be redirected")
        else:
            return False, ""

    def get_response_xml(self, r_action, og_reqest_info):
        user_ID = get_req_sender(og_reqest_info)
        if r_action.is_authreq():
            # If an openID authentication is needed
            state_id = self.auth_ctrl.generate_state_id(user_ID)
            msgclass = WeChatAuthMessage(r_action, og_reqest_info, state_id)
            self._capture_info_for_callback(user_ID, r_action, og_reqest_info)
        else:
            msgclass = WechatTextMessage(r_action, og_reqest_info)

        xml = msgclass.to_wechat_reply_xml()
        return xml  

    