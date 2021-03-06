import logging
import wechat_dev as wd

from http_auth_control import AuthController
from http_wx_message import WeChatAuthMessage, WechatTextMessage, WechatPaymentRequest
from http_utils import RequestSender, ENCODING_USED, url_path_to_dict, get_req_sender, get_ip_from_header


# Called boss because it tells other people what to do. 
# Don't want to name it 'Manager'
class RequestBoss:
    def __init__(self):
        self.auth_ctrl = AuthController()
        self.sender = RequestSender()
        self.redirect_map = {}

    # The follow up is to WeChat's API
    # Not A message to the user WechatTextMessage
    # A WeChatPayment Request !
    def send_auth_followup_message(self, state_id):
        logging.critical("SENDING AUTH FOLLOWUP")
        # Sends a POST request to WeChat
        # Uses info captured previously for auth message.
        r_action, og_post_req_info = self.auth_ctrl.pop_callback_info(state_id)
        logging.debug("Cache retrieved POST Request info {}".format(og_post_req_info))
        open_id = self.auth_ctrl.auth_fetch_open_id(state_id) # Given by WeChat after opening the auth link
        spbill_ip = self.auth_ctrl.pop_ip(state_id) # Captured when user is redirected to our domain
        wx_pay_req = WechatPaymentRequest(r_action, og_post_req_info, open_id, spbill_ip)
        wx_response = wx_pay_req.get_wx_pay_request() # Includes sending a request to Wechat servers
        return wx_response

    def _capture_redirect_url(self, state_id, url):
        self.redirect_map[state_id] = url
    
    def _get_redirect_url(self, state_id):
        return self.redirect_map.get(state_id, False)

    def _capture_purchase_callback_info(self, user_ID, r_action, request_info):
        self.auth_ctrl.stash_callback_info(user_ID, r_action, request_info)

    def interpret_get(self, path, headers):
        def is_wechat_echo_msg(req_dict):
            wx_req_comp = ["signature", "timestamp", "nonce", "echostr"]
            rd_keys = req_dict.keys()
            for c in wx_req_comp:
                if not c in rd_keys:
                    logging.debug("GET is not WeChat Auth. {} is missing".format(c))
                    return False
            return True

        def is_openid_callback(path):
            r = wd.get_openid_subdomain() in path
            if r: logging.warn("Request with path: <%s> is an openid_callback" % path)
            return r
            
        def capture_openid(req_dict):
            logging.warn("Capturing OPENID")
            open_id = req_dict.get("code", False)
            state_id = req_dict.get("state", False)
            if not open_id:
                logging.error("<CAPTURE OPENID> code not found in GET request")
            if not state_id:
                logging.error("<CAPTURE OPENID> state not found in GET request")
            
            if open_id and state_id:
                self.auth_ctrl.capture_open_id(state_id, open_id)
                self.send_auth_followup_message(state_id) # Triggers sending the POST request to Wechat
            else:
                logging.error("Did not send followup. One of the following is missing:")
                logging.error("OPENID {}| STATEID {}".format(open_id, state_id))

        def get_wechat_echo_auth(req_dict):
            # isolate echostr
            echostr = req_dict.get("echostr")
            logging.debug("<DO GET> GET request is WeChat Auth. Sending reply")
            logging.debug("Sending auth code: {}".format(echostr))
            return echostr

        request_dict = url_path_to_dict(path)
        logging.info("Recieved a GET request,\nPath: %s\nHeaders:\n%s\n", str(request_dict), str(headers))
        
        if is_wechat_echo_msg(request_dict):
            return "text", get_wechat_echo_auth(request_dict)

        elif is_openid_callback(path):
            logging.warn("GET request is WX OpenID callback")
            capture_openid(request_dict)
            return "redirect", "callback_landing.html"

        elif "redir" in path:
            logging.debug("GET request is a redir (a callback from WeChat openid Auth)")
            state_id = request_dict.get(wd.REDIRECT_CALLBACK_PARAM_NAME)
            self.auth_ctrl.stash_ip(state_id, headers)
            final_target_url = self._get_redirect_url(state_id) # Captured during authreq
            return ("redirect", final_target_url)

        else:
            logging.debug("Ordinary GET request")
            return "no_action", ""

    def interpret_post(self, r_action, og_reqest_info):
        user_ID = get_req_sender(og_reqest_info)
        if r_action.is_authreq():
            # If an openID authentication is needed
            state_id = self.auth_ctrl.generate_state_id(user_ID)
            msgclass = WeChatAuthMessage(r_action, og_reqest_info, state_id)
            self._capture_redirect_url(state_id, msgclass.get_redirect_url())
            self._capture_purchase_callback_info(user_ID, r_action, og_reqest_info)
        else:
            msgclass = WechatTextMessage(r_action, og_reqest_info)

        xml = msgclass.to_wechat_reply_xml()
        return xml  

    