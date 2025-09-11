import socket
import json

ENDLINE = "\n"
HOST = "proj1.4700.network"
PORT = 27993
MAX_BYTES = 100000

def main():
    # open connection once
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((HOST, PORT))

    # send hello + grab the id/token
    hello_msg = {"type": "hello", "northeastern_username": "wiles.t"}
    s.sendall((json.dumps(hello_msg) + ENDLINE).encode("utf-8"))
    
    # i'm assuming the ID is no longer than 100k bytes
    response = s.recv(MAX_BYTES).decode("utf-8")
    api = json.loads(response)
    print("hello response:", api)

    if "id" not in api:
        raise ValueError("bad json returned")

    token = api["id"]

    # step 2: make a guess
    first_guess = True
    completed = False
    secret = None
    
    while not completed:
        guess_msg = {"type": "guess", "id": token, "word": "abede"}
        s.sendall((json.dumps(guess_msg) + ENDLINE).encode("utf-8"))
        response = s.recv(MAX_BYTES).decode("utf-8")
        api = json.loads(response)
        
        # case one: guess is correct!!!!
        if "bye" in api:
            completed = True
            secret = api["flag"]
        # case two: retry w/ clues from server
        elif "retry" in api:
            # retry code
            completed = False
            guess = api['guesses'][0]['marks']
        else:
            # bad data
            raise ValueError("invalid response from server:\n\n" + str(response))
    
    s.close()
    return secret

if __name__ == "__main__":
    main()
