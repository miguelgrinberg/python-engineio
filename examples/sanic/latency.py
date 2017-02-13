from sanic import Sanic
from sanic.response import HTTPResponse

import engineio

eio = engineio.AsyncServer(async_mode='sanic')
app = Sanic()
eio.attach(app)


@app.route('/')
async def index(request):
    with open('latency.html') as f:
        return HTTPResponse(body=f.read(), content_type='text/html')


@eio.on('message')
async def message(sid, data):
    await eio.send(sid, 'pong', binary=False)


app.static('/static', './static')


if __name__ == '__main__':
    app.run()
