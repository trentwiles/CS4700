# FTP Client

## High Level Overview
This client first parses the passed in FTP url, extracts the username/password/hostname/port, then logs in. Next, keeping the port open, the client preforms the proper action with the FTP server, based on the user operation. For certain operations (mv, ls, cp), a second passive socket is opened, the data is gathered in 4096b chunks, and the second socket is closed. Once the desired action has been preformed, the socket is closed with a `QUIT`.

## Challenges in Development
A development challenge was understanding conceptually how to keep both the original FTP socket open and the second "passive" socket open. Plus, determining when to upload versus download a file based on the order of the arguments was interesting to implement.

## Testing

I tested the program by trying as many edge cases and combinations of the commands as possible. Examples include trying faulty passwords, listing empty folders, attempting to download a non-existant file, etc.