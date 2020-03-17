import logging
import time
import wechat_dev as wd
import http_wx_auth as wxauth

from urllib import parse
from http_utils import RequestSender, decode_post

# Class to carry message contents.
class WechatMessage():
    def to_wechat_reply_xml(self):
        pass

class WechatTextMessage(WechatMessage):
    def __init__(self, r_action, og_reqest_info, *extra_args):
        self.r_action = r_action
        self.reply_content = r_action.get_replytext()
        self.og_req_info = og_reqest_info
        self.init_extra(extra_args)

    # Method to be overwritten. So that superclasses dont have to overwrite init.
    def init_extra(self, extra_args):
        pass

    def to_wechat_reply_xml(self):
        msg_info = self.og_req_info
        xml = (
            "<xml>"
            "<ToUserName><![CDATA[%s]]></ToUserName>"
            "<FromUserName><![CDATA[%s]]></FromUserName>"
            "<CreateTime>%s</CreateTime>"
            "<MsgType><![CDATA[text]]></MsgType>"
            "<Content><![CDATA[%s]]></Content>"
            "</xml>"
        ) % (
        msg_info['FromUserName'], 
        msg_info['ToUserName'],
        time.gmtime(),
        self.reply_content
        )
        # Because its a reply, the from and to are swapped
        logging.info("POST reponse:\n{}".format(self.reply_content))
        return xml

class WeChatAuthMessage(WechatTextMessage):
    # super(WechatPaymentRequest, self).__init__(r_action, og_reqest_info) # Superclass initalizer for reference
    OPENID_URL_TEMPLATE = "https://open.weixin.qq.com/connect/oauth2/authorize?appid={app_id}&redirect_uri={notify_url}&response_type=code&scope={scope}&state={state_id}#wechat_redirect"
    auth_scope = "snsapi_base" # Basic user info. Using snsapi_userinfo would ask for personal information.

    def init_extra(self, extra_args):
        def build_url(state_id):
            encoded_url = parse.quote_plus(wd.get_openid_notify_url()) # urllib's parse encodes the url
            print("<WECHAT AUTH MSG BUILD URL>", encoded_url)
            params = {
                "app_id": wd.get_wechat_app_id(),
                "notify_url": encoded_url,
                "scope": self.auth_scope,
                "state_id": state_id
            }
            return self.OPENID_URL_TEMPLATE.format(**params)

        def insert_url(msg, url):
            return msg + "\r\n" + url

        if not len(extra_args) == 1:
            raise Exception("WeChatAuthMessage expected 1 argument, got {}".format(extra_args))
        
        state_id = extra_args[0]
        final_url = build_url(state_id)
        self.reply_content = insert_url(self.reply_content, final_url)


class WechatPaymentRequest(WechatTextMessage):
    SIGN_TYPE = "MD5"
    TRADE_TYPE = "JSAPI" # JSAPI is for WeChat apps. Others are for (native apps) and WEB
    def init_extra(self, extra_args):
        self.request_data = self.r_action.get_payload()
        amount = self.request_data.get("amount", "")
        assert(isinstance(amount,float) or isinstance(amount,int))
        auxiliary_info = {
            "appid": wd.get_wechat_app_id(),
            "mch_id": wd.get_recieving_acc_no(),
            "order_num" : self._generate_order_number(),
            "notify_url": wd.get_notify_url(),
            "nonce_str": self._generate_nonce_str(),
            "open_id": self.curr_open_id,
            "reciept": "Y",
            "trade_type": self.TRADE_TYPE,
            "spbill_create_ip": wd.get_spbillip(),
            "sign_type": self.SIGN_TYPE
        }

        self.request_data.update(auxiliary_info)

    def set_notify_url(self, add):
        self.request_data["notify_url"] = add

    # Not sure why they need the IP
    def set_spbill_ip(self, ip):
        self.request_data["spbill_create_ip"] = ip

    def set_openid(self, openid):
        self.curr_open_id = openid

    def _get_request_data(self):
        return self.request_data
    
    # Returns a string
    def _generate_order_number(self):
        int_time = int(time.time())
        onum = "ODR_" + str(int_time)
        return onum

    # Random string i assume for hashing purposes
    def _generate_nonce_str(self):
        return "1add1a30ac87aa2db72f57a2375d8fec"

    # Add the signature to the payload dict
    def _add_signature(self):
        sign = self._generate_signature()
        self.request_data["sign"] = sign

    def _generate_signature(self):
        api_k = wd.get_secret_key()
        return wxauth.get_signature(self._get_request_data(), api_k)

    def _add_to_reply_content(self, addition):
        TOKEN = "<>"
        self.reply_content = self.reply_content + TOKEN + addition
        return

    def get_wx_pay_request(self):   
        def add_data_to_reply_content(data):
            return_flag = data.get("return_code")
            return_msg = data.get("return_msg")
            if return_flag == "FAIL":
                content = "联系失败"
            elif return_flag == "SUCCESS":
                if return_msg == "OK":
                    content = "支付成功"
                else:
                    content = "支付失败"
            else:
                content = "未知失败"

            self._add_to_reply_content(content)
            return
        wx_pay_link_reply = self._request_pay_link()
        wx_pl_dict = decode_post(wx_pay_link_reply)
        logging.info("<RESPONSE_TO_XML> PAY REQUEST RESPONSE {}".format(wx_pl_dict))
        add_data_to_reply_content(wx_pl_dict)
        return

    # Sends a request to WX api for a pay link. Should get back a confirmation message of success or fail.
    def _request_pay_link(self):
        url = wd.get_api_url()
        sender = RequestSender()
        reponse_obj = sender.send_POST(url, self.to_payment_xml())
        return reponse_obj.content # Returns as bytes

    def to_payment_xml(self):
        # Following WeChat's JSAPI. Not H5.
        # <xml>
            # <appid>wx2421b1c4370ec43b</appid>
            # <attach>支付测试</attach>
            # <body>JSAPI支付测试</body>
            # <mch_id>10000100</mch_id>
            # <detail><![CDATA[{ "goods_detail":[ { "goods_id":"iphone6s_16G", "wxpay_goods_id":"1001", "goods_name":"iPhone6s 16G", "quantity":1, "price":528800, "goods_category":"123456", "body":"苹果手机" }, { "goods_id":"iphone6s_32G", "wxpay_goods_id":"1002", "goods_name":"iPhone6s 32G", "quantity":1, "price":608800, "goods_category":"123789", "body":"苹果手机" } ] }]]></detail>
            # <nonce_str>1add1a30ac87aa2db72f57a2375d8fec</nonce_str>
            # <notify_url>http://wxpay.wxutil.com/pub_v2/pay/notify.v2.php</notify_url>
            # <openid>oUpF8uMuAJO_M2pxb1Q9zNjWeS6o</openid>
            # <out_trade_no>1415659990</out_trade_no>
            # <spbill_create_ip>14.23.150.211</spbill_create_ip>
            # <total_fee>1</total_fee>
            # <limit_pay>no_credit</limit_pay>
            # <trade_type>JSAPI</trade_type>
            # <sign>0CB01533B8C1EF103065174F50BCA001</sign>
        # </xml> 
        
        self._add_signature() # This adds signature to request_data
        
        xml_formatted = "<xml>"
        for param_name, param_val in self._get_request_data().items():
            entry = "<{0}>{1}</{0}>".format(param_name, param_val) # XML entry format
            xml_formatted += entry
        xml_formatted += "</xml>"
        print("XML FORMATTED MESSAGE", xml_formatted)
        return xml_formatted

# Template of a successful reply from WeChat
# <xml>
#    <return_code><![CDATA[SUCCESS]]></return_code>
#    <return_msg><![CDATA[OK]]></return_msg>
#    <appid><![CDATA[wx2421b1c4370ec43b]]></appid>
#    <mch_id><![CDATA[10000100]]></mch_id>
#    <nonce_str><![CDATA[IITRi8Iabbblz1Jc]]></nonce_str>
#    <sign><![CDATA[7921E432F65EB8ED0CE9755F0E86D72F]]></sign>
#    <result_code><![CDATA[SUCCESS]]></result_code>
#    <prepay_id><![CDATA[wx201411101639507cbf6ffd8b0779950874]]></prepay_id>
#    <trade_type><![CDATA[MWEB]]></trade_type>
#    <mweb_url><![CDATA[https://wx.tenpay.com/cgi-bin/mmpayweb-bin/checkmweb?prepay_id=wx2016121516420242444321ca0631331346&package=1405458241]]></mweb_url>
# </xml>
