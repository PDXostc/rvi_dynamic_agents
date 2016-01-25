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
import agenthandler_config as settings
import rvi_ws

try:
    import thread
#TODO use Threading instead of _thread in python3
except ImportError:
    import _thread as thread


#DEBUG MESSAGING PRINTOUTS
DEBUG = settings.DEBUG_TOGGLE

#Agent Handler Globals
#agent_pool = Agents that are currently registered and that we are keeping track of
#agent_map = map of our agent_pool that will be stored in a memory to keep running even if case of power cycles
#running_agents = dictionary of running processes which can be terminated if needed
#expire_monitor_threads = threads that are started to watch for an agent expiration

running_agents = {}
expire_monitors = {}
agent_map = []
agent_pool = []
expire_monitor_threads = {}

#RVI Params
#The services that we must register in order for the agenthandler to receive an agent+run and a service to terminate
#The agent_report_service is the agent_report service which agents can invoke to send data to
services_to_register = {}

agent_report_service = settings.RVI_AGENT_REPORT_SERVICE

#Get the RVI websocket server location to connect to
host=settings.RVI_WS_HOST

#Global lock variable for threads to grab when they are performing an action which should not be interrupted
lock = threading.Lock()

def print_debug(message):
    if DEBUG:
        print(message)
    else:
        pass

def force_terminate(to_terminate):

    all_pids = psutil.pids()
    for pid in all_pids:
        try:
            if any(x in psutil.Process(pid).cmdline()[1] for x in to_terminate):
                print_debug('----------------Terminated----------------')
                print_debug(psutil.Process(pid).cmdline())
                print_debug(pid)
                print_debug('------------------------------------------')
                psutil.Process(pid).terminate()
        except:
            continue

def lookup_id(agent_id):

    for agent in agent_pool:
        if agent['agent_name'] == agent_id:
            launch_command = agent['launch']
            expiration_date = agent['expires']
            print_debug("Lookup_id has found "+agent_id)
            return launch_command, expiration_date
        else:
            return None, None


#The message should be a pythonic dictionary containing key value pairs of whatever you wish to send
def report(message):

    lock.acquire()

    message_dict = {}
    message_dict['payload'] = message
    message_dict['timestamp'] = str(time.time())
    message_dict['agent_id'] = sys.argv[0][7:len(sys.argv[0])-3]
    payload = {'jsonrpc':"2.0", 'id':str(time.time()), 'method':"message"}
    payload['params'] = {'service_name':agent_report_service,
                            'timeout':(int(time.time())+60), 'parameters':message_dict}
    try:
        ws1 = websocket.create_connection(host)
        print_debug(payload)
        ws1.send(json.dumps(payload))
        # ws.close()
    except:
        print_debug('Could not send agent_report')

    lock.release()

#terminate_agent accepts an agent_id which is a string which represents the agent_name in the global agent_pool
def terminate_agent(agent_id):

    lock.acquire()
    
    pwd = os.getcwd()
    save_path = pwd + settings.AGENT_SAVE_DIRECTORY

    #Grab the agent's corresponding launch_command and expiration_date
    launch_command, expiration_date = lookup_id(agent_id)

    #load the path the agent's code exists on
    try:
        tempdeletepath = os.path.join(save_path, launch_command.split()[1])
    except:
        print_debug("Could not get tempdeletepath")

    #Terminate the subprocess that contains the running agent
    try:
        running_agents[agent_id].terminate()
        print_debug('---------------Terminating----------------')
        print_debug(agent_id + launch_command + str(expiration_date))
        print_debug('---------------Terminating----------------')
    except:
        print_debug('No running agent with id:' + agent_id)

    #remove the agent from the agent_pool and update the hard_coded file
    try:
        agent_pool.remove({'agent_name':agent_id, 'launch':launch_command, 'expires':expiration_date})
    except:
        print_debug('Agent does not exist in agent_pool')
        print_debug(agent_pool)
    try:
        agent_map = open('agent_map.txt', 'w+')
        json.dump(agent_pool, agent_map)
        agent_map.close()
    except:
        print_debug('Could not write current agent pool to memory')

        agent_ids = []
        for agent in agent_pool:
            agent_ids.append(agent['launch'].split()[1])

    #Double check that process is actually killed if subprocess.terminate() did not kill it
    #Will kill any python things that the agent spawned
    to_terminate = [agent_id]
    force_terminate(to_terminate)            

    #Remove the agent's code on our local filesystem 
    try:
        os.remove(tempdeletepath)
    except:
        print_debug('Could not delete file')

    lock.release()

#agent_expiration_monitor will take in an agent_id much like the terminate agent function and will create a thread
#that is tracked in expire_mointor_threads dict that will monitor the agent so that if it dies prematurely will try
#to restart that agent or if it expires based on the unix epoch time will call the terminate function.
def agent_expiration_monitor(agent_id):

    count = 0
    expire_monitor_threads[agent_id] = threading.current_thread()
    launch_command, expiration_date = lookup_id(agent_id)

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

                print_debug('Restarting: ' + agent_id)

                split_launch_command = launch_command.split()
                split_launch_command[1] = settings.AGENT_SAVE_DIRECTORY[1:]+split_launch_command[1]

                running_agents[agent_id] = subprocess.Popen(split_launch_command)
                time.sleep(1)
                count += 1
            else:
                break

            print_debug(agent_id +' expiration_date is set at: ' + str(expiration_date))
            print_debug(agent_id +' system time is set at: ' + str(time.time()))
            print_debug(expiration_date - time.time())
            time.sleep(1)

        terminate_agent(agent_id)
        
    else:
        print_debug('Agent:'+agent_id+' does not exist')
#Registering an agent requires 3 parameters
#agent_id = string unique name of the id to create and save into the global agent_pool
#launch_command = string of how to launch the agent (e.g. python3 myscript.py <variables>)
#expiration_date = time in unix epoch format for when we should terminate the agent.
def register_agent(agent_id, launch_command, expiration_date):

    lock.acquire()

    if time.time() < expiration_date:
        agent_pool.append({'agent_name':agent_id, 'launch':launch_command, 'expires':expiration_date})
        agent_map = open('agent_map.txt', 'w+')
        json.dump(agent_pool, agent_map)
        agent_map.close()

        run_agent(agent_id = agent_id)
    else:
        print_debug('Cannot register and run agent since it is already expired')
    lock.release()

#Start up the agent and make it known in our running agent_pool global. Takes in the agent_id string
def run_agent(agent_id):

    launch_command, expiration_date = lookup_id(agent_id)

    if expiration_date is not None and launch_command is not None:
        if time.time() < expiration_date:
            split_launch_command = launch_command.split()
            split_launch_command[1] = "agents/"+split_launch_command[1]

            running_agents[agent_id] = subprocess.Popen(split_launch_command)

            print_debug('-----------------Starting-----------------')
            print_debug(agent_id + ' with command ' + launch_command)
            print_debug('------------------------------------------')

            expire_monitors[agent_id] = threading.Thread(target=agent_expiration_monitor, args=(agent_id,))
            expire_monitors[agent_id].start()
        else:
            print_debug('Agent has already expired will terminate from system')
            terminate_agent(agent_id)
            return
    else:
        print_debug('Agent does not exist')
        return

def new_agent(agent, launch, expires, agent_code):

    pwd = os.getcwd()
    save_path = pwd + settings.AGENT_SAVE_DIRECTORY
    try:
        print_debug("In try handler")
        agent_name = agent
        launch_cmd = launch  #for now launch_cmd will be "<python/python3/whatever> <AAAA.py>"
        expiration = float(expires)

        tempsavepath = os.path.join(save_path, launch_cmd.split()[1])

        print_debug("got all correct params")
        #############Save The Agent##############
        lock.acquire()
        savefile = open(tempsavepath, "w+")
        savefile.write(base64.b64decode(agent_code.encode('UTF-8')).decode('UTF-8'))
        savefile.close()
        lock.release()

        print_debug('forwarding message payload to agent_register')
        print_debug('agent_name: ' + agent_name)
        print_debug('launch_cmd: ' + launch_cmd)
        print_debug('expires: ' + str(expiration))
        try:
            register_agent(agent_id=agent_name, launch_command=launch_cmd, expiration_date=expiration)
        except:
            print_debug('agent_register forwarding failed')
    except:
        print_debug('Incorrect Parameters new_agent failed')

def kill_agent(agent):

    try:
        terminate_target = agent
        print_debug("Terminating signal got for "+terminate_target)
        try:
            terminate_agent(agent_id=terminate_target)
        except:
            print_debug('Could not terminate/find corresponding agent_id')
            pass
    except:
        print_debug('Incorrect Parameters | No Agent to terminate')

#If agenthandler is called to run as the main agenthandler task and not just importing the RVI report messages
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
    print_debug(agent_pool)
    print_debug(len(agent_pool))

    if len(agent_pool) > 0:
        agent_ids = []
        for agent in agent_pool:
            agent_ids.append(agent['launch'].split()[1])

        print_debug(agent_ids)
        
        force_terminate(agent_ids)

        temp_agent_pool = agent_pool[:]

        for agent in temp_agent_pool:
            try:
                print_debug(agent['agent_name'] + ' is trying to relaunch agents')
                run_agent(agent_id = agent['agent_name'])
            except:
                print_debug('Nothing in temp agent pool')

    rvi_client = rvi_ws.rvi_ws_client(bundle_id = settings.SERVICE_BUNDLE, host = host, debug = DEBUG)

    services_to_register[settings.NEW_AGENT_SERVICE] = new_agent
    services_to_register[settings.TERMINATE_AGENT_SERVICE] = kill_agent

    print_debug(services_to_register)
    rvi_client.register_services(services_to_register)


    while True:

        if len(sys.argv) < 2:
            host = settings.RVI_WS_HOST
        else:
            host = sys.argv[1]

        rvi_client.set_host(host)

        if rvi_client.services_run() is None:
            print_debug('No RVI. Wait and retry.')
            time.sleep(2)
            continue

    try:
        while True:
            time.sleep(1.0)

    except KeyboardInterrupt:
        print('^C received, shutting down server')
