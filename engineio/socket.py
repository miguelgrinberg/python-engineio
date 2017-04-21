import time
import six

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
        try:
            packets.append(self.queue.get(block=False))
            self.queue.task_done()
        except self.server._async['queue'].Empty:
            pass
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
                                       async=self.server.async_handlers)
        elif pkt.packet_type == packet.UPGRADE:
            self.send(packet.Packet(packet.NOOP))
        elif pkt.packet_type == packet.CLOSE:
            self.close(wait=False, abort=True)
        else:
            raise exceptions.UnknownPacketError()

    def send(self, pkt):
        """Send a packet to the client."""
        if self.closed:
            raise IOError('Socket is closed')
        if time.time() - self.last_ping > self.server.ping_timeout:
            self.server.logger.info('%s: Client is gone, closing socket',
                                    self.sid)
            self.close(wait=False, abort=True)
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
        except exceptions.QueueEmpty as e:
            self.close(wait=False)
            raise e
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
            reraise_exc = None
            try:
                self.server._trigger_event('disconnect', self.sid, async=False)
            except Exception as e:
                reraise_exc = e
            if not abort:
                self.send(packet.Packet(packet.CLOSE))
            self.closed = True
            if wait:
                self.queue.join()
            if reraise_exc:
                raise reraise_exc

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

        reraise_exc = None
        while True:
            p = None
            try:
                p = ws.wait()
            except:
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
            except Exception as e:
                # if we get an unexpected exception (such as something in an
                # application event handler) we close the connection properly
                # and then reraise the exception
                reraise_exc = e
                break

        self.queue.put(None)  # unlock the writer task so that it can exit
        writer_task.join()
        self.close(wait=True, abort=True)
        if reraise_exc:
            raise reraise_exc

        return []
