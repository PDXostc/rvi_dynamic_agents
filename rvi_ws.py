import websocket
import json
import threading

try:
    import thread
#TODO use Threading instead of _thread in python3
except ImportError:
    import _thread as thread

#rvi_ws_client will be in charge of handling all communication via websockets between the service bundle and RVI.
#we can automatically instantiate
class rvi_ws_client:

    def __init__(self, bundle_id = None, debug = False, host = "ws://localhost:8808"):

        self.DEBUG = debug
        self.service_bundle_id = bundle_id
        self.callback_funcs = {}
        self.host = host

    #set_ws_debug takes in parameter debug_status which is type bool. Will toggle on or off all websocket related debug messages.    
    def set_ws_debug(self):

        if self.DEBUG:
            websocket.enableTrace(True)
        else:
            websocket.enableTrace(False)

    #print_debug is the debug message printer. Will check the class variable self.DEBUG to determine whether or not to print messages
    def print_debug(self,message):

        if self.DEBUG:
            print(message)
        else:
            pass

    #on_error will print an error if the websocket application encounters any and prints if debug is toggled on
    def on_error(self,ws, error):

        self.print_debug(error)

    #TODO unregister service for clean close of websocket, for time being will just print out debug
    def on_close(self,ws):

        self.print_debug("### closed ###")

    #What to do on the open of the application. Note we must register_services for this to do anything.
    def on_open(self,ws):

        def run(*args):

            payload = {}
            payload['json-rpc'] = "2.0"
            payload['id'] = "0"
            payload['method'] = "register_service"

            for service_name, callback in self.callback_funcs.items():
                payload['params'] = {"service_name":self.service_bundle_id+"/"+service_name}        
                ws.send(json.dumps(payload))

        opening = threading.Thread(target=run)
        opening.start()

    #on_message will route the message from the websocket to it's corresponding callback function that registered the service
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
            if (message_dict['method'] == 'message') and (message_dict['params']['service_name'][(2+len(self.service_bundle_id)):] in self.callback_funcs):
                self.callback_funcs[message_dict['params']['service_name'][(2+len(self.service_bundle_id)):]](**message_dict['params']['parameters'])
        except:
            self.print_debug("Callback function call failed")
        else:
            self.print_debug("No service with matching callback")

    #set_host will expect a string parameter that will change the class variable host which will connect to our websocket server
    def set_host(self,target_host):

        self.host = target_host

    #register_services will take in a dictionary of services to register. 
    #The keys of the dictionary will be the service name and the value will be the callback function
    #will return success on successfully changing the class' callback function dictionary
    def register_services(self,services):

        self.callback_funcs = services
        self.print_debug(self.callback_funcs)
        self.print_debug("Registered services")

        return True
    
    def set_service_bundle(self, service_bundle):
        self.service_bundle_id = service_bundle
        return True

    #services_run is a callable function for after everything is set to start the websocket client.
    def services_run(self):

        if self.service_bundle_id == None:
            self.print_debug("No service bundle defined yet")
            return False

        self.set_ws_debug()

        ws = websocket.WebSocketApp(self.host,
                                    on_message = self.on_message,
                                    on_error = self.on_error,
                                    on_close = self.on_close)
        ws.on_open = self.on_open

        return ws.run_forever()
