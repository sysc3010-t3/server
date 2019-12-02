import json
import sqlite3
import threading

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
    SET_LED = 11

class Error(IntEnum):
    BAD_REQ = 0
    UNAUTHORIZED = 1
    SERVER_ERR = 2

    @staticmethod
    def json(errType, errMsg):
        body = { 'type': MsgType.ERROR, 'error_type': errType,
                'error_msg': errMsg }
        return json.dumps(body).encode('utf-8')

class Database():
    def __init__(self, db_name):
        self._db_conn = sqlite3.connect(db_name, check_same_thread=False)
        self._db_lock = threading.Lock()

    def __enter__(self):
        self._db_lock.acquire()
        return (self._db_conn, self._db_conn.cursor())

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self._db_lock.release()
