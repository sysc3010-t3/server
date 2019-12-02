import json
import re
import subprocess
import hashlib, os

from base64 import b64encode, b64decode
from utils import MsgType, Error

CAR_PORT = 8080 # Assume each car is listening on this port

HAPROXY_CFG = '/etc/haproxy/haproxy.cfg'
ACL_START_REGEX = r'(#ACL_START\n)'
RULE_START_REGEX = r'(#RULE_START\n)'
BACKEND_START_REGEX = r'(#BACKEND_START\n)'

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

    # Check data is valid
    if 'x' not in body or 'y' not in body:
        message = "Invalid movement information"
        print(message)
        server.send(Error.json(Error.BAD_REQ, message), source)
        return

    # Get JSON data
    x = body['x']
    y = body['y']

    # Check cache for car ip address
    car_addr = server.get_destination(source)
    if car_addr is None:
    # Return bad request.
        message = "Invalid car information"
        print(message)
        server.send(Error.json(Error.BAD_REQ, message), source)
        return

    # Send movement data to car
    _send_JSON(server, car_addr, body)

def handle_register_user(server, body, source):
    print('REGISTER USER') # TODO: Logging
    '''
    1. Store username, salt, and salted-and-hashed-password in 'users' table
    2. Send a confirmation (ACK) back to the app
    '''

    # Check data is valid. if not, send an error packet
    if 'name' not in body or 'password' not in body:
        message = "Invalid user information"
        print(message)
        server.send(Error.json(Error.BAD_REQ, message), source)
        return

    # Get JSON data
    name = body['name']
    password = body['password']

    # Salt password
    salt =  os.urandom(32)
    password = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)

    # Create user in db. Send an error if user already exists.
    with server.get_db() as (dbconnect, cursor):
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

        user_id = cursor.lastrowid

    # Send Confirmation to App
    print("User registration successful")
    ackJSON = {
      "type": MsgType.ACK,
      "user_id": user_id,
    }
    _send_JSON(server, source, ackJSON)

def handle_register_car(server, body, source):
    print('REGISTER CAR') # TODO: Logging
    '''
    1. Add a row in the 'cars' table
    2. Send a confirmation (ACK) back to the car
    '''

    ip = source[0]

    # Check data is valid. if not, send an error packet
    if 'name' not in body or 'user_id' not in body:
        message = "Invalid car information"
        print(message)
        server.send(Error.json(Error.BAD_REQ, message), source)
        return

    # Get JSON data
    name = body['name']
    user_id = body['user_id']

    with server.get_db() as (dbconnect, cursor):
        # Check that the user exists in the database
        cursor.execute("select * from users where id=(?)", [user_id])
        entry = cursor.fetchone()
        # Send error packet
        if entry is None:
            message = "User is not registered"
            print(message)
            server.send(Error.json(Error.BAD_REQ, message), source)
            return

        # Check that the user does not already have car with that name
        cursor.execute("select * from cars where name=(?) and userID=(?)", (name, user_id))
        entry = cursor.fetchone()
        # Send error if car already exists
        if entry is None:
            cursor.execute("insert into cars (name,ip,userID,isOn) values(?,?,?,?)", (name, ip, user_id, 0))
            dbconnect.commit()
        else:
            message = "Car name already registered"
            print(message)
            server.send(Error.json(Error.BAD_REQ, message), source)
            return

        car_id = cursor.lastrowid

    with open(HAPROXY_CFG, 'r+') as cfg:
        content = cfg.read()

        cfg.seek(0)
        cfg.truncate()

        # Insert ACL based on car ID
        acl_regex = r'\1    acl url_car{0} path_beg /{0}\n'.format(car_id)
        content = re.sub(ACL_START_REGEX, acl_regex, content)

        # Insert rule based on ACL
        rule_regex = r'\1    use_backend car{0} if url_car{0}\n'.format(car_id)
        content = re.sub(RULE_START_REGEX, rule_regex, content)

        # Insert backend based on car IP
        backend_regex = \
r'''\1backend car{0}
    mode http
    reqrep ^([^\ ]*\ /){0}[/]?(.*)     \\1\\2
    server car{0}_app {1}:8000 check\n\n'''.format(car_id, ip)
        content = re.sub(BACKEND_START_REGEX, backend_regex, content)

        cfg.write(content)

    subprocess.run(['systemctl', 'restart', 'haproxy'])

    # Send Confirmation to App
    print("Car registration successful")
    ackJSON = {
      "type": MsgType.ACK,
      "car_id": car_id
    }
    _send_JSON(server, source, ackJSON)

def handle_connect_car(server, body, source):
    print('CONNECT CAR')

    if 'car_id' not in body:
        print('missing field: car_id')
        server.send(Error.json(Error.BAD_REQ, 'missing field: car_id'), source)
        return

    car_id = body['car_id']

    with server.get_db() as (dbconnect, cursor):
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

def handle_login(server, body, source):
    print('LOGIN') # TODO: Logging
    '''
    1. Compare salted-and-hashed passwords
    2. If success: get car list from database and send to the app
       If failure: send failed login message
    '''

    # Check data is valid. if not, send an error packet
    if 'name' not in body or 'password' not in body:
        message = "Invalid user information"
        print(message)
        server.send(Error.json(Error.BAD_REQ, message), source)
        return

    # Get JSON data
    name = body['name']
    password = body['password']

    # Get user from db. Send an error if user doesn't exist.
    with server.get_db() as (dbconnect, cursor):
        cursor.execute("select * from users where name=(?)", [name])
        entry = cursor.fetchone()

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
        user_id = entry[0]
        ackJSON = {
          "type": MsgType.ACK,
          "user_id": user_id
        }
        _send_JSON(server, source, ackJSON)
    else:
        message = "Password is incorrect"
        print(message)
        server.send(Error.json(Error.BAD_REQ, message), source)

def handle_link(server, body, source):
    print('LINK')

    if 'car_id' not in body:
        print('missing field: car_id')
        server.send(Error.json(Error.BAD_REQ, 'missing field: car_id'), source)
        return

    car_id = body['car_id']

    with server.get_db() as (dbconnect, cursor):
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

def handle_set_led(server, body, source):
    """
    Sends SET_LED message to the destination that corresponds with the source
    address in the cache.
    """
    print('SET_LED')

    if 'state' not in body:
        print('Missing field: state')
        server.send(Error.json(Error.BAD_REQ, 'missing field: state'), source)
        return

    state = body['state']
    if state < 0 or state > 2:
        msg = 'state must be an int in range [0,2]'
        print(msg)
        server.send(Error.json(Error.BAD_REQ, msg), source)
        return

    car_addr = server.get_destination(source)
    if car_addr == None:
        msg = 'invalid destination'
        print(msg)
        server.send(Error.json(Error.BAD_REQ, msg), source)
        return

    server.send(json.dumps(body).encode('utf-8'), car_addr)

def handle_ack(server, body, source):
    """
    Sends ACK message to the destination that corresponds with the source
    address in the cache.
    """
    print('ACK')

    dest = server.get_destination(source)
    if dest == None:
        msg = 'invalid destination'
        print(msg)
        server.send(Error.json(Error.BAD_REQ, msg), source)
        return

    server.send(json.dumps(body).encode('utf-8'), dest)

def handle_get_cars(server, body, source):
    print('GET CARS') # TODO: Logging
    '''
    1. Get list of cars from databse
    2. If successful: send list of cars to app
    '''

    # Check data is valid
    if 'user_id' not in body:
        message = "Missing field: user_id"
        print(message)
        server.send(Error.json(Error.BAD_REQ, message), source)
        return

    # Get JSON data
    user_id = body["user_id"]

    # Create cars list
    cars = []
    with server.get_db() as (dbconnect, cursor):
        cursor.execute("select * from cars where userID=(?)", [user_id])
        entry = cursor.fetchall()
        # Return error if no cars are under userID
        if entry is None:
            message = "User has no registered cars"
            print(message)
            server.send(Error.json(Error.BAD_REQ, message), source)
            return
        else:
            # Add car_name and car_id to list for each car returned
            for row in entry:
                cars.append({"id":row[0],"name":row[1]})

            carsJSON = {
              "type": MsgType.ACK,
              "cars": cars
             }
            _send_JSON(server,source,carsJSON)
