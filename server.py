import json
import socket
import threading

class Server(object):
    """
    A class that encapsulates the UDP server for the Remote-Controlled Camera
    Car system. This server uses a single UDP socket for all incoming and
    outgoing messages. Once started, it will indefinitely listen on its single
    socket, expecting all UDP messages to be JSON-formatted with a "type" which
    it will use to decide which registered handler to call. This server also
    makes its socket available for thread-safe sending.
    """

    BUFFER_SIZE = 100

    def __init__(self, host, port):
        """
        Create a new UDP server that will listen forever on a single socket
        bound to the given host and port.
        """

        self.routes = {}
        self.handlers = {}
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.send_lock = threading.Lock()

        self.socket.bind((host, port))
        recv_thread = threading.Thread(target=self._receive_forever)
        recv_thread.start()

    def _receive_forever(self):
        """
        Start an infinite loop that will indefinitely block on a receive until
        a new message comes in. If the message is JSON-formatted and has a
        "type" key, then the corresponding handler will be run in a new thread.
        """

        while True:
            data, addr = self.socket.recvfrom(self.BUFFER_SIZE)
            try:
                body = json.loads(data)
            except json.JSONDecodeError:
                print('Received invalid JSON') # TODO: Logging
                continue
            if body['type'] in self.handlers:
                handler_thread = threading.Thread(
                    target=self.handlers[body['type']],
                    args=(self, body, addr)
                )
                handler_thread.start()
            else:
                print('Invalid message type', body)

    def send(self, data, address):
        """
        Send a message containing the given data from the server's UDP socket
        to the given address.
        """

        with self.send_lock:
            self.socket.sendto(data, address)

    def add_route(self, address1, address2):
        """
        Cache the source and destination addresses for a proxied-connection
        between a client application and a car, with this server acting as the
        proxy.
        """

        self.routes[address1] = address2
        self.routes[address2] = address1

    def get_destination(self, address):
        """
        Get the cached destination address that corresponds to a given source
        address.
        """

        return self.routes[address] if address in self.routes else None

    def add_handler(self, message_type, handler):
        """
        Register a handler function that will be called whenever a message of
        message_type is received.
        """

        self.handlers[message_type] = handler
