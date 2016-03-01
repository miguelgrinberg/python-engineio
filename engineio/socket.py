import time
import six

from . import packet
from . import payload


class Socket(object):
    """An Engine.IO socket."""
    upgrade_protocols = ['websocket']

    def __init__(self, server, sid):
        self.server = server
        self.sid = sid
        self.queue = self._create_queue()
        self.backlog = None
        self.last_ping = time.time()
        self.connected = False
        self.upgraded = False
        self.upgrading = False
        self.closed = False

    def poll(self):
        """Wait for packets to send to the client."""
        try:
            packets = [self.queue.get(timeout=self.server.ping_timeout)]
            self.queue.task_done()
        except self.server.async['queue'].Empty:
            raise IOError()
        if packets == [None]:
            return []
        try:
            packets.append(self.queue.get(block=False))
            self.queue.task_done()
        except self.server.async['queue'].Empty:
            pass
        return packets

    def receive(self, pkt):
        """Receive packet from the client."""
        self.server.logger.info('%s: Received packet %s data %s',
                                self.sid, packet.packet_names[pkt.packet_type],
                                pkt.data if not isinstance(pkt.data, bytes)
                                else '<binary>')
        if pkt.packet_type == packet.PING:
            self.last_ping = time.time()
            self.send(packet.Packet(packet.PONG, pkt.data))
        elif pkt.packet_type == packet.MESSAGE:
            self.server._trigger_event('message', self.sid, pkt.data,
                                       async=True)
        elif pkt.packet_type == packet.UPGRADE:
            self.send(packet.Packet(packet.NOOP))
        else:
            raise ValueError

    def send(self, pkt, _force=False):
        """Send a packet to the client. The packet may temporarily end up in
        a backlog if the connection is currently being upgraded; set
        ``_force`` to ``True`` to force the packet to be sent even if an
        upgrade is in progress."""
        if self.closed:
            raise IOError('Socket is closed')
        if time.time() - self.last_ping > self.server.ping_timeout:
            self.server.logger.info('%s: Client is gone, closing socket',
                                    self.sid)
            self.close(wait=False, abort=True)
            return
        if self.upgrading and not _force:
            self.backlog.put(pkt)
        else:
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
        except IOError as e:
            self.close(wait=False)
            raise e
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

    def close(self, wait=True, abort=False):
        """Close the socket connection."""
        self.server._trigger_event('disconnect', self.sid, async=False)
        if not abort:
            self.send(packet.Packet(packet.CLOSE))
        self.closed = True
        if wait:
            self.queue.join()

    def _create_queue(self):
        """Create a new queue to be used by the socket.

        The queue will be used either for storing outbound packets or for
        storing the packet backlog during an upgrade.
        """
        return getattr(self.server.async['queue'],
                       self.server.async['queue_class'])()

    def _flush_backlog(self):
        """Flushes the backlog where the outbound packets were being held
        during an upgrade by moving them to the outbound packet queue.
        """
        finished = False
        while not finished:
            try:
                packet = self.backlog.get(block=False)
                self.queue.put(packet)
            except self.server.async['queue'].Empty:
                finished = True

    def _upgrade_websocket(self, environ, start_response):
        """Upgrade the connection from polling to websocket."""
        if self.upgraded:
            raise IOError('Socket has been upgraded already')
        if self.server.async['websocket'] is None or \
                self.server.async['websocket_class'] is None:
            # the selected async mode does not support websocket
            return self.server._bad_request()
        websocket_class = getattr(self.server.async['websocket'],
                                  self.server.async['websocket_class'])
        ws = websocket_class(self._websocket_handler)
        return ws(environ, start_response)

    def _websocket_handler(self, ws):
        """Engine.IO handler for websocket transport."""
        if self.connected:
            # the socket was already connected, so this is an upgrade
            self.backlog = self._create_queue()
            self.upgrading = True

            self.queue.join()  # flush the queue first

            pkt = ws.wait()
            if pkt != packet.Packet(packet.PING,
                                    data=six.text_type('probe')).encode(
                                        always_bytes=False):
                self.server.logger.info(
                    '%s: Failed websocket upgrade, no PING packet', self.sid)
                return
            ws.send(packet.Packet(
                packet.PONG,
                data=six.text_type('probe')).encode(always_bytes=False))
            self.send(packet.Packet(packet.NOOP), _force=True)

            pkt = ws.wait()
            decoded_pkt = packet.Packet(encoded_packet=pkt)
            if decoded_pkt.packet_type != packet.UPGRADE:
                self.upgraded = False
                self.server.logger.info(
                    ('%s: Failed websocket upgrade, expected UPGRADE packet, '
                     'received %s instead.'),
                    self.sid, pkt)
            else:
                self.upgraded = True

            self._flush_backlog()
            self.backlog = None
            self.upgrading = False

            if not self.upgraded:
                return
        else:
            self.connected = True
            self.upgraded = True
            self.backlog = None
            self.upgrading = False

        def writer():
            while True:
                try:
                    packets = self.poll()
                except IOError:
                    break
                try:
                    for pkt in packets:
                        ws.send(pkt.encode(always_bytes=False))
                except:
                    break

        self.server.start_background_task(writer)

        self.server.logger.info(
            '%s: Upgrade to websocket successful', self.sid)

        while True:
            try:
                p = ws.wait()
            except:
                break
            if p is None:
                break
            if isinstance(p, six.text_type):  # pragma: no cover
                p = p.encode('utf-8')
            pkt = packet.Packet(encoded_packet=p)
            try:
                self.receive(pkt)
            except ValueError:
                pass
        self.close(wait=True, abort=True)
        self.queue.put(None)  # unlock the writer task so that it can exit
