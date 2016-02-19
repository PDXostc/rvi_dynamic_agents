## Important Dependencies (Currently only tested on Ubuntu) ##
* Python 2.X
* Python 3.X
* pip/pip3 (Depending on what version of Python you choose to run)

## Requiements ##


## Client Side Deployment ##
	1. Make sure RVI is running
	2. Clone the repo
	3. cd into repo i.e. "cd rvi_dynamic_agents"
	4. Make sure if you are tracking can signals that you have enabled your can link "sudo ip link set can0 up type can bitrate <XXXXX>" 
	5. python3 agenthandler.py

## Deploying Agents ##


lua dbus bindings for ubuntu need header and arch files
sudo apt-get -y install dbus libdbus-1-dev libdbus-glib-1-2 libdbus-glib-1-dev