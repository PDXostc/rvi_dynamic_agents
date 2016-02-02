-- local black_list = {"io", "require"}
local to_load = {}
to_load["time"] = true
to_load["cjson"] = true
to_load["rvi"] = true
to_load["agent"] = true

local white_list = {}
-- Lua Defaults
white_list["setmetatable"] = true
white_list["rawget"] = true
white_list["dofile"] = true
white_list["table"] = true
white_list["collectgarbage"] = true
white_list["math"] = true
white_list["loadfile"] = false		--RESTRICT
white_list["_G"] = true
white_list["load"] = true
white_list["getmetatable"] = true
white_list["coroutine"] = true
white_list["select"] = true
white_list["type"] = true
white_list["ipairs"] = true
white_list["error"] = true
white_list["rawset"] = true
white_list["string"] = true
white_list["print"] = true
white_list["rawlen"] = true
white_list["assert"] = true
white_list["xpcall"] = true
white_list["pcall"] = true
white_list["debug"] = true
white_list["bit32"] = true
white_list["arg"] = true
white_list["utf8"] = true
white_list["rawequal"] = true
white_list["pairs"] = true
white_list["tostring"] = true
white_list["os"] = false 			-- RESTRICT
white_list["io"] = false 			-- RESTRICT
white_list["next"] = true
white_list["tonumber"] = true
white_list["require"] = false 		-- RESTRICT
white_list["package"] = false		-- RESTRICT
white_list["_VERSION"] = true
-- End Lua Defaults


-- Append to_load functions onto our white_list table
for key, value in pairs(to_load) do 
    white_list[key] = value 
end

-- Load our whitelisted libraries, global variable name == package name
for key, value in pairs(to_load) do
    load("_G." .. key .. " = require(\"" .. key .. "\")")()
end

-- 
for key, value in pairs(_G) do 
    if white_list[tostring(key)] then
        
    else
        load("_G." .. tostring(key) .. " = nil")()
    end
end
