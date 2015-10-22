import can
import time
import datetime
import psutil
import subprocess
import json
import threading
import websocket
import sys
import os
import base64

try:
    import thread
except ImportError:  #TODO use Threading instead of _thread in python3
    import _thread as thread

#DEBUG MESSAGING PRINTOUTS
DEBUG = True

#Agent Handler Globals
#agent_pool = Agents that are currently registered and that we are keeping track of
#agent_map = map of our agent_pool that will be stored in a memory to keep running even if case of power cycles
#running_agents = dictionary of running processes which can be terminated if needed
running_agents = {}
expire_monitors = {}
agent_map = []
agent_pool = []
expire_monitor_threads = {}

#RVI Params
service_name_1 = "dynamicagents/agent"
service_name_2 = "dynamicagents/terminate_agent"

host="ws://localhost:8808"
counter = 0
target_service = "jlr.com/backend/dynamicagents/agent_report"

lock = threading.Lock()
def report(message):
    counter = int(time.time())
    # lock = threading.Lock()
    # lock.acquire()
    message_dict = message
    message_dict['timestamp'] = str(time.time())
    message_dict['agent_id'] = sys.argv[0][7:len(sys.argv[0])-3]
    payload = {'jsonrpc':"2.0", 'id':str(time.time()), 'method':"message"}
    payload['params'] = {'service_name':target_service,
                            'timeout':(int(time.time())+60), 'parameters':message_dict}
    try:
        ws = websocket.create_connection(host)
        if DEBUG:
            print(payload)
        ws.send(json.dumps(payload))
    except:
        if DEBUG:
            print('Could not send agent_report')
    # lock.release()

def terminate_agent(agent_id):
    lock.acquire()
    launch_command = None
    expiration_date = None
    pwd = os.getcwd()
    save_path = pwd + '/agents/'

    for agent in agent_pool:
        if agent['agent_name'] == agent_id:
            launch_command = agent['launch']
            expiration_date = agent['expires']
            break
        else:
            pass
    tempdeletepath = os.path.join(save_path, launch_command.split()[1])

    try:
        running_agents[agent_id].terminate()
        if DEBUG:
            print('---------------Terminating----------------')
            print(agent_id + launch_command + str(expiration_date))
            print('------------------------------------------')

    except:
        if DEBUG:
            print('No running agent with id:' + agent_id)

    try:
        agent_pool.remove({'agent_name':agent_id, 'launch':launch_command, 'expires':expiration_date})
    except:
        if DEBUG:
            print('Agent does not exist in agent_pool')
            print(agent_pool)
    try:
        agent_map = open('agent_map.txt', 'w+')
        json.dump(agent_pool, agent_map)
        agent_map.close()
    except:
        if DEBUG:
            print('Could not write current agent pool to memory')

        agent_ids = []
        for agent in agent_pool:
            agent_ids.append(agent['launch'].split()[1])

    to_terminate = [agent_id]
    agent_pids = psutil.pids()
    for pid in agent_pids:
        try:
            if any(x in psutil.Process(pid).cmdline()[1] for x in to_terminate):
                if DEBUG:
                    print('----------------Terminated----------------')
                    print(psutil.Process(pid).cmdline())
                    print(pid)
                    print('------------------------------------------')
                psutil.Process(pid).terminate()
        except:
            continue            

    try:
    	os.remove(tempdeletepath)
    except:
    	if DEBUG:
    		print('Could not delete file')

    lock.release()


def agent_expiration_monitor(agent_id):
    expiration_date = None
    count = 0

    expire_monitor_threads[agent_id] = threading.current_thread()

    for agent in agent_pool:
        if agent['agent_name'] == agent_id:
            launch_command = agent['launch']
            expiration_date = agent['expires']
            break
        else:
            pass

    if expiration_date is not None:

        while (expiration_date - time.time()) >= 0:
            if running_agents[agent_id].poll() is None:
                pass
            elif count <= 5:
                launch_command = None
                for agent in agent_pool:
                    if agent['agent_name'] == agent_id:
                        launch_command = agent['launch']
                        expiration_date = agent['expires']
                        break
                    else:
                        pass
                if launch_command == None:
                    break

                if DEBUG:
                    print('Restarting: ' + agent_id)

                split_launch_command = launch_command.split()
                split_launch_command[1] = "agents/"+split_launch_command[1]

                running_agents[agent_id] = subprocess.Popen(split_launch_command)
                time.sleep(1)
                count += 1
            else:
                break

            if DEBUG:
                print(agent_id +' expiration_date is set at: ' + str(expiration_date))
                print(agent_id +' system time is set at: ' + str(time.time()))
                print(expiration_date - time.time())
            time.sleep(1)
        terminate_agent(agent_id)
        
    else:
        if DEBUG:
            print('Agent:'+agent_id+' does not exist')

def register_agent(agent_id, launch_command, expiration_date):
#    lock = threading.Lock()
    lock.acquire()
    if time.time() < expiration_date:
        agent_pool.append({'agent_name':agent_id, 'launch':launch_command, 'expires':expiration_date})
        agent_map = open('agent_map.txt', 'w+')
        json.dump(agent_pool, agent_map)
        agent_map.close()

        run_agent(agent_id = agent_id)
    else:
        if DEBUG:
            print('Cannot register and run agent since it is already expired')
    lock.release()

def run_agent(agent_id):

    expiration_date = None
    launch_command = None

    for agent in agent_pool:
        if agent['agent_name'] == agent_id:
            launch_command = agent['launch']
            expiration_date = agent['expires']
            break
        else:
            pass

    if expiration_date is not None and launch_command is not None:
        if time.time() < expiration_date:
            split_launch_command = launch_command.split()
            split_launch_command[1] = "agents/"+split_launch_command[1]

            running_agents[agent_id] = subprocess.Popen(split_launch_command)

            if DEBUG:
                print('-----------------Starting-----------------')
                print(agent_id + ' with command ' + launch_command)
                print('------------------------------------------')

            expire_monitors[agent_id] = threading.Thread(target=agent_expiration_monitor, args=(agent_id,))
            expire_monitors[agent_id].start()
        else:
            if DEBUG:
                print('Agent has already expired will terminate from system')
            terminate_agent(agent_id)
            return
    else:
        if DEBUG:
            print('Agent does not exist')
        return





####################################################################################################################
#######################################WEBSOCKET SERVER PRELIM TESTING##############################################
####################################################################################################################
def on_message(ws, message):
    message_dict = json.loads(message)
#    lock = threading.Lock()

    if DEBUG:
        print(message)
        if message_dict['method'] == 'message':
            print("###########THIS IS A MESSAGE#############")
            for key, value in message_dict.items():
                print(key, value)
            print("############END OF MESSAGE###############")
##############################################################################################################
##############################################################################################################
########################################Check for the correct parameters######################################
    if message_dict['method'] == 'message' and message_dict['params']['service_name'][1:] == service_name_1:
        pwd = os.getcwd()
        save_path = pwd + '/agents/'
        try:
            params = message_dict['params']['parameters']
            if DEBUG:
                print(params)
            agent_name = params['agent']
            launch_cmd = params['launch'] #for now launch_cmd will be "<python/python3/whatever> <AAAA.py>"
            expires = float(params['expires'])

            tempsavepath = os.path.join(save_path, launch_cmd.split()[1])

            #############Save The Agent##############
            lock.acquire()
            savefile = open(tempsavepath, "w+")
            savefile.write(base64.b64decode(params['agent_code'].encode('UTF-8')).decode('UTF-8'))
            savefile.close()
            lock.release()

            if DEBUG:
                print('forwarding message payload to agent_register')
                print('agent_name: ' + agent_name)
                print('launch_cmd: ' + launch_cmd)
                print('expires: ' + str(expires))
            try:
                register_agent(agent_id=agent_name, launch_command=launch_cmd, expiration_date=expires)
            except:
                if DEBUG:
                    print('agent_register forwarding failed')
        except:
            if DEBUG:
                print('Incorrect Parameters will not forward to agent_register')

    elif message_dict['method'] == 'message' and message_dict['params']['service_name'][1:] == service_name_2:
        try:
            params = message_dict['params']['parameters']
            terminate_target = params['agent']
            try:
                terminate_agent(agent_id=terminate_target)
            except:
                if DEBUG:
                    print('Could not terminate/find corresponding agent_id')
                pass
        except:
            if DEBUG:
                print('Incorrect Parameters | No Agent to terminate')

    else:
        if DEBUG:
            print('Not a message/ Not a matching service')
        pass


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
        payload['params'] = {"service_name":service_name_1}
        
        ws.send(json.dumps(payload))

        payload['id'] = counter + 1
        payload['params'] = {"service_name":service_name_2}
        ws.send(json.dumps(payload))

    opening = threading.Thread(target=run)
    opening.start()
####################################################################################################################
####################################################################################################################
####################################################################################################################



if __name__ == "__main__":
    #Attempt to load in our previous agent mapping if not create the agent map file which will store our mapping
    try:
        agent_map = open('agent_map.txt', 'r+')
        agent_pool = json.load(agent_map)
        agent_map.close()

    except:
        agent_map = open('agent_map.txt', 'w+')
        json.dump(agent_pool, agent_map)
        agent_map.close()

    #Check to see if any agents are running and terminate so we can remap and keep track of them
    if DEBUG:
        print(agent_pool)
        print(len(agent_pool))
    if len(agent_pool) > 0:
        agent_ids = []
        for agent in agent_pool:
            agent_ids.append(agent['launch'].split()[1])

        if DEBUG:
            print(agent_ids)
        
        agent_pids = psutil.pids()
        for pid in agent_pids:
            try:
                if any(x in psutil.Process(pid).cmdline()[1] for x in agent_ids):
                    if DEBUG:
                        print('----------------Terminated----------------')
                        print(psutil.Process(pid).cmdline())
                        print(pid)
                        print('------------------------------------------')
                    psutil.Process(pid).terminate()
            except:
                continue

        temp_agent_pool = agent_pool[:]

        for agent in temp_agent_pool:
            try:
                if DEBUG:
                    print(agent['agent_name'] + ' is trying to relaunch agents')
                run_agent(agent_id = agent['agent_name'])
            except:
                if DEBUG:
                    print('Nothing in temp agent pool')

####################################################################################################################
#######################################WEBSOCKET SERVER PRELIM TESTING##############################################
####################################################################################################################

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

####################################################################################################################
####################################################################################################################
####################################################################################################################

