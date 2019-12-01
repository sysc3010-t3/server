import json
import sqlite3
import hashlib, os

from base64 import b64encode, b64decode
from utils import MsgType, Error

CAR_PORT = 8080 # Assume each car is listening on this port
DATABASE_NAME = "RCCCar.db"

def _connect_to_db():
    dbconnect = sqlite3.connect(DATABASE_NAME)
    cursor = dbconnect.cursor()
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
    x_axis = body["x_axis"]
    y_axis = body["y_axis"]

    # Check data is valid
    if not x_axis or not y_axis:
        message = "Invalid movement information"
        print(message)
        server.send(Error.json(Error.BAD_REQ, message), source)
        return

    # Check cache for car ip address
    car_ip = server.get_destination(source[0])
    if car_ip is None:
    # Return bad request.
        message = "Invalid car information"
        print(message)
        server.send(Error.json(Error.BAD_REQ, message), source)
        return

    # Send movement data to car
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
        message = "Invalid user information"
        print(message)
        server.send(Error.json(Error.BAD_REQ, message), source)
        return

    # Salt password
    salt =  os.urandom(32)
    password = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)

    # Create user in db. Send an error if user already exists.
    dbconnect, cursor = _connect_to_db()
    cursor.execute("select * from users where name=(?)", [name])
    entry = cursor.fetchone()
    if entry is None:
        cursor.execute("insert into users (name,salt,password) values (?,?,?)",\
        (name,b64encode(salt).decode('utf-8'), b64encode(password).decode('utf-8')))
        dbconnect.commit()
    else:
        message = "User already exists"
        print(message)
        server.send(Error.json(Error.BAD_REQ, message), source)
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
        message = "Invalid car information"
        print(message)
        server.send(Error.json(Error.BAD_REQ, message), source)
        return

    # Check that the user exists in the database
    dbconnect, cursor = _connect_to_db()
    cursor.execute("select * from users where name=(?)", [userID])
    entry = cursor.fetchone()
    # Send error packet
    if entry is None:
        message = "User is not registered"
        print(message)
        server.send(Error.json(Error.BAD_REQ, message), source)
        return

    # Check that the user does not already have car with that name
    cursor.execute("select * from cars where name=(?) and userID=(?)", (name, userID))
    entry = cursor.fetchone()
    # Send error if car already exists
    if entry is None:
        cursor.execute("insert into cars (name,ip,userID) values(?,?,?)",(name, ip, userID))
        dbconnect.commit()
    else:
        message = "Car name already registered"
        print(message)
        server.send(Error.json(Error.BAD_REQ, message), source)
        return

    # Send Confirmation to App
    print("Car registration successful")
    ackJSON = {
      "type": MsgType.ACK,
      "message": "Car registration successful"
    }
    _send_JSON(server, source, ackJSON)

    dbconnect.close()

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
        server.send(data.encode('utf-8'), (source))

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
        message = "Invalid user information"
        print(message)
        server.send(Error.json(Error.BAD_REQ, message), source)
        return

    # Get user from db. Send an error if user doesn't exist.
    dbconnect, cursor = _connect_to_db()
    cursor.execute("select * from users where name=(?)", [name])
    entry = cursor.fetchone()
    dbconnect.close()
    if entry is None:
        message = "User does not exist"
        print(message)
        server.send(Error.json(Error.BAD_REQ, message), source)
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
        message = "Password is incorrect"
        print(message)
        server.send(Error.json(Error.BAD_REQ, message), source)

def handle_get_cars(server, body, source):
    print('GET CARS') # TODO: Logging
    '''
    1. Get lsit of cars form databse
    2. If successful: send list of cars to app
    '''

    # Get JSON data
    userID = body["userID"]

    # Check data is valid. if not, send an error packet
    if not userID:
        message = "Invalid user ID"
        print(message)
        server.send(Error.json(Error.BAD_REQ, message), source)
        return

    # Create cars list
    cars = []

    # Create user in db. Send an error if user already exists.
    dbconnect, cursor = _connect_to_db()
    cursor.execute("select * from cars where userID=(?)", [userID])
    entry = cursor.fetchall()
    dbconnect.close()
    # Return error is no cors are under userID
    if entry is None:
        message = "User has no registered cars"
        print(message)
        server.send(Error.json(Error.BAD_REQ, message), source)
        return
    else:
        # Add car name and id to list for each car returned
        for row in entry:
            cars.append({row[1]:row[0]})
        
        carsJSON = {
          "type": MsgType.ACK,
          "cars": cars
         }
        print(carsJSON)
        _send_JSON(server,source,carsJSON)
