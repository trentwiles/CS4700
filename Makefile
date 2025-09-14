# Makefile for CS 4700 Project 1: Wordle Client

# Default target
all: client

# Make the Python script executable
client: client.py
	chmod +x client.py
	ln -sf client.py client

# Clean target
clean:
	rm -f client

# Install dependencies (optional)
install:
	pip3 install requests

.PHONY: all clean install