from aiohttp import web

import engineio

eio = engineio.AsyncServer(async_mode='aiohttp')
app = web.Application()
eio.attach(app)


async def index(request):
    with open('latency.html') as f:
        return web.Response(text=f.read(), content_type='text/html')


@eio.on('message')
async def message(sid, data):
    await eio.send(sid, 'pong', binary=False)


app.router.add_static('/static', 'static')
app.router.add_get('/', index)


if __name__ == '__main__':
    web.run_app(app)
