from eventlet import wsgi
import eventlet
from flask import Flask, render_template

import engineio

eio = engineio.Server()
app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')


@eio.on('connect')
def connect(sid, environ):
    print("connect ", sid)


@eio.on('message')
def message(sid, data):
    print('message from', sid, data)
    eio.send(sid, 'message received')


@eio.on('disconnect')
def disconnect(sid):
    print('disconnect ', sid)


if __name__ == '__main__':
    mapp = engineio.Middleware(eio, app)
    wsgi.server(eventlet.listen(('', 5000)), mapp)
