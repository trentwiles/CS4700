#!/usr/bin/env python3

import socket
import ssl
import json
import sys
import argparse
import requests

# constants (all caps in python!!!)
ENDLINE = "\n"
DEFAULT_HOST = "proj1.4700.network"
DEFAULT_PORT = 27993
DEFAULT_TLS_PORT = 27994
WORD_LIST_URL = "https://4700.network/projects/project1-words.txt"

# grab the word list from remote, per spec
def load_word_list():
    try:
        response = requests.get(WORD_LIST_URL, headers={"user-agent": "trent"})
        response.raise_for_status() # kill if bad http status but unlikely
        
        # convert wordlist to a python list, filter junk
        return [word.strip().lower() for word in response.text.split('\n') if word.strip()]
    except:
        raise ValueError("cuoldn't grab the wordlist")

# python string to UTF + newline at the end
def send_json(sock, msg):
    message = json.dumps(msg) + ENDLINE
    sock.sendall(message.encode("utf-8"))

# parse a 
def recv_json(sock_file):
    line = sock_file.readline()
    if not line:
        raise ConnectionError("server closed connection")
    try:
        return json.loads(line.strip())
    except:
        raise ValueError("unable to parse JSON, try again later")

# wordle algorithm
# NOTE TO SELF: CLEAN THIS UP
def analyze_marks(guesses):
    # "confirmed letters" = 2, the letter IS in that exact position
    # "misplaced letters" = 1, the letter IS in the word, however it MAY not be in the exact position
    # "junk letters" = 0, they aren't in the word, and we should filter out words with them
    
    conf_letters = {} # word and it's respective location, in dict format!
    misplaced_letters = set() 
    junk_letters = set()
    
    for guess_info in guesses:
        word = guess_info["word"]
        marks = guess_info["marks"]
        
        for i, (letter, mark) in enumerate(zip(word, marks)):
            # correct possition: add to misplaced words AND confirmed words
            if mark == 2:
                conf_letters[i] = letter
                misplaced_letters.add(letter)
            # wrong position: 
            elif mark == 1:  # Wrong position but in word
                misplaced_letters.add(letter)
            elif mark == 0:  # Not in word
                junk_letters.add(letter)
    
    return conf_letters, misplaced_letters, junk_letters

def filter_candidates(word_list, conf_letters, misplaced_letters, junk_letters, previous_guesses):
    """Filter word list based on what we know so far."""
    candidates = []
    guessed_words = {guess["word"] for guess in previous_guesses}
    
    for word in word_list:
        if word in guessed_words:
            continue
            
        # Skip if word contains impossible letters
        if any(letter in junk_letters for letter in word):
            continue
            
        # Skip if word doesn't have confirmed letters in right positions
        valid = True
        for pos, letter in conf_letters.items():
            if word[pos] != letter:
                valid = False
                break
        
        if not valid:
            continue
            
        # Skip if word doesn't contain all possible letters
        if not all(letter in word for letter in misplaced_letters):
            continue
            
        # Additional check: letters marked as 1 shouldn't be in their guessed positions
        valid_positions = True
        for guess_info in previous_guesses:
            guess_word = guess_info["word"]
            marks = guess_info["marks"]
            for i, (letter, mark) in enumerate(zip(guess_word, marks)):
                if mark == 1 and word[i] == letter:  # Wrong position constraint
                    valid_positions = False
                    break
            if not valid_positions:
                break
                
        if valid_positions:
            candidates.append(word)
    
    return candidates

def choose_next_guess(word_list, guesses):
    """Choose the next word to guess based on previous results."""
    if not guesses:
        # First guess - use a word with common vowels and consonants
        return "adieu"
    
    # Analyze what we know
    conf_letters, misplaced_letters, junk_letters = analyze_marks(guesses)
    
    # Filter candidates
    candidates = filter_candidates(word_list, conf_letters, misplaced_letters, junk_letters, guesses)
    
    if candidates:
        return candidates[0]  # Return first valid candidate
    else:
        # Fallback: find any word not yet guessed
        guessed_words = {guess["word"] for guess in guesses}
        for word in word_list:
            if word not in guessed_words:
                return word
        
        # If somehow all words are exhausted, return the first one
        return word_list[0]

def play_game(sock, sock_file, username, word_list):

    # send hello to grab ID
    hello_msg = {"type": "hello", "northeastern_username": username}
    send_json(sock, hello_msg)
    
    # Receive start message
    response = recv_json(sock_file)
    if response.get("type") == "error":
        raise ValueError(f"Rmote server error: {response.get('message', 'Unknown error')}")
    
    if response.get("type") != "start":
        raise ValueError(f"Expected 'start' message, got: {response}")
    
    game_id = response["id"]
    
    # 500 guesses until we get kicked according to the docs
    # included so we don't get force kicked from the server
    guess_count = 0
    max_guesses = 500
    
    while guess_count < max_guesses:
        # first guess? pass a blank list to represent no guesses
        # otherwise, just use the list of guesses reflected from websocket
        if guess_count == 0:
            next_guess = choose_next_guess(word_list, [])
        else:
            next_guess = choose_next_guess(word_list, response.get("guesses", []))
        
        # make the guess
        guess_msg = {"type": "guess", "id": game_id, "word": next_guess}
        send_json(sock, guess_msg)
        guess_count += 1
        
        # grab the response
        response = recv_json(sock_file)
        
        # three cases:
        # 1. error, kill the program
        if response.get("type") == "error":
            raise ValueError(f"Server error: {response.get('message', 'Unknown error')}")
        # 2. it's correct, return the flag
        elif response.get("type") == "bye":
            return response["flag"]
        # 3. wrong guess, let's try again...
        elif response.get("type") == "retry":
            continue
        # 4. unexpected response type, throw an error for further inspection
        else:
            raise ValueError(f"Unexpected response type: {response.get('type')}")
    
    raise ValueError("Exceeded maximum number of guesses (500)")

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Project One, CS 4700 (by Trent Wiles)")
    parser.add_argument("-p", "--port", type=int, help="Server port")
    parser.add_argument("-s", "--tls", action="store_true", help="Use TLS encryption?")
    parser.add_argument("hostname", help="Server hostname")
    parser.add_argument("username", help="myNortheastern username")
    
    args = parser.parse_args()
    
    # fallback to predefined default ports as specified in docs if user doesn't override
    if args.port:
        port = args.port
    elif args.tls:
        port = DEFAULT_TLS_PORT
    else:
        port = DEFAULT_PORT
    
    word_list = load_word_list()
    
    try:
        # learned how to do this from:
        # https://realpython.com/python-sockets/
        # https://docs.python.org/3/howto/sockets.html
        # ^ pasted some "starter code" from sources above
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        if args.tls:
            context = ssl.create_default_context()
            sock = context.wrap_socket(sock, server_hostname=args.hostname)
        
        # prof mentioned how sockets and file I/O have quite a few paralells
        # python has a feature where you can treat a socket like a file
        sock.connect((args.hostname, port))
        sock_file = sock.makefile("r")
        
        flag = play_game(sock, sock_file, args.username, word_list)
        
        # only required output is printing the flag
        print(flag)
        
    except Exception as e:
        raise ValueError(f"error: {e}", str(sys.stderr))
    finally:
        sock.close()

if __name__ == "__main__":
    main()