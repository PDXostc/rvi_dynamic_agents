## Important Dependencies (Currently only tested on Ubuntu) ##
* make (apt-get install make)
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

## Deploying Agents ##
