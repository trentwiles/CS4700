# CS 4700 Project 1: Wordle Client

## High-Level Approach

This project implements a client for a Wordle-like guessing game. The client connects to a server via TCP sockets (with optional TLS encryption) and plays the game by making intelligent guesses based on feedback from previous attempts.

## Implementation Details

### Core Components

1. **Socket Communication**: The client establishes a TCP connection to the server and exchanges JSON messages terminated by newlines.

2. **TLS Support**: When the `-s` flag is provided, the client wraps the socket with TLS encryption using Python's `ssl` module.

3. **Protocol Implementation**: The client follows the specified protocol:
   - Sends a `hello` message with the Northeastern username
   - Receives a `start` message with a game ID
   - Makes guesses with `guess` messages
   - Processes `retry` responses with scoring information
   - Terminates when receiving a `bye` message with the secret flag

### Guessing Strategy

The client implements an intelligent guessing strategy:

1. **First Guess**: Uses "adieu" as it contains four common vowels and one consonant, providing good information about the target word.

2. **Subsequent Guesses**: Analyzes the marks from previous guesses to:
   - Track confirmed letters (mark = 2) and their positions
   - Identify letters that are in the word but in wrong positions (mark = 1)
   - Eliminate letters that are not in the word (mark = 0)

3. **Word Filtering**: Filters the word list to find candidates that:
   - Haven't been guessed before
   - Don't contain impossible letters
   - Have confirmed letters in the correct positions
   - Contain all letters known to be in the word
   - Don't place letters marked as wrong position in their guessed positions

4. **Candidate Selection**: Chooses the first valid candidate from the filtered list.

## Challenges Faced

1. **JSON Message Handling**: Initially had issues with message framing, solved by properly reading until newline characters.

2. **Strategy Optimization**: Balancing between exploration (finding new letters) and exploitation (using known information) required careful consideration of the marking system.

3. **TLS Implementation**: Ensuring proper TLS socket wrapping while maintaining the same protocol flow.

4. **Edge Cases**: Handling scenarios where multiple instances of the same letter appear in words, and correctly interpreting the marking system.

## Testing

The client was tested by:

1. Running against the server with both encrypted and unencrypted connections
2. Testing command-line argument parsing with various flag combinations
3. Verifying correct protocol message formatting
4. Testing the guessing strategy with manual trace-through of example games
5. Ensuring robust error handling for network issues and protocol errors

## Usage

```bash
# Non-encrypted connection
./client proj1.4700.network your.username

# TLS encrypted connection  
./client -s proj1.4700.network your.username

# Custom port
./client -p 27993 proj1.4700.network your.username

# TLS with custom port
./client -s -p 27994 proj1.4700.network your.username
```

## Dependencies

- Python 3.x
- `requests` library (for downloading the word list)
- Standard library modules: `socket`, `ssl`, `json`, `sys`, `argparse`