## Important Dependencies (Currently only tested on Ubuntu) ##
* Python 2.X 
* Python 3.X
* Python.h (apt-get install python-dev/python3-dev)
* dbus.h and dbus-arch-deps.h (apt-get -y install dbus libdbus-1-dev libdbus-glib-1-2 libdbus-glib-1-dev)
* pip/pip3 (Depending on what version of Python you choose to run)
* Lua 5.3.X
* Luarocks (Package Manager | Most recent version)
* Linux environment that allows symlinking

## Other important things to have ##
* A valid can database file (*.dbc) so you can input into our dbus can object simulator for tests (Has default fake emulator)


## Installing ##
Make sure that all dependencies are met before continuing
```bash
sudo <pip | pip3 > install -r ./deps/python/python_requirements.txt

sudo luarocks install ./deps/lua/ldbus-scm-0.rockspec DBUS_INCDIR=/<path>/<to>/dbus.h DBUS_ARCH_INCDIR=/<path>/<to>/dbus-arch-deps.h

sudo luarocks install ./deps/lua/lua-cjson-2.1devel-1.rockspec

sudo luarocks install ./deps/lua/luasocket-scm-0.rockspec

sudo luarocks install ./deps/lua-websockets-scm-1.rockspec

```

## Running checks ##

## Client Side Deployment ##
**NOTE: If you run the agent_handler as root you must make sure that your dbus session objects are also being run as root or else you will not be able to find them on the dbus!**

Edit the agent_handler_config.py file. You can change the name of the registered services and the RVI_WS_HOST is probably the most important setting to change to reflect what your actual node is using for the websocket server port.

If you wish to add additional signals into the agent sandbox for the time being you must do so manually in the ./src/lua/agent.lua file in the section "DBus signals to subscribe to" section.


## Deploying Agents ##
The current agent_handler code will spawn 2 RVI services. These 2 services are described below and what they are expected to have passed in.

```
<RVI_PREFIX>/dynamicagents/agent
Expected Parameters:
	agent = {
		Expected Type = String
		Description = A symbolic name of the agent we will be registering. This will be translated to the agent_id in how we reference the agents internally.
	}
	expires = {
		Expected Type = String or Float or Int of Unix Epoch time
		Description = A Unix Epoch time of when the agent should self terminate. 
	}
	agent_code = {
		Expected Type = Base64 Encoded String
		Description = The actual executable Lua code that is Base64 Encoded of UTF-8 Encoding. Expected Python encoding method is "base64.b64encode(<CODESTRING>.encode('UTF-8'))"
	}
	launch = { //NOT CURRENTLY USED
		Expected Type = String
		Description = Launch command of the script. Currently not used since we only support Lua sandboxing but future iterations may support all types of languages!
	}



<RVI_PREFIX>/dynamicagents/terminate_agent
Expected Parameters:
	agent = {
		Expected Type = String
		Description = A symbolic name of the agent we will be registering. This will be translated to the agent_id in how we reference the agents internally. Same agent string we used to register the agent on the client.
	}

```

## Current Agent API ##
The default Lua sandbox environment at the current moment can be found in the ./src/lua_libraries/lua_init.lua file. The 4 additional libraries that are include in addition to the base runtime environment are as follow:

```
cjson: 
	Documentation can be found at http://www.kyne.com.au/~mark/software/lua-cjson-manual.html

time:
	time.time() = {
		Expected Parameters:
			None

		Return = Unix Epoch timestamp with millisecond precision
	}
	time.sleep(n) = {
		Expected Parameters:
			n = {
				Expected Type = int | float
				Description = Number of seconds you wish your agent to sleep for
			}

		Return = void, agent process will sleep for specified number of seconds
	}

rvi:
	rvi.message(service,payload) = {
		Expected Parameters:
			service = {
				Expected Type = String
				Description = Target rvi service endpoint which you wish to send a message to. AKA a logging RVI service endpoint would be ideal.
			}
			payload = {
				Expected Type = Table
				Description = Table that is able to be cast into a JSON string. This can contain key values which you wish to report back to the backend server.
			}

		Return = True | False , depending on success or failure of message send
	}

agent:
	agent.medium_speed_can_table = Table to current medium speed can table value which was given by a invoked method call.

	agent.dbus_connected() = {
		Expected Parameters:
			None

		Return = True, Will block until True is returned thus notifying that there is something in the dbus message queue.
		Note = It would be best to use this as the main event loop i.e. while agent.dbus_connected() do...
	}

	agent.get_event() = {
		Expected Parameters:
			None
		Return = Table that will look like this:
			{
				signal_type = 'VEHICLE_SIGNAL',
				signal_id = int signal id,
				sig_value = int or float value,
			}
	}

```

Typical Event Loop code:
```Lua
while agent.dbus_connected() do 
	local msg = agent.get_event()

	-- Do something with the msg for example--	
	agent.medium_speed_can_table[signal] compare with msg[sig_value]

	...
	if condition do
		rvi.message(<service>, {a='b', c='d'})
	end
end
```