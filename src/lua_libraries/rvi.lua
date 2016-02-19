local websocket = require("websocket")
local json = require("cjson.safe")
local time = require("time")

local rvi = {}

local ws_target_host = "ws://localhost:8808"
local ws_target_topic = "rvi"

local client = websocket.client.sync()

local function message(service, payload)
    local to_send = {}
    to_send['jsonrpc'] = '2.0'
    to_send['id'] = tostring(time.now())
    to_send['method'] = 'message'
    to_send['params'] = {}
    to_send['params']['service_name'] = service
    to_send['params']['timeout'] = os.time() + 60
    
    to_send['params']['parameters'] = {}
    to_send['params']['parameters']['timestamp'] = tostring(time.now())
    to_send['params']['parameters']['agent_id'] = arg[0]
    for key, value in pairs(payload) do 
        to_send['params']['parameters'][key] = value 
    end

    client:connect(ws_target_host, ws_target_topic)
    local ok,close_was_clean,close_code,close_reason = client:send(json.encode(to_send),websocket.TEXT)
    client:close()

    if ok then
        return true
    else
        return false
    end
end

rvi.message = message

return rvi
