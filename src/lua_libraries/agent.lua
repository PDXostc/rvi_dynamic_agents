local cjson = require("cjson.safe")
local sleep = require("socket")
local ldbus = require("ldbus")

local agent = {
    conn = assert(ldbus.bus.get("session"))
}

assert(assert(ldbus.bus.request_name(agent.conn , "dynamicagent.signal.sink" , {replace_existing = true})) == "primary_owner" , "Not Primary Owner")

-- DBus signals to subscribe to --
assert(ldbus.bus.add_match(agent.conn , "type='signal',interface='bus.can.update.can_medium_speed'"))
-- assert(ldbus.bus.add_match(agent.conn , "type='signal',interface='com.jlr.fmradio'"))
-- assert(ldbus.bus.add_match(agent.conn , "type='signal',interface='com.jlr.'"))
----------------------------------

agent.conn:flush()

local function get_event()
    while agent.conn:read_write(0) do
        local msg = agent.conn:pop_message()
        if not msg then
            ;
        elseif msg:get_type () == 'signal' then
            local iter = ldbus.message.iter.new()
            if msg:iter_init(iter) then
                if iter:get_arg_type() == ldbus.types.string then
                    local payload = cjson.decode(iter:get_basic())
                    if payload == nil then
                    elseif payload['signal_type'] == 'VEHICLE_SIGNAL' then
                        agent.medium_speed_can_table[payload['signal_id']] = payload['value']
                        return payload
                    elseif payload['signal_type'] == 'HMI_EVENT' then
                        return payload
                    else 
                    end
                end
            end
        end
    end
end

local function get_signals_table()
    local msg = assert(ldbus.message.new_method_call("bus.can.medium_speed" , "/bus/can/can_medium_speed/object" , "bus.can.request.can_medium_table" , "request_can_table") , "Message Null")
    local iter = ldbus.message.iter.new ()
    msg:iter_init_append(iter)
    local reply = assert(agent.conn:send_with_reply_and_block(msg))

    assert(reply:iter_init(iter), "Message has no arguments")
    return cjson.decode(iter:get_basic())
end

local function dbus_connected()
    return agent.conn:read_write_dispatch()
end

agent.get_event = get_event
-- agent.get_signals_table = get_signals_table
agent.dbus_connected = dbus_connected
agent.medium_speed_can_table = get_signals_table()

return agent