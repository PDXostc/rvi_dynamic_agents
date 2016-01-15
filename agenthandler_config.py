#Do we wish to see debug messages on our agenthandler
DEBUG_TOGGLE = True

#Services that we wish to register locally
NEW_AGENT_SERVICE = "dynamicagents/agent"
TERMINATE_AGENT_SERVICE = "dynamicagents/terminate_agent"

#The websocket host that our RVI websocket server is listening on
RVI_WS_HOST = "ws://localhost:8808"

#The remote backend target service we should send our messages to
RVI_AGENT_REPORT_SERVICE = "genivi.org/backend/dynamicagents/agent_report"

#Not an absolute path, this directory will append onto the current working directory that agenthandler is executed on
AGENT_SAVE_DIRECTORY = '/agents/'
