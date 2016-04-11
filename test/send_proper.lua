local host_prefix = "genivi.org/node/test-node/"

time.now()
time.sleep(1)
print(agent.medium_speed_can_table)

while agent.dbus_connected() do
	msg = agent.get_event
	break
end

rvi.message(host_prefix .. "smoketest/reply", { a = "why", b = "hello", c = "world" })
