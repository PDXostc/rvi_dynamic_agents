import json
import threading
import websocket
import time
import sys
import redis

DEBUG = True

host="ws://localhost:8808"
counter = 0
service_name = 'dynamicagents/agent_report'

open_files = {}



def on_message(ws, message):
    message_dict = json.loads(message)
#    lock = threading.Lock()

    if DEBUG:
        if message_dict['method'] == 'message':
            print("###########THIS IS A MESSAGE#############")
            for key, value in message_dict.items():
                print(key, value)
            print("############END OF MESSAGE###############")
##############################################################################################################
##############################################################################################################
########################################Check for the correct parameters######################################
    if message_dict['method'] == 'message' and message_dict['params']['service_name'][1:] == service_name:
        try:
            params = message_dict['params']['parameters']
            agent_id = params['agent_id']
            timestamp = params['timestamp']
            for key in params['payload']:
                rconn.hincrby(('agent:'+agent_id), key , str(params['payload'][key]))


            if agent_id not in open_files:
                open_files[agent_id] = open(agent_id, "a+")

            elif agent_id in open_files:
                open_files[agent_id].write(json.dumps(params) + "\n")
                open_files[agent_id].flush()
            
            else:
                pass

        except:
            if DEBUG:
                print('Incorrect Parameters will not forward to agent_register')


##############################################################################################################
##############################################################################################################

def on_error(ws, error):
    if DEBUG:
        print(error)


def on_close(ws):
    if DEBUG:
        print("### closed ###")


def on_open(ws):
    def run(*args):
        payload = {}
        payload['json-rpc'] = "2.0"
        payload['id'] = counter
        payload['method'] = "register_service"
        payload['params'] = {"service_name":service_name}
        
        ws.send(json.dumps(payload))

    opening = threading.Thread(target=run)
    opening.start()


if __name__ == "__main__":

    websocket.enableTrace(True)


    while True:

        if len(sys.argv) < 2:
            host = "ws://localhost:8808"
        else:
            host = sys.argv[1]

        ws = websocket.WebSocketApp(host,
                                    on_message = on_message,
                                    on_error = on_error,
                                    on_close = on_close)
        ws.on_open = on_open

        rconn = redis.StrictRedis(host='localhost', port=6379, db=0)

        if ws.run_forever() is None:
            if DEBUG:
                print('No RVI. Wait and retry.')
                time.sleep(2)
            continue

    try:
        while True:
            time.sleep(1.0)

    except KeyboardInterrupt:
        print('^C received, shutting down server')
