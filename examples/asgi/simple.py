import os
import uvicorn

import engineio

eio = engineio.AsyncServer(async_mode='asgi')
app = engineio.ASGIApp(eio, static_files={
    '/': {'content_type': 'text/html', 'filename': 'simple.html'},
    '/static/engine.io.js': {'content_type': 'application/javascript',
                             'filename': 'static/engine.io.js'}
})


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


if __name__ == '__main__':
    uvicorn.run(app, '127.0.0.1', 5000)
