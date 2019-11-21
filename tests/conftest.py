import json
import os
import pytest
import subprocess
import signal
import socket

from time import sleep
from utils import MsgType

LOG_FILENAME = 'server.log'

SERVER_ADDR = ('localhost', 5005)
BUFFER_SIZE = 1024

with open(LOG_FILENAME, 'a') as f:
    f.write('\n------------\n')
    f.write('NEW TEST RUN\n')
    f.write('------------\n')

@pytest.fixture
def server(request):
    cmd = ['python', 'main.py', '5005']
    f = open(LOG_FILENAME, 'a')
    f.write('\n')
    proc = subprocess.Popen(
        cmd,
        stdout=f,
        stderr=subprocess.STDOUT,
        close_fds=True)
    sleep(0.1)
    yield proc
    os.kill(proc.pid, signal.SIGINT)
    proc.wait()

@pytest.fixture
def register_user(server):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    req = {
        'type': MsgType.REG_USER,
        'name': 'mock_username',
        'password': 'mock_password',
    }
    s.sendto(json.dumps(req).encode('utf-8'), SERVER_ADDR)
    data, _ = s.recvfrom(BUFFER_SIZE)
    user_id = json.loads(data)['user_id']

    return s, user_id

@pytest.fixture
def register_car(register_user):
    app_sock, user_id = register_user
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    req = {
        'type': MsgType.REG_CAR,
        'user_id': user_id,
    }
    s.sendto(json.dumps(req).encode('utf-8'), SERVER_ADDR)
    data, _ = s.recvfrom(BUFFER_SIZE)
    car_id = json.loads(data)['car_id']

    return app_sock, user_id, s, car_id