# add shebang here later

import argparse
from urllib.parse import urlparse
import socket
import re
import os

FTPENDCHAR = b"\r\n"

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
    
    return {"username": parsed.username, "password": parsed.password, "host": parsed.hostname, "port": parsed.port, "path": parsed.path}

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

def enterPassiveMode(control_sock):
    # enter passive mode
    # see comments at the end of the username/password auth logic
    # to see when this is used, there's only a few select commands that need this

    control_sock.sendall(b"PASV" + FTPENDCHAR)
    resp = control_sock.recv(4096).decode()
    _, msg, success = parseServerResp(resp.strip())
    if not success:
        raise ValueError(f"PASV command failed: {msg}")

    # ftp gives a weird response when entering passive mode
    # instead of being normal and providing the IP/port combo, it gives this:
    # 227 Entering Passive Mode (192,168,1,100,195,80)
    # ...where the first four digits are the IPv4 address, and the last two numbers form the port:
    # NUM1 * 256 + NUM2 = port
    match = re.search(r"\((\d+,\d+,\d+,\d+,\d+,\d+)\)", msg)
    if not match:
        raise ValueError(f"Cannot parse PASV response... {msg}")

    # grab the digits as an array (list) from the regex exp
    nums = list(map(int, match.group(1).split(',')))
    data_host = f"{nums[0]}.{nums[1]}.{nums[2]}.{nums[3]}"
    data_port = nums[4] * 256 + nums[5]
    return data_host, data_port

# intake: previously existing socket
def ftp_ls(control_sock, path):
    data_host, data_port = enterPassiveMode(control_sock)
    data_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    data_sock.connect((data_host, data_port))

    cmd = f"LIST {path}\r\n".encode()
    print(cmd)
    control_sock.sendall(cmd)

    resp = control_sock.recv(4096).decode()
    # first arg from tuple is code, but we really don't need this right now, maybe implement error checking in the future?
    _, msg, success = parseServerResp(resp.strip())
    if not success:
        data_sock.close()
        raise ValueError(f"LIST command failed: {msg}")

    # read the dir listing chunk by chunk, in 4096b chunks
    # add each chunk to the listing, which is in the byte format
    # DO NOT USE STRING FORMAT THIS WILL LEAD TO WEIRD ERRORS
    listing = b""
    while True:
        chunk = data_sock.recv(4096)
        if not chunk:
            break
        listing += chunk

    # close the second socket, we don't need it anymore
    data_sock.close()

    # Receive final response from control socket
    resp = control_sock.recv(4096).decode()
    print("Server:", resp.strip())

    # .decode() required!!! we can't print off a byte string
    return listing.decode()

# determines which path is local and remote,
# then based on this, what action should be taken (upload or download)
# if the local path is first, we upload
# if the local path is second, we upload
# [local, remote, useUpload?]
def manageLocalRemote(path1, path2):
    if detectLocalPath(path1):
        local = path1
        remote = parseURL(path2)  # parse remote FTP URL
        return local, remote, True
    elif detectLocalPath(path2):
        local = path2
        remote = parseURL(path1)
        return local, remote, False
    else:
        raise ValueError("must pass at least one local path to use cp/mv funcs")

# true = string is local path
# false = string is NOT local path
def detectLocalPath(path:str) -> bool:
    if path == None:
        return False
    return "ftp://" not in path

# intake same as above, previously opened sock
def ftp_download(control_sock, remote_path, local_path):
    # enter passive via helper function from above
    data_host, data_port = enterPassiveMode(control_sock)
    data_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    data_sock.connect((data_host, data_port))

    # RETR = retrieve
    print(remote_path + " <--- remote")
    control_sock.sendall(f"RETR {remote_path}\r\n".encode())
    resp = control_sock.recv(4096).decode()

    # again code doesn't matter for our impl
    _, msg, success = parseServerResp(resp.strip())
    if not success:
        data_sock.close()
        raise ValueError(f"RETR (via ftp_download) failed: {msg}")

    # similar to ls, we need to read the response in 4096b chunks
    # (which is an file this time, rather than a directory listing respomnse)
    
    file_data = b""
    while True:
        chunk = data_sock.recv(4096)
        if not chunk:
            break
        file_data += chunk

    data_sock.close()

    # Final control response
    resp = control_sock.recv(4096).decode()
    code, msg, success = parseServerResp(resp.strip())
    if not success:
        raise ValueError(f"RETR failed: {msg}")

    # local save
    with open(local_path, "wb") as f:
        f.write(file_data)
    
    return code, msg

def ftp_upload(control_sock, local_path, remote_path):
    # passive via helper function
    data_host, data_port = enterPassiveMode(control_sock)
    data_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # also keep in mind host is just an ip/hostname, don't include the path here
    # otherwise an error will occur!!!!!
    data_sock.connect((data_host, data_port))

    # STOR = upload in FTP
    print(f"Uploading local file '{local_path}' to remote path '{remote}'")
    control_sock.sendall(f"STOR {parseURL(remote_path)['path']}\r\n".encode())
    resp = control_sock.recv(4096).decode()
    _, msg, success = parseServerResp(resp.strip())
    if not success:
        data_sock.close()
        raise ValueError(f"STOR failed... {msg}")

    # Send file contents
    with open(local_path, "rb") as f:
        while chunk := f.read(4096):
            data_sock.sendall(chunk)

    data_sock.close()

    # Final control response
    resp = control_sock.recv(4096).decode()
    code, msg, success = parseServerResp(resp.strip())
    if not success:
        raise ValueError(f"STOR failed: {msg}")
    
    return code, msg

# access args above via args.operation
# Valid operations are ls, mkdir, rm, rmdir, cp, and mv
# prof: "mv is just cp with a delete"
VALID_OPERATIONS = ["ls", "mkdir", "rm", "rmdir", "cp", "mv"]

if args.operation not in VALID_OPERATIONS:
    raise ValueError("invalid command (insert verbose message here)")

# in the case of mv and cp, the remote server URL could be either arg1 or arg2
try:
    ftp_creds = parseURL(args.param1)
except:
    try:
        ftp_creds = parseURL(args.param2)
    except:
        raise ValueError("unable to parse FTP url... neither arg1 nor arg2 are valid FTP server URLs")

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

# password & username combo success by this point, we're authenticated
# for reference, the following commands need PASV
# LIST (directory listing), RETR (download), STOR (upload)

if args.operation == "ls":
    # call helper to open new socket
    dir_listing = ftp_ls(control_sock, ftp_creds['path'])
    print(dir_listing)
elif args.operation == "mkdir":
    control_sock.sendall(f"MKD {ftp_creds['path']}\r\n".encode())
    resp = control_sock.recv(4096).decode()
    parsedResp = parseServerResp(resp.strip())
    print(parsedResp)
elif args.operation == "rm":
    # raw socket sends DELE
    control_sock.sendall(f"DELE {ftp_creds['path']}\r\n".encode())
    resp = control_sock.recv(4096).decode()
    parsedResp = parseServerResp(resp.strip())
    print(parsedResp)
elif args.operation == "rmdir":
    # raw socket sends RMD
    control_sock.sendall(f"RMD {ftp_creds['path']}\r\n".encode())
    resp = control_sock.recv(4096).decode()
    parsedResp = parseServerResp(resp.strip())
    print(parsedResp)
elif args.operation == "cp":
    local, remote, shouldUpload = manageLocalRemote(args.param1, args.param2)
    if shouldUpload:
        ftp_upload(control_sock, local, remote['path'])
    else:
        ftp_download(control_sock, remote['path'], local)
    # copy doesn't delete anything... we're done!

elif args.operation == "mv":
    local, remote, shouldUpload = manageLocalRemote(args.param1, args.param2)
    if shouldUpload:
        ftp_upload(control_sock, local, remote['path'])
    else:
        ftp_download(control_sock, remote['path'], local)    
    # however, move does delete the original file
    # if we're uploading, we delete local
    # otherwise delete external
    if shouldUpload:
        # delete local
        os.remove(local)
    else:
        # delete external
        control_sock.sendall(f"DELE {remote}\r\n".encode())
        resp = control_sock.recv(4096).decode()
        parsedResp = parseServerResp(resp.strip())
        print(parsedResp)


else:
    print("you should never reach this")



# SEND A QUIT COMMAND HERE
# DO NOT FORGET TO DO THIS!!!!!!!!