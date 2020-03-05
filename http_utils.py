from xml.etree import ElementTree

import logging
import wechat_dev as wd
import time


def response_to_xml(r_action, og_reqest_info):
    if r_action.is_bill():
        msgclass = WechatPaymentRequest(r_action)
    else:
        msgclass = WechatTextMessage(r_action, og_reqest_info)
    xml = msgclass.to_xml()
    return xml

# Class to carry message contents.
class WechatMessage():
    def to_xml(self):
        pass

class WechatTextMessage(WechatMessage):
    def __init__(self, r_action, og_reqest_info):
        self.r_action = r_action
        self.og_req_info = og_reqest_info

    def to_xml(self):
        msg_info = self.og_req_info
        reply_content = self.r_action.get_replytext()
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
        reply_content
        )
        # Because its a reply, the from and to are swapped
        logging.info("POST reponse:\n{}".format(reply_content))
        return xml

class WechatPaymentRequest(WechatMessage):
    def __init__(self, r_action, body=""):
        self.rd = r_action.get_payload()
        assert(isinstance(amount,float) or isinstance(amount,int))
        auxiliary_info = {
            "body": body,
            "appid": wd.get_wechat_app_id(),
            "recv_acc_num": wd.get_recieving_acc_no(),
            "order_num" : self._generate_order_number()
        }

        self.rd.update(auxiliary_info)

    def set_notification_url(self, add):
        self.rd["notify_url"] = add

    # Returns the raw dict
    def _get_request_details(self):
        return self.rd
    
    # Returns a string
    def _generate_order_number(self):
        int_time = int(time.time())
        onum = "ODR_" + str(int_time)
        return onum

    def get_wechat_pay_url(self):
        wechat_api_address = "https://api.mch.weixin.qq.com/pay/unifiedorder"
        return wechat_api_address

    def to_xml(self):
        # Looks like this
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

        request_details = self.rd
        p_details = request_details.get("p_details",)
        p_details = '<![CDATA[{ "goods_detail":[ { "goods_id":"iphone6s_16G", "wxpay_goods_id":"1001", "goods_name":"iPhone6s 16G", "quantity":1, "price":528800, "goods_category":"123456", "body":"苹果手机" }, { "goods_id":"iphone6s_32G", "wxpay_goods_id":"1002", "goods_name":"iPhone6s 32G", "quantity":1, "price":608800, "goods_category":"123789", "body":"苹果手机" } ] }]]>'
        xml_formatted = (
            "<xml>"
            "<appid>{appid}</appid>"
            "<attach>{title}</attach>"
            "<body>{body}</body>"
            "<mch_id>{recv_acc_num}</mch_id>" # 微信支付分配的商户号 Recieving merchant account number
            "<detail>{p_details}</detail>"
            "<nonce_str>1add1a30ac87aa2db72f57a2375d8fec</nonce_str>" # Random String
            "<notify_url>{notify_url}</notify_url>" # Address that recieves the outcome of the transaction (SUCCESS or FAIL)
            "<openid>oUpF8uMuAJO_M2pxb1Q9zNjWeS6o</openid>" # openID. Need to figure out how
            "<out_trade_no>{order_num}</out_trade_no>" # Order number. Should be unique (within same merchant)
            "<total_fee>{amount}</total_fee>"
            "<limit_pay>no_credit</limit_pay>" # Restrictions on payment method
            "<trade_type>JSAPI</trade_type>" # Constant
            "<sign>0CB01533B8C1EF103065174F50BCA001</sign>" #Signature. Need to figure out how
        ).format(**request_details)
        return xml_formatted

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
