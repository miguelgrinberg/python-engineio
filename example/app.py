from flask import Flask, render_template

import engineio

eio = engineio.Server(async_mode='threading')
app = Flask(__name__)
app.wsgi_app = engineio.Middleware(eio, app.wsgi_app)


@app.route('/')
def index():
    return render_template('index.html')


@eio.on('connect')
def connect(sid, environ):
    print("connect ", sid)


@eio.on('message')
def message(sid, data):
    print('message from', sid, data)
    eio.send(sid, 'Thank you for your message!', binary=False)


@eio.on('disconnect')
def disconnect(sid):
    print('disconnect ', sid)


if __name__ == '__main__':
    # deploy with Werkzeug
    app.run(threaded=True)

    # deploy with eventlet
    # import eventlet
    # eventlet.wsgi.server(eventlet.listen(('', 5000)), app)

    # deploy with gevent
    # from gevent import pywsgi
    # pywsgi.WSGIServer(('', 5000), app).serve_forever()
