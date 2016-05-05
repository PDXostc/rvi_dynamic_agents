#Do we wish to see debug messages on our agenthandler
DEBUG_TOGGLE = True

#What our service bundle will be called
SERVICE_BUNDLE = "dynamicagents"

#Services that we wish to register locally
NEW_AGENT_SERVICE = "agent"
TERMINATE_AGENT_SERVICE = "terminate_agent"

#The websocket host that our RVI websocket server is listening on
RVI_WS_HOST = "ws://localhost:9008"

#For future iterations when we confirm the status of the dynamic agents
RVI_AGENT_REPORT_SERVICE = "genivi.org/backend/dynamicagents/agent_report"

#Not an absolute path, this directory will append onto the current working directory that agenthandler is executed on
AGENT_SAVE_DIRECTORY = '/agents/'

#Absolute path to your local lua interpreter| MUST BE Lua VERSION 5.3
LUA_PATH = '/usr/local/bin/lua'

#DO NOT CHANGE THESE... Unless you change the src directory code 
#Relative path to where your agenthandler executes 
LUA_SANDBOX_PATH = '/lua_sandbox/'

#File name of the sandbox settings inside of your Lua Sanbdbox Path
LUA_SANDBOX_SETTINGS = 'lua_init.lua'