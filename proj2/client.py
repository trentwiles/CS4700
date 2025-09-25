# add shebang here later

import argparse
from urllib.parse import urlparse
import socket
import re

FTPENDCHAR = "\n\r"

# ./4700ftp [operation] [param1] [param2]

parser = argparse.ArgumentParser(description="CS4700 FTP Client")
parser.add_argument("operation", help="FTP operation (think COPY)")
parser.add_argument("param1", nargs="?", help="First parameter (optional)", default=None)
parser.add_argument("param2", nargs="?", help="Second parameter (optional)", default=None)
args = parser.parse_args()

# helper functions
def parseURL(ftp_string:str):
    parsed = urlparse(ftp_string)

    if parsed.scheme != "ftp" or not parsed.hostname:
        raise ValueError("invalid FTP url passed")
    
    return {"username": parsed.username, "password": parsed.password, "host": parsed.hostname, "port": parsed.port}

def parseServerResp(ftp_resp:str):
    # [RESPONSE_CODE, RESPONSE_STRING, success?]
    # regex exp to get server response
    match = re.match(r"\s*(\d+)\s*(.*)", ftp_resp)
    if match:
        code = int(match.group(1))
        message = match.group(2)

        # failure, 1XX, 2XX, 3XX codes mean success
        #          4XX, 5XX, 6XX codes mean failure
        return [code, message, code <= 399]
    raise ValueError("cannot parse server response: " + ftp_resp)


# access args above via args.operation
# Valid operations are ls, mkdir, rm, rmdir, cp, and mv
VALID_OPERATIONS = ["ls", "mkdir", "rm", "rmdir", "cp", "mv"]

if args.operation not in VALID_OPERATIONS:
    raise ValueError("invalid command (insert verbose message here)")

ftp_creds = parseURL(args.param1)

# if we've made it to this section, we know that there is a valid FTP url

control_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
control_sock.connect((ftp_creds['host'], ftp_creds['port']))

# Receive the server's initial response
resp = control_sock.recv(4096).decode()
print("Server:", resp.strip())

# if there's a failure for whatever reason kill
if not parseServerResp(resp.strip())[2]:
    raise ValueError("Unable to connect to host on provided port, try again later??")

# Send USER command
control_sock.sendall(f"USER {ftp_creds['username']}\r\n".encode())
resp = control_sock.recv(4096).decode()
print("Server:", resp.strip())

control_sock.sendall(f"PASS {ftp_creds['password']}\r\n".encode())
resp = control_sock.recv(4096).decode()
parsedResp = parseServerResp(resp.strip())

# we've sent the username and password, now check if it was a success
if not parsedResp[2]:
    raise ValueError(f"username / password combination ({ftp_creds['username'], ftp_creds['password']} invalid on host {ftp_creds['host']})")