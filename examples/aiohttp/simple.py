from aiohttp import web

import engineio

eio = engineio.AsyncServer(async_mode='aiohttp')
app = web.Application()
eio.attach(app)


async def index(request):
    with open('simple.html') as f:
        return web.Response(text=f.read(), content_type='text/html')


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


app.router.add_static('/static', 'static')
app.router.add_get('/', index)


if __name__ == '__main__':
    web.run_app(app)
