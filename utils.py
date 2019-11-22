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
