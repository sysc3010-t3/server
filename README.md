# RC Camera Car Central Server

This is the repository for the central server of the RC Camera Car system. This
repository contains the Python code for a UDP server that exposes a single port
and handles request-response messages, as well as proxying control messages
between client applications and the cars. The server expects that `haproxy` is
installed on the system as it modifies the `haproxy` configuration to allow for
the proxying of the car's live video stream. The server has been developed and
tested to run on the Raspbian operating system.

## Setup
### Dependencies:
* Python 3
* sqlite3
* haproxy

### Steps:
1. Setup `haproxy`.  
  a) On Raspbian, install `haproxy` by running `sudo apt-get install haproxy`.  
  b) Copy the `haproxy.cfg` file from the top-level directory of this repository
     to `/etc/haproxy/haproxy.cfg`.  
  c) Run `sudo systemctl restart haproxy`.  
2. Setup the database.  
  a) On Raspbian, install `sqlite3` by running `sudo apt-get install sqlite3`.  
  b) Run `sqlite3 RCCar.db` in the top-level directory of this repository to
     create the database.  
  c) In the `sqlite3` command-line interface, execute `read dbSchema.sql` to
     create the tables, then exit.  
3. Run the server.  
  a) Python 3 should come pre-installed on Raspbian.  
  b) Run `sudo python3 main.py 6006`. The server will now be listening on port
     6006 for UDP requests from apps and cars.  
