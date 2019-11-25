import json

from enum import IntEnum

class MsgType(IntEnum):
    ACK = 0
    ERROR = 1
    REG_USER = 2
    LOGIN = 3
    GET_CARS = 4
    LINK = 5
    REG_CAR = 6
    CONN_CAR = 7
    MOVE = 8

class Error(IntEnum):
    BAD_REQ = 0
    UNAUTHORIZED = 1
    SERVER_ERR = 2

    @staticmethod
    def json(errType, errMsg):
        body = { 'type': MsgType.ERROR, 'error_type': errType,
                'error_msg': errMsg }
        return json.dumps(body).encode('utf-8')
