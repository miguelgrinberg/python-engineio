import os

import tornado.ioloop
from tornado.options import define, options, parse_command_line
import tornado.web

import engineio

define("port", default=8888, help="run on the given port", type=int)
define("debug", default=False, help="run in debug mode")

eio = engineio.AsyncServer(async_mode='tornado')


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("simple.html")


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


def main():
    parse_command_line()
    app = tornado.web.Application(
        [
            (r"/", MainHandler),
            (r"/engine.io/", engineio.get_tornado_handler(eio)),
        ],
        template_path=os.path.join(os.path.dirname(__file__), "templates"),
        static_path=os.path.join(os.path.dirname(__file__), "static"),
        debug=options.debug,
    )
    app.listen(options.port)
    tornado.ioloop.IOLoop.current().start()


if __name__ == "__main__":
    main()
