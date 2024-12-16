import uvicorn

import engineio

eio = engineio.AsyncServer(async_mode='asgi')
app = engineio.ASGIApp(eio, static_files={
    '/': 'simple.html',
    '/static': 'static',
})


@eio.on('connect')
def connect(sid, environ):
    print("connect ", sid)


@eio.on('message')
async def message(sid, data):
    print('message from', sid, data)
    await eio.send(sid, 'Thank you for your message!')


@eio.on('disconnect')
def disconnect(sid, reason):
    print('disconnect ', sid, reason)


if __name__ == '__main__':
    uvicorn.run(app, host='127.0.0.1', port=5000)
