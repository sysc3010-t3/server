import json

CAR_PORT = 6006 # Assume each car is listening on this port

def handle_movement(server, body, source):
    print('MOVEMENT') # TODO: Logging
    '''
    TODO:
    1. Get desination IP from cache (if not in cache, get from 'cars' table)
    2. Forward the message
    '''
    data = json.dumps(body).encode('utf-8')
    car_ip = 'localhost' # TODO: Make this read from cache or 'cars' table
    server.send(data, (car_ip, CAR_PORT))

def handle_register_user(server, body, source):
    print('REGISTER USER') # TODO: Logging
    '''
    TODO:
    1. Store username, salt, and salted-and-hashed-password in 'users' table
    2. Send a confirmation (ACK) back to the app
    '''

def handle_register_car(server, body, source):
    print('REGISTER CAR') # TODO: Logging
    '''
    TODO:
    1. Add a row in the 'cars' table
    2. Send a confirmation (ACK) back to the car
    '''

def handle_login(server, body, source):
    print('LOGIN') # TODO: Logging
    '''
    TODO:
    1. Compare salted-and-hashed passwords
    2. If success: get car list from database and send to the app
       If failure: send failed login message
    '''
