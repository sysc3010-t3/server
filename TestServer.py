import socket
import json
import pytest
import server
import handlers
import sqlite3
from utils import MsgType

# Clear the database of test values
dbconnect = sqlite3.connect("RCCCar.db");
cursor = dbconnect.cursor();
cursor.execute("DELETE FROM users WHERE name == 'user1'")
cursor.execute("DELETE FROM cars WHERE userID == 'user1'")
dbconnect.commit()
dbconnect.close()
# Constant values
PORT = 8080
HOST = "localhost"
BUFFER_SIZE = 100

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

class TestServer:

    def _receive_packet():
        """
        Wait for a packet on port.
        """
        data, address = s.recvfrom(BUFFER_SIZE)
        try:
            body = json.loads(data)
        except json.JSONDecodeError:
            return False
        return body["type"]

    def _send_packet(jsondict):
        JSON = json.dumps(jsondict)
        s.sendto(JSON.encode('utf-8'), (HOST, PORT))

    def test_connect_to_database(self):
        dbconnect, cursor = handlers._connect_to_db()
        assert dbconnect is not None and cursor is not None

    def test_register_user_invalid_user(self):
        body = {
          "type": MsgType.REG_USER,
          "name": "",
          "password": "pass"
        }
        TestServer._send_packet(body)
        assert TestServer._receive_packet() == MsgType.ERROR

    def test_register_user_invalid_password(self):
        body = {
          "type": MsgType.REG_USER,
          "name": "user1",
          "password": ""
        }
        TestServer._send_packet(body)
        assert TestServer._receive_packet() == MsgType.ERROR

    def test_register_user_packet_success(self):
        body = {
          "type": MsgType.REG_USER,
          "name": "user1",
          "password": "pass"
        }
        TestServer._send_packet(body)
        assert TestServer._receive_packet() == MsgType.ACK

    def test_register_user_db_success(self):
        dbconnect, cursor = handlers._connect_to_db()
        cursor.execute('''select * from users where (name='user1');''')
        entry = cursor.fetchone()
        assert entry is not None

    def test_register_user_already_exists(self):
        body = {
          "type": MsgType.REG_USER,
          "name": "user1",
          "password": "pass"
        }
        TestServer._send_packet(body)
        assert TestServer._receive_packet() == MsgType.ERROR

    def test_register_car_invalid_car_name(self):
        body = {
          "type": MsgType.REG_CAR,
          "name": "",
          "ip": "127.0.0.1",
          "userID": "user1"
        }
        TestServer._send_packet(body)
        assert TestServer._receive_packet() == MsgType.ERROR

    def test_register_car_invalid_ip(self):
        body = {
          "type": MsgType.REG_CAR,
          "name": "car1",
          "ip": "",
          "userID": "user1"
        }
        TestServer._send_packet(body)
        assert TestServer._receive_packet() == MsgType.ERROR

    def test_register_car_invalid_userID(self):
        body = {
          "type": MsgType.REG_CAR,
          "name": "car1",
          "ip": "127.0.0.1",
          "userID": ""
        }
        TestServer._send_packet(body)
        assert TestServer._receive_packet() == MsgType.ERROR

    def test_register_car_no_user(self):
        body = {
          "type": MsgType.REG_CAR,
          "name": "car1",
          "ip": "127.0.0.1",
          "userID": "user2"
        }
        TestServer._send_packet(body)
        assert TestServer._receive_packet() == MsgType.ERROR

    def test_register_car_packet_success(self):
        body = {
          "type": MsgType.REG_CAR,
          "name": "car1",
          "ip": "localhost",
          "userID": "user1"
        }
        TestServer._send_packet(body)
        assert TestServer._receive_packet() == MsgType.ACK

    def test_register_car_db_success(self):
        dbconnect, cursor = handlers._connect_to_db()
        cursor.execute('''select * from cars where (name='car1');''')
        entry = cursor.fetchone()
        assert entry is not None

    def test_register_car_name_exists(self):
        body = {
          "type": MsgType.REG_CAR,
          "name": "car1",
          "ip": "localhost",
          "userID": "user1"
        }
        TestServer._send_packet(body)
        assert TestServer._receive_packet() == MsgType.ERROR


    def test_user_login_success(self):
        body = {
          "type": MsgType.LOGIN,
          "name": "user1",
          "password": "pass"
        }
        TestServer._send_packet(body)
        assert TestServer._receive_packet() == MsgType.ACK


    # Test not required
    '''def test_move_success(self):
        body = {
          "type": MsgType.MOVE,
          "car_id": 1,
          "x_axis": "500",
          "y_axis": "500"
        }
        TestServer._send_packet(body)
        print("yup")
        assert TestServer._receive_packet() == MsgType.MOVE
'''
