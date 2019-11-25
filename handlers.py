import json
import sqlite3
import hashlib, os

from base64 import b64encode, b64decode
from utils import MsgType

CAR_PORT = 8080 # Assume each car is listening on this port
DATABASE_NAME = "RCCCar.db"


def _connect_to_db():
    dbconnect = sqlite3.connect(DATABASE_NAME);
    cursor = dbconnect.cursor();
    return dbconnect, cursor

def _send_JSON(server, source, JSON):
    data = json.dumps(JSON)
    server.send(data.encode('utf-8'), source)

def _format_error_JSON(message):
    print(message)
    returnJSON = {
      "type": MsgType.ERROR,
      "message": message
    }
    return returnJSON

def handle_movement(server, body, source):
    print('MOVEMENT') # TODO: Logging
    '''
    1. Get desination IP from cache (if not in cache, get from 'cars' table)
    2. Forward the message
    '''

    # Get JSON data
    car_name = body["car_name"]
    userID = body["userID"]
    x_axis = body["x_axis"]
    y_axis = body["y_axis"]

    # Check data is valid
    '''if type(car_name) is not str or type(x_axis) is not int or type(y_axis) is not int:
        errorJSON = _format_error_JSON("Invalid movement information")
        _send_JSON(server, source, errorJSON)
        return'''
    if not car_name or not x_axis or not y_axis:
        errorJSON = _format_error_JSON("Invalid movement information")
        _send_JSON(server, source, errorJSON)
        return

    # Check cache for car ip address
    car_ip = server.get_ip(car_name)
    if car_ip is None:
    # Get car ip address from database.
        dbconnect, cursor = _connect_to_db()
        cursor.execute('''select * from cars where (name='%s') and (userID='%s');''' %(car_name, userID))
        entry = cursor.fetchone()[2]
        dbconnect.close()
        if entry is None:
            errorJSON = _format_error_JSON("Invalid car information")
            _send_JSON(server, source, errorJSON)
            return
        car_ip = entry
        server.add_ip(car_name, car_ip)

    _send_JSON(server,(car_ip, CAR_PORT),body)
    #_send_JSON(server,source,body)


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
        errorJSON = _format_error_JSON("Invalid user information")
        _send_JSON(server, source, errorJSON)
        return

    # Salt password
    salt =  os.urandom(32)
    print(salt)
    password = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)

    # Create user in db. Send an error if user already exists.
    dbconnect, cursor = _connect_to_db()
    cursor.execute('''select * from users where (name='%s');''' %(name))
    entry = cursor.fetchone()
    if entry is None:
        cursor.execute('''insert into users (name,salt,password) values('%s','%s','%s');'''%(name,b64encode(salt).decode('utf-8'),b64encode(password).decode('utf-8')))
        dbconnect.commit()
    else:
        errorJSON = _format_error_JSON("User already exists")
        _send_JSON(server, source, errorJSON)
        return

    # Send Confirmation to App
    print("User registration successful")
    ackJSON = {
      "type": MsgType.ACK,
      "message": "User registration successful"
    }
    _send_JSON(server, source, ackJSON)

    dbconnect.close()

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
        errorJSON = _format_error_JSON("Invalid car information")
        _send_JSON(server, source, errorJSON)
        return

    # Check that the user exists in the database
    dbconnect, cursor = _connect_to_db()
    cursor.execute('''select * from users where (name='%s');''' %(userID))
    entry = cursor.fetchone()
    # Send error packet
    if entry is None:
        errorJSON = _format_error_JSON("User is not registered")
        _send_JSON(server, source, errorJSON)
        return

    # Check that the user does not already have car with that name
    cursor.execute('''select * from cars where (name='%s' and userID='%s');''' %(name, userID))
    entry = cursor.fetchone()
    # Send error if car already exists
    if entry is None:
        cursor.execute('''insert into cars (name,ip,userID) values('%s','%s','%s');'''%(name,ip,'user1'))
        dbconnect.commit()
    else:
        errorJSON = _format_error_JSON("Car name already registered")
        _send_JSON(server, source, errorJSON)
        return

    # Send Confirmation to App
    print("Car registration successful")
    ackJSON = {
      "type": MsgType.ACK,
      "message": "Car registration successful"
    }
    _send_JSON(server, source, ackJSON)

    dbconnect.close()

def handle_login(server, body, source):
    print('LOGIN') # TODO: Logging
    '''
    1. Compare salted-and-hashed passwords
    2. If success: get car list from database and send to the app
       If failure: send failed login message
    '''

    # Get JSON data
    name = body["name"]
    password = body["password"]

    # Check data is valid. if not, send an error packet
    if not name or not password:
        errorJSON = _format_error_JSON("Invalid user information")
        _send_JSON(server, source, errorJSON)
        return

    # Get user from db. Send an error if user doesn't exist.
    dbconnect, cursor = _connect_to_db()
    cursor.execute('''select * from users where (name='%s');''' %(name))
    entry = cursor.fetchone()
    dbconnect.close()
    if entry is None:
        errorJSON = _format_error_JSON("User does not exist")
        _send_JSON(server, source, errorJSON)
        return

    # Get salt as bytes
    salt =  entry[2]
    b_salt = b64decode(salt.encode('utf-8'))
    # Get salted password string from database
    salted_password = entry[3]
    # Salt the login password
    new_password = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), b_salt, 100000)
    str_new_password = b64encode(new_password).decode('utf-8')

    # Compare two passwords as strings
    if str_new_password == salted_password:
        # Send Confirmation to App
        print("User login successful")
        ackJSON = {
          "type": MsgType.ACK,
          "message": "User login successful"
        }
        _send_JSON(server, source, ackJSON)
    else:
        errorJSON = _format_error_JSON("Password is incorrect")
        _send_JSON(server, source, errorJSON)
