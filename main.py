import argparse
import handlers

from enum import IntEnum
from server import Server

class MsgType(IntEnum):
    REG_USER = 0
    REG_CAR = 1
    LOGIN = 2
    MOVEMENT = 3
    ERROR = 4
    ACK = 5

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='RC Camera Car Server.')
    parser.add_argument('port', type=int, help='port to listen on')

    args = parser.parse_args()
    PORT = args.port
    HOST = ''

    server = Server(HOST, PORT)
    server.add_handler(MsgType.REG_USER, handlers.handle_register_user)
    server.add_handler(MsgType.REG_CAR, handlers.handle_register_car)
    server.add_handler(MsgType.LOGIN, handlers.handle_login)
    server.add_handler(MsgType.MOVEMENT, handlers.handle_movement)
