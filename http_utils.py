from xml.etree import ElementTree

import logging
import requests
import time
import wechat_dev as wd


def response_to_xml(r_action, og_reqest_info):
    if r_action.is_bill():
        msgclass = WechatPaymentRequest(r_action, og_reqest_info)
        pay_req_response = msgclass.send_pay_request() # SEND it first
        logging.info("<RESPONSE_TO_XML> PAY REQUEST RESPONSE {}".format(pay_req_response.text))
    else:
        msgclass = WechatTextMessage(r_action, og_reqest_info)
    xml = msgclass.to_wechat_reply_xml()
    return xml

# Class to carry message contents.
class WechatMessage():
    def to_wechat_reply_xml(self):
        pass

class WechatTextMessage(WechatMessage):
    def __init__(self, r_action, og_reqest_info):
        self.r_action = r_action
        self.og_req_info = og_reqest_info

    def to_wechat_reply_xml(self):
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

class WechatPaymentRequest(WechatTextMessage):
    def __init__(self, r_action, og_reqest_info):
        super(WechatPaymentRequest, self).__init__(r_action, og_reqest_info) # Superclass initalizer

        self.rd = r_action.get_payload()
        amount = self.rd.get("amount", "")
        assert(isinstance(amount,float) or isinstance(amount,int))
        auxiliary_info = {
            "appid": wd.get_wechat_app_id(),
            "recv_acc_num": wd.get_recieving_acc_no(),
            "order_num" : self._generate_order_number(),
            "notify_url": wd.get_notify_url(),
            "spbill_ip": wd.get_spbillip()
        }

        self.rd.update(auxiliary_info)

    def set_notify_url(self, add):
        self.rd["notify_url"] = add

    # Not sure what it means
    def set_spbill_ip(self, ip):
        self.rd["spbill_ip"] = ip

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
    
    def send_pay_request(self):
        url = wd.get_api_url()
        sender = RequestSender()
        return sender.send_POST(url, self.to_payment_xml()) # SEND IT

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

        request_details = self.rd
        p_details = request_details.get("p_details",)
        p_details = '<![CDATA[{ "goods_detail":[ { "goods_id":"iphone6s_16G", "wxpay_goods_id":"1001", "goods_name":"iPhone6s 16G", "quantity":1, "price":528800, "goods_category":"123456", "body":"苹果手机" }, { "goods_id":"iphone6s_32G", "wxpay_goods_id":"1002", "goods_name":"iPhone6s 32G", "quantity":1, "price":608800, "goods_category":"123789", "body":"苹果手机" } ] }]]>'
        xml_formatted = (
            "<xml>"
            "<appid>{appid}</appid>" # REQ 公众号 ID 
            "<attach>{title}</attach>" # OPTIONAL
            # "<detail>{p_details}</detail>" # OPTIONAL)  
            # "<device_info>WEB</device_info>" # OPTIONAL               
            "<body>{body}</body>" # REQ
            # "<product_id>0001</product_id>" # OPTIONAL
            "<mch_id>{recv_acc_num}</mch_id>" # REQ 微信支付分配的商户号 Recieving merchant account number
            "<nonce_str><![CDATA[1add1a30ac87aa2db72f57a2375d8fec]]></nonce_str>" # REQ. Random String 32 char and below
            "<notify_url><![CDATA[{notify_url}]]></notify_url>" # REQ Address that recieves the outcome of the transaction (SUCCESS or FAIL)
            "<openid><![CDATA[oUpF8uMuAJO_M2pxb1Q9zNjWeS6o]]></openid>" # REQ for JSAPI. OpenID is assigned to customer and 公众号 pair
            "<out_trade_no><![CDATA[{order_num}]]></out_trade_no>" # REQ Order number. Should be unique (within same merchant)
            "<total_fee><![CDATA[{amount}]]></total_fee>" # REQ
            "<spbill_create_ip><![CDATA[{spbill_ip}]]></spbill_create_ip>" # REQ
            # "<limit_pay>no_credit</limit_pay>" # OPTIONAL Restrictions on payment method
            "<trade_type>JSAPI</trade_type>" # REQ Constant
            # "<reciept>Y</reciept>" # OPTIONAL Whether or not to generate a reciept on Wechat
            "<sign><![CDATA[0CB01533B8C1EF103065174F50BCA001]]></sign>" # REQ Signature. Need to figure out how
            "</xml>"
        ).format(**request_details)
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

class RequestSender:
    # Returns a Request object
    def send_GET(self, url, req_params):
        param_dict = {
            "body":req_params
        }
        return requests.get(url, params=param_dict)

    # Returns a Request object
    def send_POST(self, url, xml):
        headers = {'Content-Type': 'text/html'}
        e_xml = xml.encode('utf-8')
        return requests.post(url=url, data=e_xml, headers = headers)

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
