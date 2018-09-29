import six
import sys
import time

from . import exceptions
from . import packet
from . import payload


class Socket(object):
    """An Engine.IO socket."""
    upgrade_protocols = ['websocket']

    def __init__(self, server, sid):
        self.server = server
        self.sid = sid
        self.queue = self.create_queue()
        self.last_ping = time.time()
        self.connected = False
        self.upgraded = False
        self.closing = False
        self.closed = False

    def create_queue(self):
        return getattr(self.server._async['queue'],
                       self.server._async['queue_class'])()

    def poll(self):
        """Wait for packets to send to the client."""
        try:
            packets = [self.queue.get(timeout=self.server.ping_timeout)]
            self.queue.task_done()
        except self.server._async['queue'].Empty:
            raise exceptions.QueueEmpty()
        if packets == [None]:
            return []
        while True:
            try:
                packets.append(self.queue.get(block=False))
                self.queue.task_done()
            except self.server._async['queue'].Empty:
                break
        return packets

    def receive(self, pkt):
        """Receive packet from the client."""
        packet_name = packet.packet_names[pkt.packet_type] \
            if pkt.packet_type < len(packet.packet_names) else 'UNKNOWN'
        self.server.logger.info('%s: Received packet %s data %s',
                                self.sid, packet_name,
                                pkt.data if not isinstance(pkt.data, bytes)
                                else '<binary>')
        if pkt.packet_type == packet.PING:
            self.last_ping = time.time()
            self.send(packet.Packet(packet.PONG, pkt.data))
        elif pkt.packet_type == packet.MESSAGE:
            self.server._trigger_event('message', self.sid, pkt.data,
                                       run_async=self.server.async_handlers)
        elif pkt.packet_type == packet.UPGRADE:
            self.send(packet.Packet(packet.NOOP))
        elif pkt.packet_type == packet.CLOSE:
            self.close(wait=False, abort=True)
        else:
            raise exceptions.UnknownPacketError()

    def check_ping_timeout(self):
        """Make sure the client is still sending pings.

        This helps detect disconnections for long-polling clients.
        """
        if self.closed:
            raise exceptions.SocketIsClosedError()
        if time.time() - self.last_ping > self.server.ping_timeout:
            self.server.logger.info('%s: Client is gone, closing socket',
                                    self.sid)
            self.close(wait=False, abort=True)
            return False
        return True

    def send(self, pkt):
        """Send a packet to the client."""
        if not self.check_ping_timeout():
            return
        self.queue.put(pkt)
        self.server.logger.info('%s: Sending packet %s data %s',
                                self.sid, packet.packet_names[pkt.packet_type],
                                pkt.data if not isinstance(pkt.data, bytes)
                                else '<binary>')

    def handle_get_request(self, environ, start_response):
        """Handle a long-polling GET request from the client."""
        connections = [
            s.strip()
            for s in environ.get('HTTP_CONNECTION', '').lower().split(',')]
        transport = environ.get('HTTP_UPGRADE', '').lower()
        if 'upgrade' in connections and transport in self.upgrade_protocols:
            self.server.logger.info('%s: Received request to upgrade to %s',
                                    self.sid, transport)
            return getattr(self, '_upgrade_' + transport)(environ,
                                                          start_response)
        try:
            packets = self.poll()
        except exceptions.QueueEmpty:
            exc = sys.exc_info()
            self.close(wait=False)
            six.reraise(*exc)
        return packets

    def handle_post_request(self, environ):
        """Handle a long-polling POST request from the client."""
        length = int(environ.get('CONTENT_LENGTH', '0'))
        if length > self.server.max_http_buffer_size:
            raise exceptions.ContentTooLongError()
        else:
            body = environ['wsgi.input'].read(length)
            p = payload.Payload(encoded_payload=body)
            for pkt in p.packets:
                self.receive(pkt)

    def close(self, wait=True, abort=False):
        """Close the socket connection."""
        if not self.closed and not self.closing:
            self.closing = True
            self.server._trigger_event('disconnect', self.sid, run_async=False)
            if not abort:
                self.send(packet.Packet(packet.CLOSE))
            self.closed = True
            if wait:
                self.queue.join()
            del self.server.sockets[self.sid]

    def _upgrade_websocket(self, environ, start_response):
        """Upgrade the connection from polling to websocket."""
        if self.upgraded:
            raise IOError('Socket has been upgraded already')
        if self.server._async['websocket'] is None or \
                self.server._async['websocket_class'] is None:
            # the selected async mode does not support websocket
            return self.server._bad_request()
        websocket_class = getattr(self.server._async['websocket'],
                                  self.server._async['websocket_class'])
        ws = websocket_class(self._websocket_handler)
        return ws(environ, start_response)

    def _websocket_handler(self, ws):
        """Engine.IO handler for websocket transport."""
        # try to set a socket timeout matching the configured ping interval
        for attr in ['_sock', 'socket']:  # pragma: no cover
            if hasattr(ws, attr) and hasattr(getattr(ws, attr), 'settimeout'):
                getattr(ws, attr).settimeout(self.server.ping_timeout)

        if self.connected:
            # the socket was already connected, so this is an upgrade
            self.queue.join()  # flush the queue first

            pkt = ws.wait()
            if pkt != packet.Packet(packet.PING,
                                    data=six.text_type('probe')).encode(
                                        always_bytes=False):
                self.server.logger.info(
                    '%s: Failed websocket upgrade, no PING packet', self.sid)
                return []
            ws.send(packet.Packet(
                packet.PONG,
                data=six.text_type('probe')).encode(always_bytes=False))
            self.send(packet.Packet(packet.NOOP))

            pkt = ws.wait()
            decoded_pkt = packet.Packet(encoded_packet=pkt)
            if decoded_pkt.packet_type != packet.UPGRADE:
                self.upgraded = False
                self.server.logger.info(
                    ('%s: Failed websocket upgrade, expected UPGRADE packet, '
                     'received %s instead.'),
                    self.sid, pkt)
                return []
            self.upgraded = True
        else:
            self.connected = True
            self.upgraded = True

        # start separate writer thread
        def writer():
            while True:
                packets = None
                try:
                    packets = self.poll()
                except exceptions.QueueEmpty:
                    break
                if not packets:
                    # empty packet list returned -> connection closed
                    break
                try:
                    for pkt in packets:
                        ws.send(pkt.encode(always_bytes=False))
                except:
                    break
        writer_task = self.server.start_background_task(writer)

        self.server.logger.info(
            '%s: Upgrade to websocket successful', self.sid)

        while True:
            p = None
            try:
                p = ws.wait()
            except Exception as e:
                # if the socket is already closed, we can assume this is a
                # downstream error of that
                if not self.closed:  # pragma: no cover
                    self.server.logger.info(
                        '%s: Unexpected error "%s", closing connection',
                        self.sid, str(e))
                break
            if p is None:
                # connection closed by client
                break
            if isinstance(p, six.text_type):  # pragma: no cover
                p = p.encode('utf-8')
            pkt = packet.Packet(encoded_packet=p)
            try:
                self.receive(pkt)
            except exceptions.UnknownPacketError:
                pass
            except exceptions.SocketIsClosedError:
                self.server.logger.info('Receive error -- socket is closed')
                break
            except:  # pragma: no cover
                # if we get an unexpected exception we log the error and exit
                # the connection properly
                self.server.logger.exception('Unknown receive error')
                break

        self.queue.put(None)  # unlock the writer task so that it can exit
        writer_task.join()
        self.close(wait=True, abort=True)

        return []
