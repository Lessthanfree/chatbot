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
        
# Run here
if __name__ == "__main__":
    try:
        chat_forever()
    except KeyboardInterrupt:
        print("Keyboard interrupted")
    except Exception as e:
        print("Exception!", e)
    finally:
        print("Exiting...")