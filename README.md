Important Dependencies (Currently only tested on Ubuntu)

Python 2.X
Python 3.X
python-can (python3 install)
websocket-client (python-pip3)
psutil (python-pip3)

--Optional for backend--
	flask 
	redis 

Requiements:
	1. RVI setup on both the client side and the server side and can communicate with each other.
		-Please refer to https://github.com/PDXostc/rvi_core for more information
	2. RVI backend is installed to push agents to client.
		-Please refer to https://github.com/PDXostc/rvi_backend for more information to find the backend w/ dynamic_agent code
	3. All dependencies are met
 
Server Side Deployment:
	0. Make sure RVI is running
	1. Clone the repo
	2. cd into repo i.e. "cd rvi_dynamic_agents"
	--Optional Redis Server and Flask Counter Demo Setup--
		a. Install flask and redis
		b. Make sure redis server is setup
		c. Change flasktest/hello.py to make sure your redis client will work if not using default setup
		d. python flasktest/hello.py
		e. Access and see reported agent counts at localhost:5000
	--End optional Section--
	3. python3 agentserver/agentserver.py

Client Side Deployment:
	0. Make sure RVI is running
	1. Clone the repo
	2. cd into repo i.e. "cd rvi_dynamic_agents"
	3. Make sure if you are tracking can signals that you have enabled your can link "sudo ip link set can0 up type can bitrate <XXXXX>" 
	4. python3 agenthandler.py

Deploying Agents:
	0. Make sure RVI is running
	1. Clone the rvi_backend repo
	2. Follow setup instructions for the rvi_backend repo
	3. Add a vehicle and make sure the vin is what you set up for RVI
	4. Add an Agent where launch command is how you would launch your script 
		-For example python3 script ABC.py would be launched with "python3 ABC.py"
	5. Add an update choosing which agent you wish to send to which vehicle and its expiration date
	6. Click checkbox and select start agent from dropdown list and hit go.
	7. Agent should not be running, you are also able to remotely terminate from this page.
