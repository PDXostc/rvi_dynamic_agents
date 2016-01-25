import websocket
import json
import threading
import inspect 

try:
    import thread
#TODO use Threading instead of _thread in python3
except ImportError:
    import _thread as thread

class rvi_ws_client:
    def __init__(self):
        self.DEBUG = False
        self.callback_funcs = {}
        self.host = "ws://localhost:8808"

    def set_ws_debug(self, debug_status):
        self.DEBUG = debug_status
        if self.DEBUG:
            websocket.enableTrace(True)
        else:
            websocket.enableTrace(False)

    def print_debug(self,message):

        if self.DEBUG:
            print(message)
        else:
            pass

    def on_error(self,ws, error):

        self.print_debug(error)

    def on_close(self,ws):

        self.print_debug("### closed ###")

    def on_open(self,ws):

        def run(*args):
            payload = {}
            payload['json-rpc'] = "2.0"
            payload['id'] = "0"
            payload['method'] = "register_service"

            for service_name, callback in self.callback_funcs.items():
                payload['params'] = {"service_name":service_name}        
                ws.send(json.dumps(payload))

        opening = threading.Thread(target=run)
        opening.start()

    def on_message(self,ws, message):

        message_dict = json.loads(message)

        if self.DEBUG:
            print(message)
            if message_dict['method'] == 'message':
                print("###########THIS IS A MESSAGE#############")
                for key, value in message_dict.items():
                    print(key, value)
                print("############END OF MESSAGE###############")

        try:
            if (message_dict['method'] == 'message') and (message_dict['params']['service_name'][1:] in self.callback_funcs):
                self.callback_funcs[message_dict['params']['service_name'][1:]](**message_dict['params']['parameters'])
        except:
            self.print_debug("Callback function call failed")
        else:
            self.print_debug("No service with matching callback")


    def set_host(self,target_host):
        self.host = target_host

    def register_services(self,services):

        self.callback_funcs = services
        self.print_debug(self.callback_funcs)
        self.print_debug("Registered services")

        return True

    def services_run(self):

        ws = websocket.WebSocketApp(self.host,
                                    on_message = self.on_message,
                                    on_error = self.on_error,
                                    on_close = self.on_close)
        ws.on_open = self.on_open

        return ws.run_forever()
