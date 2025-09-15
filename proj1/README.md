# CS 4700 Project 1

## Usage

```bash
python3 proj1\client.py [host] [username] [-p/--port] [-s/--tls]
```

## Concept
<<<<<<< HEAD
I first load the wordlist from the CS4700 website. I then connect to the socket, getting the unique ID for my Northeastern username. I then enter a loop that only terminates when I hit 500 guesses* or when the correct guess is reached. I start by picking a random word from the word list. Then, the script reviews the response from the server (the 0s, 1s, 2s...), and based on this, iterates through the entire word list and filters out words that violate the constraints.
=======
I first load the wordlist from the CS4700 website. I then connect to the socket, getting the unique ID for my Northeastern username. I then enter a loop that only terminates when I hit 500 guesses* or when the correct guess is reached. I start by picking a random word from the word list. Then, the script reviews the response from the server (the 0s, 1s, 2s...), and based on this, iterates through the entire word list and filters out words that violate the constraints. The script uses a dictionary (dict) to record the frequency of how often words appear, and uses this knowledge to eliminate irrelevent words from the word list, speeding up the guessing.
>>>>>>> bc4e16175cbb39335b06c2b69eab1678719cb521

## Challenge
I started out by looping through every single word in the wordlist. Sadly, I ran out of my 500 guess allowance incredibly fast with this technique. To solve this, I tried to reconnect to the server after 500 guessing, leaving off on the word that I ended at. However, I was unable to figure out how to reconnect to the socket without re-running the script, so I decided to move to the solution above.
