from sanic import Sanic
from sanic.response import html

import engineio

eio = engineio.AsyncServer(async_mode='sanic')
app = Sanic()
eio.attach(app)


@app.route('/')
async def index(request):
    with open('simple.html') as f:
        return html(f.read())


@eio.on('connect')
def connect(sid, environ):
    print("connect ", sid)


@eio.on('message')
async def message(sid, data):
    print('message from', sid, data)
    await eio.send(sid, 'Thank you for your message!', binary=False)


@eio.on('disconnect')
def disconnect(sid):
    print('disconnect ', sid)


app.static('/static', './static')


if __name__ == '__main__':
    app.run()
