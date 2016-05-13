import base64
import json
import os
import psutil
import signal
import subprocess
import sys
import threading
import time

import agent_handler_config as settings
import rvi_ws

try:
    import thread
# TODO use Threading instead of _thread in python3
except ImportError:
    import _thread as thread


signal.signal(signal.SIGINT, signal.SIG_DFL)

# DEBUG MESSAGING PRINTOUTS
DEBUG = settings.DEBUG_TOGGLE

######## DEPRECATED IN VERSION 1.0| WAS ONLY FOR DEMO VERSION OF CODE ########
# The agent_report_service is the agent_report service which agents can invoke
# to send data to
# agent_report_service = settings.RVI_AGENT_REPORT_SERVICE

# Get the RVI websocket server location to connect to
host = settings.RVI_WS_HOST


def print_debug(message):
    if DEBUG:
        print(message)
    else:
        pass


def pwd(rel_path=None):
    """Return working directory or transform relative path into full one."""

    work_dir = os.path.dirname(os.path.realpath(__file__))

    if rel_path:
        # restrict path going level up from work_dir
        if rel_path[0] == '/':
            rel_path = rel_path[1:]

    if rel_path:
        work_dir = os.path.join(work_dir, rel_path)

    return work_dir


def sandbox_launch(launch_cmd):
    """Launch Lua script in the isolated sandbox."""

    sandbox_path = pwd(settings.LUA_SANDBOX_PATH)
    sandbox_file = os.path.join(sandbox_path, settings.LUA_SANDBOX_SETTINGS)

    command = '(cd {0}; LUA_INIT=@{1} {2})'.format(
        sandbox_path, sandbox_file, launch_cmd)

    print_debug(command)

    return command


class Agent(object):
    """Specific Agent instance."""

    def __init__(self, name, expiration_date, launch_command=None):
        self.name = name
        self.expiration = expiration_date

        self.process = None

        self.launch_command = launch_command
        if self.launch_command is None:
            self.launch_command = settings.LUA_PATH + ' ' + self.script_path

    @property
    def is_running(self):
        if self.process is not None:
            if self.process.poll() is None:
                return True

        return False

    @property
    def script_path(self):
        save_path = pwd(settings.AGENT_SAVE_DIRECTORY)
        return os.path.join(save_path, self.name + '.lua')

    def purge(self):
        """Remove Agent's code from disk."""

        try:
            os.remove(self.script_path)
        except OSError as e:
            print_debug('Failed to remove script of agent "%s": %s' % (
                self.name, e))

    def save_code(self, script_code):
        with open(self.script_path, 'w') as script:
            raw_code = base64.b64decode(script_code.encode('UTF-8'))
            script.write(raw_code.decode('UTF-8'))

    def start(self):
        """Start agent script in new process."""

        print_debug('Launching agent "%s" with command: %s' % (
            self.name, self.launch_command))

        # try to terminate any previous agent running
        self.force_terminate()

        self.process = subprocess.Popen(
            sandbox_launch(self.launch_command), shell=True)

    def terminate(self):
        """Terminate agent's subprocess."""

        print_debug('Terminating agent: %s' % self.name)

        self.process.terminate()

    def force_terminate(self):
        """Force termination of agent's process."""

        def is_my_process(cmdline):
            if cmdline and ' '.join(cmdline) == self.launch_command:
                return True
            return False

        all_pids = psutil.pids()

        for pid in all_pids:
            try:
                cmd_line = psutil.Process(pid).cmdline()

                if is_my_process(cmd_line):
                    print_debug('Terminating process "%s": %s' % (
                        pid, cmd_line))
                    psutil.Process(pid).terminate()
            except Exception as e:
                print_debug('Failed to force_terminate "%s": %s' % (
                    self.name, e))

    def __repr__(self):
        params = ', '.join([
            'name="%s"' % self.name,
            'expiration_date=%s' % self.expiration,
            'launch_command="%s"' % self.launch_command,
        ])
        return 'Agent(%s)' % params

    def to_json(self):
        return json.dumps(
            dict(name=self.name, expiration_date=self.expiration))

    @classmethod
    def from_json(cls, json_text):
        params = json.loads(json_text)
        return cls(**params)


class AgentPool(object):
    """Agent Pool to manage running agents in the system."""

    MAX_RESTARTS = 5  # max attempts to restart agent's process

    def __init__(self, storage_filename):
        self._pool = {}

        self.storage_filename = storage_filename

        # Global lock variable for threads to grab when they are performing
        # an action which should not be interrupted
        self.lock = threading.Lock()

    def __contains__(self, item):
        return item in self._pool

    def __len__(self):
        return len(self._pool)

    def __getitem__(self, key):
        return self._pool[key]

    def _monitor_handler(self, agent):
        """Monitor Handler for the Agents.

        Perform:
            1. Restart agent if it's process was terminated for some reason.
            2. Check expiration date and terminate process when expired.
        """

        restarts = 0

        while time.time() < agent.expiration:
            if agent.is_running:
                pass
            elif restarts < self.MAX_RESTARTS:
                restarts += 1
                print_debug('Restarting agent (attempt %d/%d): %s' % (
                    restarts, self.MAX_RESTARTS, agent.name))

                with self.lock:
                    agent.start()

                time.sleep(1)
            else:
                break

            print_debug('Agent "%s" will expire in %d s.' % (
                agent.name, agent.expiration - time.time()))
            time.sleep(1)

        self.terminate_agent(agent)

    def register_new_agent(self, agent_name, expiration_date, script_code):
        """Registering a new agent in the system."""

        print_debug('Registering agent: %s' % agent_name)

        with self.lock:
            agent = Agent(agent_name, expiration_date)
            try:
                agent.save_code(script_code)
            except IOError as e:
                print_debug('Saving agent code failed: %s' % e)
                return

            self.add_agent(agent)

        self.save_pool()

    def kill_agent(self, agent_name):
        """Kill agent by name."""

        if agent_name in self._pool:
            self.terminate_agent(self._pool[agent_name])
        else:
            print_debug(
                'Kill canceled, agent was not found in pool: %s' % agent_name)

    def add_agent(self, agent):
        """Add agent to the pool and run it."""

        print_debug('Adding new agent to the pool: %s' % agent)

        if time.time() < agent.expiration:
            try:
                agent.start()

                print_debug('Starting expiration monitor for: %s' % agent.name)
                agent.monitor = threading.Thread(
                    target=self._monitor_handler, args=(agent,))
                agent.monitor.start()
            except OSError as e:
                print_debug('Failed to run agent %s: %s' % (agent, e))
                return

            self._pool[agent.name] = agent
        else:
            print_debug(
                'Skipped adding agent since it is already expired: %s' % agent)

    def terminate_agent(self, agent):
        """Terminate the running agent and remove it from the pool."""

        with self.lock:
            try:
                agent.terminate()
            except OSError as e:
                print_debug('Failed to terminate agent "%s": %s' % (
                    agent.name, e))

            # Double check that process is actually killed if
            # subprocess.terminate() did not kill it
            # Will kill any python things that the agent spawned
            agent.force_terminate()
            agent.purge()

            # remove the agent from the pool
            try:
                del self._pool[agent.name]
            except KeyError:
                print_debug('Agent already removed from pool: %s' % agent)

        self.save_pool()

    def save_pool(self):
        """Save Agent Pool."""

        print_debug('Saving Agent Pool to disk...')

        with self.lock:
            with open(self.storage_filename, 'w') as f:
                for agent in self._pool.values():
                    f.write(agent.to_json())
                    f.write('\n')

    def load_pool(self):
        """Load Agent Pool."""

        print_debug('Loading Agent Pool from disk...')

        with self.lock:
            if not os.path.exists(self.storage_filename):
                print_debug(
                    'Agent Pool file not found: %s' % self.storage_filename)
                return

            with open(self.storage_filename, 'r') as f:
                for line in f:
                    agent = Agent.from_json(line)

                    if os.path.exists(agent.script_path):
                        self.add_agent(agent)
                    else:
                        print_debug(
                            'Agent skipped, no script file found: %s' % agent)


class RviServices(object):
    """RVI Service API."""

    def __init__(self, pool):
        self.pool = pool

    def new_agent(self, agent, expires, agent_code, launch=None):
        """Handle new agent incoming from RVI.

        Launch will be a hardcoded parameter for the time being.
        In future iterations we will support more programming languages.
        """

        print_debug('New Agent received from server: %s' % agent)

        try:
            agent_name = ''.join(agent.split())
        except AttributeError as e:
            print_debug('Incorrect Parameters, new_agent failed: %s' % e)
            return

        if agent_name in self.pool:
            msg = (
                'Agent with same name already exists, '
                'please terminate first or rename')
            print_debug(msg)
        else:
            # TODO: support custom launch command
            self.pool.register_new_agent(
                agent_name, float(expires), agent_code)

    def kill_agent(self, agent):
        try:
            print_debug('Server requested terminating agent: %s' % agent)
            agent_name = ''.join(agent.split())

            self.pool.kill_agent(agent_name)
        except AttributeError as e:
            print_debug('Incorrect Parameters: %s' % e)

        print_debug('Agent was terminated: %s' % agent_name)


# If agenthandler is called to run as the main agenthandler task and not just
# importing the RVI report messages
if __name__ == "__main__":
    agent_registry = AgentPool(storage_filename=pwd('agent_map.txt'))
    rvi_services = RviServices(pool=agent_registry)

    agent_registry.load_pool()

    print_debug('Loaded %d agent(s) to the pool.' % len(agent_registry))

    rvi_client = rvi_ws.rvi_ws_client(
        bundle_id=settings.SERVICE_BUNDLE, host=host, debug=DEBUG)

    # The services that we must register in order for the agenthandler
    # to receive an agent + run and a service to terminate
    services_to_register = {
        settings.NEW_AGENT_SERVICE: rvi_services.new_agent,
        settings.TERMINATE_AGENT_SERVICE: rvi_services.kill_agent,

    }
    print_debug(
        'Registering services: %s' % ', '.join(services_to_register.keys()))
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
