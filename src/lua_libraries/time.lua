local os = require("os")
local socket = require("socket")

time = {}

local function sleep(n)
	os.execute("sleep "..tonumber(n))
end

local function now()
	return socket.gettime()
end

time.sleep = sleep
time.now = now

return time
