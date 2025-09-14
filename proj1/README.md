# CS 4700 Project 1

## Usage

```bash
python3 proj1\client.py [host] [username] [-p/--port] [-s/--tls]
```

## Concept
I first load the wordlist from the CS4700 website. I then connect to the socket, getting the unique ID for my Northeastern username. I then enter a loop that only terminates when I hit 500 guesses* or when the correct guess is reached. I start by picking a random word from the word list. Then, the script reviews the response from the server (the 0s, 1s, 2s...), and based on this, iterates through the entire word list and filters out words that violate the constraints.


## Challenge
I started out by looping through every single word in the wordlist. Sadly, I ran out of my 500 guess allowance incredibly fast with this technique. To solve this, I tried to reconnect to the server after 500 guessing, leaving off on the word that I ended at. However, I was unable to figure out how to reconnect to the socket without re-running the script, so I decided to move to the solution above.
