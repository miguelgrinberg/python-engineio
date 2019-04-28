import uvicorn

import engineio

eio = engineio.AsyncServer(async_mode='asgi')
app = engineio.ASGIApp(eio, static_files={
    '/': {'content_type': 'text/html', 'filename': 'latency.html'},
    '/static/engine.io.js': {'content_type': 'application/javascript',
                             'filename': 'static/engine.io.js'},
    '/static/style.css': {'content_type': 'text/css',
                          'filename': 'static/style.css'}
})


@eio.on('message')
async def message(sid, data):
    await eio.send(sid, 'pong', binary=False)


if __name__ == '__main__':
    uvicorn.run(app, host='127.0.0.1', port=5000)
