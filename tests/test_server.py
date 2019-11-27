import json
import socket

from utils import MsgType

SERVER_ADDR = ('127.0.0.1', 5005)
BUFFER_SIZE = 1024

def test_register_user(server):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    req = {
        'type': MsgType.REG_USER,
        'name': 'mock_username',
        'password': 'mock_password',
    }
    s.sendto(json.dumps(req).encode('utf-8'), SERVER_ADDR)
    s.settimeout(1)
    data, addr = s.recvfrom(BUFFER_SIZE)
    res = json.loads(data)

    assert addr == SERVER_ADDR
    assert res['type'] == MsgType.ACK
    assert type(res['user_id']) == str

def test_login(register_user):
    s, user_id = register_user
    req = {
        'type': MsgType.LOGIN,
        'name': 'mock_username',
        'password': 'mock_password',
    }
    s.sendto(json.dumps(req).encode('utf-8'), SERVER_ADDR)
    s.settimeout(1)
    data, addr = s.recvfrom(BUFFER_SIZE)
    res = json.loads(data)

    assert addr == SERVER_ADDR
    assert res['type'] == MsgType.ACK
    assert res['user_id'] == user_id

def test_get_cars(register_car):
    app_sock, user_id, _, car_id = register_car
    req = {
        'type': MsgType.GET_CARS,
        'user_id': user_id,
    }
    app_sock.sendto(json.dumps(req).encode('utf-8'), SERVER_ADDR)
    app_sock.settimeout(1)
    data, addr = app_sock.recvfrom(BUFFER_SIZE)
    res = json.loads(data)

    assert addr == SERVER_ADDR
    assert res['type'] == MsgType.ACK
    assert type(res['cars']) == list
    assert car_id in res['cars']

def test_register_car(register_user):
    _, user_id = register_user

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    req = {
        'type': MsgType.REG_CAR,
        'user_id': user_id,
    }
    s.sendto(json.dumps(req).encode('utf-8'), SERVER_ADDR)
    s.settimeout(1)
    data, addr = s.recvfrom(BUFFER_SIZE)
    res = json.loads(data)

    assert addr == SERVER_ADDR
    assert res['type'] == MsgType.ACK
    assert type(res['car_id']) == str

def test_connect_car(register_car):
    _, _, car_sock, car_id = register_car

    car_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    req = {
        'type': MsgType.CONN_CAR,
        'car_id': car_id,
    }
    car_sock.sendto(json.dumps(req).encode('utf-8'), SERVER_ADDR)
    car_sock.settimeout(1)
    data, addr = car_sock.recvfrom(BUFFER_SIZE)
    res = json.loads(data)

    assert addr == SERVER_ADDR
    assert res['type'] == MsgType.ACK

def test_movement(register_car):
    app_sock, _, car_sock, _ = register_car

    TEST_X = 100
    TEST_Y = 100

    app_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    req = {
        'type': MsgType.MOVE,
        'x': TEST_X,
        'y': TEST_Y,
    }
    app_sock.sendto(json.dumps(req).encode('utf-8'), SERVER_ADDR)
    car_sock.settimeout(1)
    data, addr = car_sock.recvfrom(BUFFER_SIZE)
    res = json.loads(data)

    assert addr == SERVER_ADDR
    assert res['type'] == MsgType.MOVE
    assert res['x'] == TEST_X
    assert res['y'] == TEST_Y

def test_invalid_json(server):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    data = b'{"type": 2'
    s.sendto(data, SERVER_ADDR)
    s.settimeout(1)
    data, addr = s.recvfrom(BUFFER_SIZE)
    body = json.loads(data)

    assert addr == SERVER_ADDR
    assert body['type'] == MsgType.ERROR

def test_invalid_type(server):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    data = b'{"type": 666}'
    s.sendto(data, SERVER_ADDR)
    s.settimeout(1)
    data, addr = s.recvfrom(BUFFER_SIZE)
    body = json.loads(data)

    assert addr == SERVER_ADDR
    assert body['type'] == MsgType.ERROR
