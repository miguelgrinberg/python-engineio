import eventlet
from eventlet import websocket
import six

from . import packet
from . import payload


class Socket(object):
    """An Engine.IO socket."""
    upgrade_protocols = ['websocket']

    def __init__(self, server, sid):
        self.server = server
        self.sid = sid
        self.queue = eventlet.queue.Queue()
        self.upgraded = False
        self.closed = False

    def poll(self):
        """Wait for packets to send to the client."""
        try:
            packets = [self.queue.get(timeout=self.server.ping_timeout)]
            self.queue.task_done()
        except eventlet.queue.Empty:
            raise IOError()
        try:
            packets.append(self.queue.get(block=False))
            self.queue.task_done()
        except eventlet.queue.Empty:
            pass
        return packets

    def receive(self, pkt):
        """Receive packet from the client."""
        self.server.logger.info('%s: Received packet %s with %s', self.sid,
                                packet.packet_names[pkt.packet_type],
                                pkt.data)
        if pkt.packet_type == packet.PING:
            self.send(packet.Packet(packet.PONG, pkt.data))
        elif pkt.packet_type == packet.MESSAGE:
            self.server._trigger_event('message', self.sid, pkt.data)
        elif pkt.packet_type == packet.UPGRADE:
            self.send(packet.Packet(packet.NOOP))
        else:
            raise ValueError

    def send(self, pkt):
        """Send a packet to the client."""
        if self.closed:
            raise IOError('Socket is closed')
        self.queue.put(pkt)
        self.server.logger.info('%s: Sending packet %s with %s', self.sid,
                                packet.packet_names[pkt.packet_type],
                                pkt.data)

    def handle_get_request(self, environ, start_response):
        """Handle a long-polling GET request from the client."""
        connections = environ.get('HTTP_CONNECTION', '').lower().split(',')
        transport = environ.get('HTTP_UPGRADE', '').lower()
        if 'upgrade' in connections and transport in self.upgrade_protocols:
            return getattr(self, '_upgrade_' + transport)(environ,
                                                          start_response)
        try:
            packets = self.poll()
        except IOError:
            self.close(wait=False)
            raise
        return packets

    def handle_post_request(self, environ):
        """Handle a long-polling POST request from the client."""
        length = int(environ.get('CONTENT_LENGTH', '0'))
        if length > self.server.max_http_buffer_size:
            raise ValueError()
        else:
            body = environ['wsgi.input'].read(length)
            p = payload.Payload(encoded_payload=body)
            for pkt in p.packets:
                self.receive(pkt)

    def close(self, wait=True):
        """Close the socket connection."""
        self.server._trigger_event('disconnect', self.sid)
        self.send(packet.Packet(packet.CLOSE))
        self.closed = True
        if wait:
            self.queue.join()

    def _upgrade_websocket(self, environ, start_response):
        """Upgrade the connection from polling to websocket."""
        if self.upgraded:
            raise IOError('Socket has been upgraded already')
        ws = websocket.WebSocketWSGI(self._websocket_handler)
        return ws(environ, start_response)

    def _websocket_handler(self, ws):
        """Engine.IO handler for websocket transport."""
        pkt = ws.wait()
        if pkt != packet.Packet(packet.PING,
                                data=six.text_type('probe')).encode(
                                    always_bytes=False):
            return
        ws.send(packet.Packet(packet.PONG, data=six.text_type('probe')).encode(
            always_bytes=False))
        self.send(packet.Packet(packet.NOOP))
        self.upgraded = True
        self.queue.join()

        pkt = ws.wait()
        if pkt != packet.Packet(packet.UPGRADE).encode(always_bytes=False):
            self.upgraded = False
            return

        def writer():
            while True:
                try:
                    packets = self.poll()
                except IOError:
                    break
                for pkt in packets:
                    ws.send(pkt.encode(always_bytes=False))

        writer_task = eventlet.spawn(writer)

        while True:
            p = ws.wait()
            if p is None:
                break
            if isinstance(p, six.text_type):  # pragma: no cover
                p = p.encode('utf-8')
            pkt = packet.Packet(encoded_packet=p)
            try:
                self.receive(pkt)
            except ValueError:
                pass
        self.close(wait=False)
        writer_task.wait()
