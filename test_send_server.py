import requests

def send_post(payload):
    addr = "http://localhost:8080"
    try:
        r = requests.post(url=addr, data = payload)
        return r
    except Exception as e:
        print(e)
        return 

def chat_forever(port = 8080):
    userID = input("Enter your user ID: ")
    while 1:
        msg = input("Enter a message:\n")
        payload = {
            'userID': userID,
            'message': msg,
            'msg_type':"raw"
        }
        req = send_post(payload)
        print("RESPONSE TEXT <{}>".format(req.text))
        
def send_GET_request(addr):
    try:
        r = requests.get(url=addr)
    except Exception as e:
        print(e)
        return 
    cont = r.content.decode("utf-8")
    print(cont)

# Run here
if __name__ == "__main__":
    addr = input("Enter the address:")
    try:
        send_GET_request(addr)
    except KeyboardInterrupt:
        print("Keyboard interrupted")
    except Exception as e:
        print("Exception!", e)
    finally:
        print("Exiting...")