import argparse
import handlers

from server import Server
from utils import MsgType

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='RC Camera Car Server.')
    parser.add_argument('port', type=int, help='port to listen on')

    args = parser.parse_args()
    PORT = args.port
    HOST = ''

    server = Server(HOST, PORT)
    server.add_handler(MsgType.ACK, handlers.handle_ack)
    server.add_handler(MsgType.REG_USER, handlers.handle_register_user)
    server.add_handler(MsgType.REG_CAR, handlers.handle_register_car)
    server.add_handler(MsgType.LOGIN, handlers.handle_login)
    server.add_handler(MsgType.CONN_CAR, handlers.handle_connect_car)
    server.add_handler(MsgType.MOVE, handlers.handle_movement)
    server.add_handler(MsgType.SET_LED, handlers.handle_set_led)
