local websocket = require("websocket")
local json = require("cjson.safe")
local time = require("time")

local uuid = "DEFAULT_UUID"
local full_path = (arg[0]):match("^.+/(.+)$")

if full_path == nil then
    full_path = arg[0]
end

-- COMMENT THIS SECTION OUT AND CHANGE uuid IF NOT USING DEFAULT RVI UUID --
-- local cmdline = io.open("/proc/cmdline")
-- local read_file = cmdline:read("*all")
-- cmdline.close()

-- for i in string.gmatch(read_file, "%S+") do
--     if string.match(i, "root=UUID=") then
--         uuid = string.gsub(i, "root=UUID=", "")
--     end
-- end
-- ---------------------------------------------------------------------- --

local rvi = {}

local ws_target_host = "ws://localhost:9008"
local ws_target_topic = "rvi"

local client = websocket.client.sync()

local function message(service, payload)
    local to_send = {}
    to_send['jsonrpc'] = '2.0'
    to_send['id'] = tostring(time.now())
    to_send['method'] = 'message'
    to_send['params'] = {}
    to_send['params']['service_name'] = service
    to_send['params']['timeout'] = time.now() + 60
    
    to_send['params']['parameters'] = {}
    to_send['params']['parameters']['timestamp'] = tostring(time.now())
    to_send['params']['parameters']['agent_id'] = full_path
    to_send['params']['parameters']['uuid'] = uuid
    to_send['params']['parameters']['payload'] = payload

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
