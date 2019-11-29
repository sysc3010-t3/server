import json
import sqlite3
import hashlib, os

from base64 import b64encode
from utils import MsgType, Error

CAR_PORT = 6006 # Assume each car is listening on this port
DATABASE_NAME = "RCCCar.db"

def _connect_to_db():
    dbconnect = sqlite3.connect(DATABASE_NAME)
    cursor = dbconnect.cursor()
    return dbconnect, cursor

def _send_JSON(server, source, JSON):
    data = json.dumps(JSON)
    server.send(data.encode('utf-8'), source)

def handle_movement(server, body, source):
    print('MOVEMENT') # TODO: Logging
    '''
    TODO:
    1. Get desination IP from cache (if not in cache, get from 'cars' table)
    2. Forward the message
    '''

def handle_register_user(server, body, source):
    print('REGISTER USER') # TODO: Logging
    '''
    1. Store username, salt, and salted-and-hashed-password in 'users' table
    2. Send a confirmation (ACK) back to the app
    '''

    # Get JSON data
    name = body["name"]
    password = body["password"]

    # Check data is valid. if not, send an error packet
    if not name or not password:
        print("Invalid user information")
        errorJSON = {
          "type": MsgType.ERROR,
          "message": "Invalid user information"
        }
        _send_JSON(server, source, errorJSON)
        return

    # Salt password
    salt =  os.urandom(32)
    password = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)

    # Create user in db. Send an error if user already exists.
    dbconnect, cursor = _connect_to_db()
    cursor.execute('''select * from users where (name='%s');''' %(name))
    entry = cursor.fetchone()
    if entry is None:
        cursor.execute('''insert into users (name,salt,password) values('%s','%s','%s');'''%(name,b64encode(salt).decode('utf-8'),b64encode(password).decode('utf-8')))
        dbconnect.commit()
    else:
        print("User already exists")
        errorJSON = {
          "type": MsgType.ERROR,
          "message": "User already exists"
        }
        _send_JSON(server, source, errorJSON)
        return

    # Send Confirmation to App
    print("User registration successful")
    ackJSON = {
      "type": MsgType.ACK,
      "message": "User registration successful"
    }
    _send_JSON(server, source, ackJSON)

def handle_register_car(server, body, source):
    print('REGISTER CAR') # TODO: Logging
    '''
    1. Add a row in the 'cars' table
    2. Send a confirmation (ACK) back to the car
    '''

    # Get JSON data
    name = body["name"]
    ip = body["ip"]
    userID = body["userID"]

    # Check data is valid. if not, send an error packet
    if not name or not ip or not userID:
        print("Invalid car information")
        errorJSON = {
          "type": MsgType.ERROR,
          "message": "Invalid car information"
        }
        _send_JSON(server, source, errorJSON)
        return

    # Check that the user does not already have car with that name
    dbconnect, cursor = _connect_to_db()
    cursor.execute('''select * from cars where (name='%s' and userID='%s');''' %(name, userID))
    entry = cursor.fetchone()

    if entry is None:
        cursor.execute('''insert into cars (name,ip,userID) values('%s','%s','%s');'''%(name,ip,'user1'))
        dbconnect.commit()
    else:
        print("Car name already registered")
        errorJSON = {
          "type": MsgType.ERROR,
          "message": "Car name already registered"
        }
        _send_JSON(server, source, errorJSON)
        return

    # Send Confirmation to App
    print("Car registration successful")
    ackJSON = {
      "type": MsgType.ACK,
      "message": "Car registration successful"
    }
    _send_JSON(server, source, ackJSON)

def handle_connect_car(server, body, source):
    print('CONNECT CAR')

    car_id = body['car_id']

    if not car_id:
        print('missing field: car_id')
        server.send(Error.json(Error.BAD_REQ, 'missing field: car_id'), source)
        return

    dbconnect, cursor = _connect_to_db()
    cursor.execute('select * from cars where (id=?)', (car_id,))
    entry = cursor.fetchone()

    request_ip = source[0]
    if entry is None:
        msg = 'car does not exist'
        print(msg)
        server.send(Error.json(Error.BAD_REQ, msg), source)
    elif entry[2] != request_ip:
        msg = 'IP address does not match car ID'
        print(msg)
        server.send(Error.json(Error.BAD_REQ, msg), source)
    else:
        cursor.execute('update cars set isOn=1 where (id=?)', (car_id,))
        dbconnect.commit()
        data = '{"type": %d}' % MsgType.ACK
        server.send(data.encode('utf-8'), source)

    dbconnect.close()

def handle_login(server, body, source):
    print('LOGIN') # TODO: Logging
    '''
    TODO:
    1. Compare salted-and-hashed passwords
    2. If success: get car list from database and send to the app
       If failure: send failed login message
    '''

def handle_link(server, body, source):
    print('LINK')

    car_id = body['car_id']

    if not car_id:
        print('missing field: car_id')
        server.send(Error.json(Error.BAD_REQ, 'missing field: car_id'), source)
        return

    dbconnect, cursor = _connect_to_db()
    cursor.execute('select * from cars where (id=?)', (car_id,))
    entry = cursor.fetchone()

    if entry == None:
        msg = 'car does not exist'
        print(msg)
        server.send(Error.json(Error.BAD_REQ, msg), source)
    else:
        server.add_route(source, (entry[2], CAR_PORT))
        data = '{"type": %d}' % MsgType.ACK
        server.send(data.encode('utf-8'), source)

    dbconnect.close()
