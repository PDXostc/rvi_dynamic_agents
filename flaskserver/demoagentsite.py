from flask import Flask, render_template
from flask.ext.socketio import SocketIO, emit
import redis
import json
import time
# import logging

# logging.basicConfig()

app = Flask(__name__)
app.debug = True

socketio = SocketIO(app)

@app.route("/")
def hello():
        r = redis.StrictRedis(host='localhost',port=6379,db=0)

        agents = r.smembers('agent')

        payload = {}

        for item in agents:
            payload[item] = {}
            aitems = r.hgetall("agent:"+item)
            for key in aitems:
                k = key.decode('UTF-8')
                j = aitems[key].decode('UTF-8')
                payload[item][k] = j

        return render_template('index.html', 
        data=payload)

if __name__ == "__main__":
    app.run('0.0.0.0')


